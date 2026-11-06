"""API endpoints for Patient Chat and Staff Search Debugger (Iteration 3)."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_patient, get_current_staff, CurrentUser
from app.rag.chat import handle_patient_chat, ChatResponse
from app.rag.retriever import get_hybrid_retriever

router = APIRouter(tags=["Chat & Search"])

class PatientChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="Patient message up to 500 characters.")
    history: List[Dict[str, str]] = Field(default_factory=list, description="Recent conversation history (last 6 messages).")

@router.post("/patient/chat", response_model=ChatResponse)
def patient_chat_endpoint(
    req: PatientChatRequest,
    patient: CurrentUser = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Patient chat assistant answering from clinic knowledge base with citations."""
    try:
        response = handle_patient_chat(
            message=req.message,
            history=req.history,
            patient_id=patient.id,
            db=db,
        )
        return response
    except Exception as e:
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

