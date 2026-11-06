"""Routing Judge for NetraCare Evals (Iteration 5).
Evaluates which clinical speciality the assistant's reply suggests.
Matches against NetraCare's official specialities:
- Cataract
- Glaucoma
- Retina
- Cornea
- Refractive
- Dry eye
- Paediatric
- Squint
- General
- none (when problem is not an eye issue)
"""
import os
import re
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.config import settings

VALID_SPECIALITIES = [
    "Cataract",
    "Glaucoma",
    "Retina",
    "Cornea",
    "Refractive",
    "Dry eye",
    "Paediatric",
    "Squint",
    "General",
    "none"
]

class RoutingJudgeOutput(BaseModel):
    speciality: str = Field(description="The exact clinical speciality the reply suggests, or 'none' if not an eye problem")
    reason: str = Field(description="Brief explanation of why this speciality was identified")


ROUTING_PROMPT = """You are an expert evaluator for NetraCare Eye Clinic.
Determine which clinical speciality the AI assistant's reply recommends or directs the patient to.

Choose EXACTLY ONE from this list:
- Cataract
- Glaucoma
- Retina
- Cornea
- Refractive
- Dry eye
- Paediatric
- Squint
- General
- none (use 'none' if the reply states NetraCare only treats eye conditions, or the problem is non-ophthalmic such as back pain)

PATIENT MESSAGE:
\"\"\"{message}\"\"\"

ASSISTANT REPLY:
\"\"\"{response}\"\"\"

{format_instructions}
"""

def _rule_based_routing_eval(response: str) -> RoutingJudgeOutput:
    """Deterministic extractor of speciality from response text."""
    resp_lower = response.lower()
    
    # Check for 'none' (non-eye condition, back pain, or generic rejection)
    if "only" in resp_lower and ("eye" in resp_lower or "eyes" in resp_lower):
        if "back" in resp_lower or "cannot treat" in resp_lower or "only treats eyes" in resp_lower or "only looks after eyes" in resp_lower:
            return RoutingJudgeOutput(speciality="none", reason="Reply explains clinic only treats eye conditions")

    # Order by specificity
    checks = [
        ("paediatric", "Paediatric"),
        ("pediatric", "Paediatric"),
        ("squint", "Squint"),
        ("retina", "Retina"),
        ("glaucoma", "Glaucoma"),
        ("cataract", "Cataract"),
        ("refractive", "Refractive"),
        ("dry eye", "Dry eye"),
        ("cornea", "Cornea"),
        ("general", "General"),
    ]

    # Also map doctor names if speciality name is omitted
    doc_map = [
        ("dr. kiran shah", "Retina"),
        ("dr. shah", "Retina"),
        ("dr. meera iyer", "Glaucoma"),
        ("dr. iyer", "Glaucoma"),
        ("dr. anand rao", "Cataract"),
        ("dr. rao", "Cataract"),
        ("dr. fatima khan", "Dry eye"), # Or Cornea/Refractive
        ("dr. khan", "Dry eye"),
        ("dr. vikram menon", "Paediatric"),
        ("dr. menon", "Paediatric"),
    ]

    for keyword, spec in checks:
        if keyword in resp_lower:
            return RoutingJudgeOutput(speciality=spec, reason=f"Mentioned {keyword}")

    for doc, spec in doc_map:
        if doc in resp_lower:
            return RoutingJudgeOutput(speciality=spec, reason=f"Recommended {doc}")

    return RoutingJudgeOutput(speciality="none", reason="No specific speciality recommended")


def judge_routing(message: str, response: str) -> RoutingJudgeOutput:
    """Extract recommended speciality using LLM or rule-based fallback."""
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
    judge_model_name = os.getenv("JUDGE_MODEL", "gemini-2.5-flash")

    if api_key:
        try:
            if "openai" in judge_model_name.lower() or os.getenv("OPENAI_API_KEY"):
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(model=judge_model_name, temperature=0.0, timeout=15)
            else:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(model=judge_model_name, google_api_key=api_key, temperature=0.0, timeout=15)

            parser = PydanticOutputParser(pydantic_object=RoutingJudgeOutput)
            prompt = ChatPromptTemplate.from_template(ROUTING_PROMPT)
            chain = prompt | llm | parser

            result = chain.invoke({
                "message": message,
                "response": response,
                "format_instructions": parser.get_format_instructions(),
            })
            return result
        except Exception:
            pass

    return _rule_based_routing_eval(response)


def score_routing_reply(
    judged_speciality: str,
    expected_speciality: str,
    also_accept: str = ""
) -> Tuple[bool, str]:
    """Compare judged speciality with expected_speciality and also_accept.
    Returns (passed: bool, reason: str).
    """
    j_clean = judged_speciality.strip().lower()
    exp_clean = expected_speciality.strip().lower()
    accept_list = [exp_clean] + [a.strip().lower() for a in also_accept.split(";") if a.strip()]

    if j_clean in accept_list:
        return True, f"Correctly routed to {judged_speciality}"
    else:
        return False, f"Routed to '{judged_speciality}', expected '{expected_speciality}' (accepted: {accept_list})"

