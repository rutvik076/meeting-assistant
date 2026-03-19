import re

# Tier 1: explicit question words and patterns (~1ms)
_QUESTION_PATTERNS = [
    r'\b(what|how|why|when|where|who|which|whose|whom)\b',
    r'\b(can|could|would|should|do|does|did|is|are|was|were|will|have|has)\s+\w+',
    r'\?',
    r'\b(explain|define|describe|tell me|show me|help me|walk me through)\b',
    r'\b(difference between|compare|versus|vs\.?|pros and cons)\b',
    r'\b(give me|what are|list|name|examples? of)\b',
]

# Tier 2: implicit curiosity phrases (no question word, but clearly asking)
_CURIOSITY_PHRASES = [
    "i don't understand",
    "i'm not sure",
    "not sure about",
    "i'm confused",
    "how do you",
    "any idea",
    "do you know",
    "any thoughts",
    "any suggestions",
    "help me",
    "walk me through",
    "step by step",
    "what's the best way",
    "best practice",
    "which one should",
]

# Short utterances that are never real questions
_NOISE_PATTERNS = [
    r'^(yes|no|okay|ok|sure|right|got it|hmm|uh|um|yeah|yep|nope)\.?$',
    r'^(thanks|thank you|sounds good|makes sense|alright)\.?$',
]

def is_question(text: str) -> bool:
    """
    Returns True if text is a question or implicit request for information.
    Designed to be fast — no LLM calls, pure heuristic.
    """
    if not text or len(text.split()) < 3:
        return False

    t = text.lower().strip().rstrip('.')

    # Reject obvious non-questions first
    for pattern in _NOISE_PATTERNS:
        if re.match(pattern, t):
            return False

    # Tier 1: explicit patterns
    for pattern in _QUESTION_PATTERNS:
        if re.search(pattern, t):
            return True

    # Tier 2: implicit curiosity
    for phrase in _CURIOSITY_PHRASES:
        if phrase in t:
            return True

    return False