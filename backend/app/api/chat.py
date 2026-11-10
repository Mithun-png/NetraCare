"""API endpoints for Patient Conversational Booking Agent and Staff Search Debugger (Iteration 4)."""
import uuid
import json
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.types import Command

from app.db.session import get_db
from app.api.deps import get_current_patient, get_current_staff, CurrentUser
from app.agent.graph import agent_graph
from app.rag.retriever import get_hybrid_retriever
from app.observability.opik_setup import get_opik_tracer, track_op

router = APIRouter(tags=["Chat & Search"])

class PatientChatRequest(BaseModel):
    message: Optional[str] = Field(None, max_length=500, description="Patient message up to 500 characters.")
    thread_id: Optional[str] = Field(None, description="Conversation thread identifier for memory.")
    confirm: Optional[bool] = Field(None, description="Confirm (true) or decline (false) for a pending confirmation card.")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Legacy history field.")

class PatientChatResponse(BaseModel):
    thread_id: str
    answer: str
    sources: List[str] = Field(default_factory=list)
    pending_action: Optional[Dict[str, Any]] = None
    emergency: bool = False
    answered: bool = True

@router.post("/patient/chat", response_model=PatientChatResponse)
@track_op(name="patient_chat_turn", tags=["chat", "patient"])
def patient_chat_endpoint(
    req: PatientChatRequest,
    patient: CurrentUser = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Patient conversational booking agent.
    Performs slot discovery, booking, rescheduling, cancellations, clinic document Q&A with citations,
    and pauses for human confirmation before mutating the database.
    """
    thread_id = req.thread_id or f"t_{patient.id}_{uuid.uuid4().hex[:12]}"
    project_name = os.getenv("OPIK_PROJECT_NAME", "netracare-dev")
    tracer = get_opik_tracer(
        project_name=project_name,
        tags=["chat", "patient"],
        metadata={"patient_id": patient.id, "thread_id": thread_id}
    )
    config = {
        "configurable": {
            "thread_id": thread_id,
            "patient_id": patient.id,
        },
        "recursion_limit": 15,
    }
    if tracer is not None:
        config["callbacks"] = [tracer]

    try:
        # 1. Handle confirmation card response
        if req.confirm is not None:
            list(agent_graph.stream(Command(resume=req.confirm), config))
        elif req.message and req.message.strip():
            msg_text = req.message.strip()
            curr_state = agent_graph.get_state(config)

            # If legacy history was provided and thread has no messages yet
            history_msgs = []
            if req.history and not curr_state.values.get("messages"):
                for h in req.history:
                    if h.get("role") == "user":
                        history_msgs.append(HumanMessage(content=h.get("content", "")))
                    elif h.get("role") == "assistant":
                        history_msgs.append(AIMessage(content=h.get("content", "")))

            # If an action was waiting on this thread and the user typed a new message,
            # resume with False (cancel action per R5) then process the new message
            if curr_state.tasks and any(t.interrupts for t in curr_state.tasks):
                list(agent_graph.stream(Command(resume=False), config))

            list(agent_graph.stream({"messages": history_msgs + [HumanMessage(content=msg_text)]}, config))
        else:
            raise HTTPException(status_code=400, detail="Either 'message' or 'confirm' must be provided.")

        # 2. Extract final state
        final_state = agent_graph.get_state(config)
        
        # Check for pending confirmation interrupt
        tasks = final_state.tasks
        interrupts = [i.value for t in tasks for i in t.interrupts] if tasks else []
        pending_action = interrupts[0] if interrupts else None

        # Determine answer
        msgs = final_state.values.get("messages", [])
        if pending_action:
            answer = pending_action.get("summary", "Please confirm your action:")
        else:
            ai_msgs = [m for m in msgs if isinstance(m, AIMessage) and m.content]
            answer = ai_msgs[-1].content if ai_msgs else "How can I assist you with NetraCare appointments?"

        # Extract sources from search_clinic_docs, get_lab_test_info, and skills
        sources = []
        skills_loaded = []
        lab_used = False
        lab_offline = False

        for m in msgs:
            if isinstance(m, ToolMessage):
                if m.name == "search_clinic_docs":
                    try:
                        data = json.loads(m.content) if isinstance(m.content, str) else m.content
                        if isinstance(data, dict):
                            for s in data.get("sources", []):
                                if s not in sources:
                                    sources.append(s)
                    except Exception:
                        pass
                elif m.name == "get_lab_test_info":
                    lab_used = True
                    if "offline" in str(m.content) or "can't check" in str(m.content).lower():
                        lab_offline = True
            elif isinstance(m, AIMessage) and hasattr(m, "tool_calls") and m.tool_calls:
                for tc in m.tool_calls:
                    if tc.get("name") in ("load_skill", "read_skill_file"):
                        sk = tc.get("args", {}).get("name")
                        if sk and sk not in skills_loaded:
                            skills_loaded.append(sk)
                    elif tc.get("name") == "get_lab_test_info":
                        lab_used = True

        # Append Lab citation
        if lab_used and not lab_offline:
            if "Source: CityCare Lab (partner)" not in answer and not any(k in answer.lower() for k in ("cannot interpret", "cannot advise", "cannot book")):
                answer = f"{answer}\n\nSource: CityCare Lab (partner)"
            if "CityCare Lab (partner)" not in sources:
                sources.append("CityCare Lab (partner)")

        # Append Skill citations
        for sk in skills_loaded:
            if f"Skill: {sk}" not in answer:
                if sk == "prepare-for-visit" and "clinic_policy_faq.md" not in answer:
                    answer = f"{answer}\n\nSkill: {sk}, clinic_policy_faq.md"
                else:
                    answer = f"{answer}\n\nSkill: {sk}"
            if f"Skill: {sk}" not in sources:
                sources.append(f"Skill: {sk}")

        # Format sources line if present and not already in answer
        if sources and "Sources:" not in answer and not lab_used and not skills_loaded:
            answer = f"{answer}\n\nSources: {', '.join(sources)}"

        emergency = bool(final_state.values.get("emergency", False))

        return PatientChatResponse(
            thread_id=thread_id,
            answer=answer,
            sources=sources,
            pending_action=pending_action,
            emergency=emergency,
            answered=True,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't check your message just now. Please try again, or call the clinic if it's urgent.",
        )

@router.get("/staff/search-debug")
def staff_search_debug_endpoint(
    q: str = Query(..., min_length=1, description="Search query string"),
    staff: CurrentUser = Depends(get_current_staff),
):
    """Staff Search Debug View comparing BM25 keyword, Vector similarity, and Hybrid results."""
    retriever = get_hybrid_retriever()
    results = retriever.search_debug(query=q, top_k=4)
    return results
