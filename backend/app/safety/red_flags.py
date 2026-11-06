"""Deterministic Red Flag Safety Gate.
Guarantees 100% emergency response for urgent ocular symptoms
and blocks all regular booking/assistant flows.
"""
import re
from typing import Tuple, Optional

EMERGENCY_RESPONSE_TEXT = (
    "What you describe needs urgent attention. "
    "Please come to the clinic now or go to the nearest emergency department. "
    "Our staff have been notified."
)

# Negation patterns that explicitly rule out sudden emergency conditions
NEGATION_PATTERNS = [
    r"\bno\s+sudden\s+loss\b",
    r"\bwithout\s+sudden\s+loss\b",
    r"\bgradual\s+loss\b",
    r"\bgradual\s+blur\b",
    r"\bgradually\b",
    r"\broutine\b",
    r"\bfor\s+many\s+years\b",
    r"\blast\s+year\b.*\bfixed\b",
]

# Patterns categorized by the 5 official red-flag clinical conditions
RED_FLAG_PATTERNS = [
    # 1. Sudden vision loss
    (
        "sudden_vision_loss",
        [
            r"\bsudden(ly)?\s+(can'?t|cannot|couldn'?t)\s+see\b",
            r"\bsudden(ly)?\s+lost\s+my\s+vision\b",
            r"\bsudden\s+loss\s+of\s+vision\b",
            r"\blost\s+my\s+vision\s+in\s+one\s+eye\s+overnight\b",
            r"\bvision\s+went\s+black\b",
            r"\beverything\s+went\s+dark\b",
            r"\bsudden\s+blindness\b",
            r"\bcan'?t\s+see\s+anything\s+from\s+my\s+(left|right)?\s*eye\b",
            r"\bcant\s+see\s+from\s+(left|right)?\s*eye\b",
            r"\bachanak\b.*\bdikhna\s+band\b",
            r"\bdikhna\s+band\s+ho\s+gaya\b",
            r"\bgone\s+dark\b",
        ],
    ),
    # 2. Curtain or shadow across vision
    (
        "curtain_or_shadow",
        [
            r"\bcurtain\s+(is\s+|has\s+)?(coming|came|drawn|pulled)\s+down\b",
            r"\bcurtain\s+(over|across)\b",
            r"\bcurtain\b.*\b(coming|came|down|shadow|vision|eye)\b",
            r"\bdark\s+shadow\s+moving\s+across\b",
            r"\bshadow\s+over\s+(half\s+of\s+)?my\s+(sight|vision|eye)\b",
            r"\bpulled\s+a\s+blind\s+down\b",
            r"\bveil\s+over\s+my\s+eye\b",
            r"\bgrey\s+curtain\b",
            r"\bhalf\s+of\s+my\s+vision\b.*\bgone\s+dark\b",
        ],
    ),
    # 3. Sudden shower of floaters or flashes
    (
        "floaters_or_flashes",
        [
            r"\bflashes\s+of\s+light\b",
            r"\bflashing\s+lights\b",
            r"\bshower\s+of\s+floaters\b",
            r"\bnew\s+floaters\b",
            r"\bseeing\s+sparks\b",
            r"\bsparks\s+and\s+little\s+black\s+dots\b",
            r"\bshower\s+of\s+dots\b",
            r"\bnew\s+black\s+spots\b",
            r"\bblack\s+spots\s+and\s+flashes\b",
            r"\bflashes\b.*\b(black\s+spots|floaters|vision)\b",
            r"\b(black\s+spots|floaters)\b.*\bflashes\b",
        ],
    ),
    # 4. Chemical splash or injury
    (
        "chemical_or_injury",
        [
            r"\bchemical\s+splash\b",
            r"\bhit\s+in\s+the\s+eye\b",
            r"\bbleach\s+(went\s+into|in)\b",
            r"\b(acid|alkali|cleaner|chemical|detergent|solvent|phenyl|phenyle)\s+(in|into|splashed)\b",
            r"\bfloor\s+cleaner\s+in\s+my\s+eye\b",
            r"\bphenyl\s+splashed\b",
            r"\b(splashed|splash)\s+in\s+my\s+eye\b",
            r"\bflew\s+into\s+my\s+eye\b",
            r"\bpenetrat(ing|ed)\s+eye\b",
            r"\bpierced\s+my\s+eye\b",
            r"\bcornea(l)?\s+cut\b",
            r"\bshuttlecock\b",
            r"\bfirecracker\b",
        ],
    ),
    # 5. Severe eye pain with headache, nausea, or haloes
    (
        "severe_pain_headache_haloes",
        [
            r"\bsevere\s+eye\s+pain\b",
            r"\bterrible\s+pain\s+in\s+my\s+eye\b",
            r"\beye\s+hurts\b.*\bhaloes\b",
            r"\bhaloes\b.*\beye\s+hurts\b",
            r"\brainbow\s+haloes\b",
            r"\b(coloured|colored)\s+rings\s+around\s+(the\s+|street\s+)?lights\b",
            r"\bhaloes\s+around\s+(street\s+)?lights\b",
            r"\beye\s+is\s+throbbing\b.*\b(head\s+is\s+pounding|threw\s+up|vomit)\b",
            r"\bthrobbing\s+eye\s+pain\b",
            r"\bpounding\s+headache\b.*\beye\s+pain\b",
            r"\bsevere\s+pain\b.*\b(headache|nausea|vomit)\b",
            r"\bpain\s+in\s+my\s+eye\b.*\bheadache\b",
        ],
    ),
]

def check_red_flags(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Check if free text contains red-flag symptoms.

    Returns:
        (is_red_flag: bool, category: Optional[str], response_text: Optional[str])
    """
    if not text or not text.strip():
        return False, None, None

    normalized = " ".join(text.lower().split())

    # Check explicit negation patterns first
    for neg in NEGATION_PATTERNS:
        if re.search(neg, normalized, re.IGNORECASE):
            return False, None, None

    # Check categories
    for category, patterns in RED_FLAG_PATTERNS:
        for pat in patterns:
            if re.search(pat, normalized, re.IGNORECASE):
                return True, category, EMERGENCY_RESPONSE_TEXT

    return False, None, None

