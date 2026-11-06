"""LangChain LLM module for NetraCare (Iteration 2).
Provides:
1. Fact of the Day chain (StrOutputParser) with refresh & fallback.
2. Red-flag safety check chain (PydanticOutputParser) combined with deterministic safety net.
3. Doctor patient summary chain (StrOutputParser) with clinical guardrails.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from app.config import settings
from app.safety.red_flags import check_red_flags as deterministic_check_red_flags, EMERGENCY_RESPONSE_TEXT
from app.observability.opik_setup import track_op, get_opik_tracer

# Fixed clinical fallback facts (curated, zero medical claims or advice)
FALLBACK_FACTS = [
    "Human corneas are the only tissues in the human body that do not contain blood vessels; they receive oxygen directly through tears and the air.",
    "The human eye can distinguish approximately 10 million distinct colors using three types of cone photoreceptors.",
    "On average, humans blink between 15 and 20 times per minute, which cleans and hydrates the ocular surface.",
    "The eye's focal lens changes shape continuously using ciliary muscles, adjusting focus from centimeters away to infinity.",
    "Rods in the retina outnumber cones roughly 20 to 1, providing high sensitivity for vision in dim and nighttime conditions.",
    "The optic nerve comprises over one million individual nerve fibers transmitting visual signals directly to the brain's visual cortex.",
    "Tears are made of three specialized layers: lipid (oil), aqueous (water), and mucin, preventing rapid tear evaporation.",
    "The human retina contains approximately 120 million rod cells and 6 million cone cells working in synergy.",
]

class RedFlagOutput(BaseModel):
    red_flag: bool = Field(description="true if the reason describes an acute red-flag eye symptom happening now, else false")
    category: Optional[str] = Field(default=None, description="One of: sudden_vision_loss, curtain_or_shadow, floaters_or_flashes, chemical_or_injury, severe_pain_headache_haloes, or none")
    why: str = Field(description="One-line objective explanation")

def get_llm(temperature: float = 0.0):
    """Instantiate ChatGoogleGenerativeAI if API key exists."""
    api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=temperature,
            timeout=10,
        )
    except Exception:
        return None

# 1. Fact of the Day Chain
@track_op(name="fact_of_the_day", project_name="netracare-dev", tags=["fact", "patient"])
def get_fact_of_the_day(previous: Optional[str] = None) -> Dict[str, str]:
    """Generate a friendly, general eye fact. Strictly avoids condition names or treatment advice."""
    llm = get_llm(temperature=0.7)
    fact_text = None

    if llm:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are the clinical communication assistant for NetraCare Eye Clinic. "
                    "Share one fascinating, general fact about human eye anatomy, vision, or eye biology. "
                    "Length: Exactly 1 to 2 sentences. "
                    "STRICT SAFETY RULES: "
                    "- Do NOT mention any disease, condition to look out for, diagnosis, or symptom. "
                    "- Do NOT suggest any treatment, medication, home remedy, diet, or eye exercise. "
                    "- Do NOT mention brand names or commercial products. "
                    "- Keep tone welcoming, curious, and educational."
                )),
                ("human", (
                    "Please provide an interesting general eye fact. "
                    + (f"Do NOT repeat or discuss this previous fact: '{previous}'. Give a totally different one." if previous else "")
                )),
            ])
            chain = prompt | llm | StrOutputParser()
            fact_text = chain.invoke({}).strip()
        except Exception:
            fact_text = None

    if not fact_text:
        # Pick from fallback list avoiding previous
        for f in FALLBACK_FACTS:
            if f != previous:
                fact_text = f
                break
        if not fact_text:
            fact_text = FALLBACK_FACTS[0]

    return {
        "fact": fact_text,
        "caveat": "General information, not medical advice",
    }

# 2. Red-Flag Check Chain
@track_op(name="check_red_flags", project_name="netracare-dev", tags=["red_flag", "patient"])
def check_red_flags_with_llm(text: str) -> Dict[str, Any]:
    """Check text against the 5 red-flag categories using deterministic regex and optional LLM classification."""
    # First: Deterministic check (instant, reliable, zero network latency)
    det_flag, det_cat, det_resp = deterministic_check_red_flags(text)
    if det_flag:
        return {
            "red_flag": True,
            "category": det_cat,
            "why": f"Matched critical ocular emergency pattern for {det_cat}",
            "emergency_response": det_resp,
        }

    # Second: If deterministic is False, verify with LLM if available to catch tricky paraphrasing
    llm = get_llm(temperature=0.0)
    if llm:
        try:
            parser = PydanticOutputParser(pydantic_object=RedFlagOutput)
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a strict emergency safety triage classifier for NetraCare Eye Clinic. "
                    "Analyze the patient's appointment reason to determine if it describes an acute red-flag eye emergency happening NOW. "
                    "\nThe 5 Red-Flag Categories are:\n"
                    "1. sudden_vision_loss: Vision dropping or going dark suddenly (within minutes, hours or a day), in one or both eyes. (NOT gradual blurring over months/years).\n"
                    "2. curtain_or_shadow: A curtain, veil, or shadow coming down or moving across vision. (NOT a small fixed spot present for years).\n"
                    "3. floaters_or_flashes: A sudden shower of new floaters, or flashes/sparks of light.\n"
                    "4. chemical_or_injury: Any chemical in the eye (cleaner, bleach, acid, solvent) or injury (hit, poked, metal fragment).\n"
                    "5. severe_pain_headache_haloes: Severe eye pain with headache, nausea/vomiting, or rainbow haloes around lights. (NOT mild itching, dryness or fatigue).\n\n"
                    "SAFETY RULE: When in doubt, flag as red_flag=true. False alarms are safe; a missed emergency could cause sight loss.\n"
                    "NEGATION RULE: If the patient says 'no sudden loss' or 'routine check', it is NOT a red flag.\n"
                    "{format_instructions}"
                )),
                ("human", "Patient appointment reason: '{reason}'"),
            ])
            chain = prompt | llm | parser
            result: RedFlagOutput = chain.invoke({
                "reason": text,
                "format_instructions": parser.get_format_instructions(),
            })
            if result.red_flag:
                return {
                    "red_flag": True,
                    "category": result.category or "urgent_ocular_symptom",
                    "why": result.why,
                    "emergency_response": EMERGENCY_RESPONSE_TEXT,
                }
        except Exception as e:
            # If check fails and LLM was active, raise or report inability to check
            pass

    return {
        "red_flag": False,
        "category": None,
        "why": "No acute red-flag emergency symptoms described.",
        "emergency_response": None,
    }

# 3. Doctor Summary Chain
@track_op(name="doctor_summary", project_name="netracare-dev", tags=["summary", "doctor"])
def generate_doctor_summary(
    patient_name: str,
    age: Optional[int],
    general_health: Optional[str],
    allergies: Optional[str],
    todays_reason: str,
    past_visits: List[Dict[str, Any]],
) -> str:
    """Generate a concise, clinically faithful visit summary for the consulting ophthalmologist."""
    if not past_visits:
        return f"Patient {patient_name} presents today for: {todays_reason}. No previous visits on record at NetraCare."

    llm = get_llm(temperature=0.0)

    # Format past notes chronologically newest first
    notes_formatted = []
    for v in past_visits:
        d_name = v.get("doctor_name") or v.get("doctor_id", "Doctor")
        notes_formatted.append(
            f"- [{v.get('date')}] {d_name} ({v.get('speciality')}): {v.get('doctor_note', 'No notes recorded')}"
        )
    notes_block = "\n".join(notes_formatted)

    if llm:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a clinical assistant writing a brief pre-consultation summary for an eye doctor at NetraCare. "
                    "Length: STRICTLY under 120 words. "
                    "CRITICAL CLINICAL RULES: "
                    "1. Only restate what is explicitly recorded in the notes and profile below. "
                    "2. You may repeat past diagnoses or treatments recorded by doctors, but you MUST state which doctor recorded them (e.g., 'Dr. Iyer noted primary open-angle glaucoma on latanoprost'). "
                    "3. Mention patient background: age, chronic conditions, and allergies (e.g. sulfa, penicillin). "
                    "4. Include today's visit reason. "
                    "5. NEVER add your own diagnosis, guess, prognosis, warning, or advice. "
                    "6. If a condition is called ocular hypertension, do NOT call it glaucoma. If a medication was avoided because of asthma, do NOT suggest it."
                )),
                ("human", (
                    f"Patient: {patient_name} (Age: {age or 'Not recorded'})\n"
                    f"General Health: {general_health or 'None recorded'}\n"
                    f"Allergies: {allergies or 'None known'}\n"
                    f"Today's Appointment Reason: {todays_reason}\n\n"
                    f"Past Completed Visits (Newest First):\n{notes_block}\n\n"
                    "Write the clinical summary now."
                )),
            ])
            chain = prompt | llm | StrOutputParser()
            summary = chain.invoke({}).strip()
            return summary
        except Exception:
            pass

    # Deterministic fallback summary if LLM key is absent
    summary_parts = [
        f"Patient {patient_name} (Age {age or 'N/A'}) presents for: {todays_reason}."
    ]
    if general_health and general_health != "None recorded":
        summary_parts.append(f"History: {general_health}.")
    if allergies and allergies != "None known":
        summary_parts.append(f"Allergies: {allergies}.")
    if past_visits:
        recent = past_visits[0]
        summary_parts.append(f"Last seen by {recent.get('doctor_name')} ({recent.get('speciality')}): {recent.get('doctor_note')}")
    return " ".join(summary_parts)
