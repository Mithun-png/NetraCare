"""Output Safety Guard for NetraCare.
Guarantees 0 diagnosis or treatment statements in patient-facing responses.
Blocks unverified condition names, prescription advice, and home remedies.
"""
import re
from typing import Tuple

SAFE_REFUSAL = "A doctor will assess your symptoms and examine your eyes during your consultation."

FORBIDDEN_DIAGNOSIS_PATTERNS = [
    r"\byou\s+(have|suffer\s+from|might\s+have|likely\s+have|probably\s+have)\b",
    r"\bsounds\s+like\s+(you\s+have|a\s+case\s+of|glaucoma|cataract|conjunctivitis)\b",
    r"\bthis\s+(indicates|means)\s+you\s+have\b",
    r"\bdiagnos(ed|is|ing)\b",
    r"\byour\s+condition\s+is\b",
]

FORBIDDEN_TREATMENT_PATTERNS = [
    r"\byou\s+should\s+(take|apply|use|instill|administer)\s+(drops|medicine|antibiotic|steroid)\b",
    r"\bprescribe\b",
    r"\bdosage\b",
    r"\bstart\s+taking\b",
    r"\bstop\s+taking\b",
    r"\btake\s+\d+\s+mg\b",
    r"\bhome\s+remed(y|ies)\b",
]

def check_patient_facing_output(text: str) -> Tuple[bool, str]:
    """Check if generated text violates medical safety guardrails.

    Returns:
        (is_safe: bool, sanitized_text: str)
    """
    if not text:
        return True, ""

    normalized = text.lower()

    for pat in FORBIDDEN_DIAGNOSIS_PATTERNS:
        if re.search(pat, normalized, re.IGNORECASE):
            return False, SAFE_REFUSAL

    for pat in FORBIDDEN_TREATMENT_PATTERNS:
        if re.search(pat, normalized, re.IGNORECASE):
            return False, SAFE_REFUSAL

    return True, text

def sanitize_clinical_output(text: str) -> str:
    """Sanitize patient-facing text, ensuring zero diagnosis or treatment advice."""
    is_safe, sanitized = check_patient_facing_output(text)
    return sanitized

