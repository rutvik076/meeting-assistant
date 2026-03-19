import anthropic
import json
from collections import deque
from brain.profile import load_profile, build_persona_prompt
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

_history: deque = deque(maxlen=8)

AGENT_SYSTEM = """\
You are a smart real-time assistant helping a candidate in a live job interview.

Your ONLY job: read the conversation and decide what action to take RIGHT NOW.

Return ONLY raw JSON — no markdown, no explanation:

{
  "action": "ANSWER" | "HINT" | "SKIP",
  "reason": "one short sentence",
  "speaker": "interviewer" | "candidate" | "unclear",
  "answer": "full answer in first person (ONLY if action is ANSWER)",
  "hint":   "one coaching sentence (ONLY if action is HINT)"
}

=== ACTION DECISION RULES ===

Return ANSWER when:
- The interviewer asked ANY question directed at the candidate
- Examples: "Tell me about yourself", "What is X?", "How do you Y?",
  "What did you work on?", "Can you explain...", "Have you worked with...",
  "Where do you see yourself...", "What is [project] and what did you do?"
- Even follow-up or clarifying questions from interviewer → ANSWER
- Utterance ends with "?" or starts with What/How/Why/Tell/Can/Have/Do/Did/Where/When/Who

Return HINT when:
- The CANDIDATE is speaking and giving a vague or incomplete answer
- Only trigger when candidate is clearly missing something important

Return SKIP when:
- The CANDIDATE is speaking confidently in first-person detail
- Social openers: "how are you", "how was your day", "nice to meet you"
- Small talk, filler, incomplete fragments under 5 words
- Interviewer says "okay", "great", "I see", "one moment", "sure"
- YOU asking for clarification ("sorry what did you ask", "can you repeat")

=== CRITICAL ===
- NEVER skip a real question from the interviewer
- If uncertain → lean ANSWER not SKIP
- Candidate speaking first-person ("I have", "I built") → SKIP or HINT only
- Do NOT return ANSWER when the candidate is the one speaking\
"""

CLASSIFY_SYSTEM = """\
You are a conversation classifier. Read the conversation and latest utterance.
Return ONLY raw JSON:

{
  "action": "ANSWER" | "HINT" | "SKIP",
  "reason": "one short sentence",
  "speaker": "interviewer" | "candidate" | "unclear"
}

OVERRIDE RULE — apply this FIRST before anything else:
If the latest utterance starts with any of these words:
What, How, Can, Could, Why, Where, When, Who, Tell, Explain, Describe,
Have, Do, Did, Is, Are, Was, Were, Will, Would, Should
→ ALWAYS return action=ANSWER and speaker=interviewer
   regardless of previous context.

Only after checking the override:
- ANSWER if interviewer asked a question
- SKIP if candidate is speaking confidently  
- HINT if candidate is giving incomplete answer
- Lean ANSWER when uncertain\
"""


def _build_context_block(new_utterance: str) -> str:
    lines = ["=== RECENT CONVERSATION ==="]
    for turn in _history:
        lines.append(turn)
    lines.append("")
    lines.append("=== LATEST UTTERANCE ===")
    lines.append(new_utterance)
    return "\n".join(lines)


async def classify_utterance(text: str) -> dict:
    """Fast classify-only call — no answer generated yet."""
    profile = load_profile()
    persona = build_persona_prompt(profile)
    system = (persona + "\n\n" + CLASSIFY_SYSTEM) if persona else CLASSIFY_SYSTEM

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=120,
        system=system,
        messages=[{"role": "user", "content": _build_context_block(text)}],
    )
    raw = response.content[0].text.strip()
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                raw = part
                break
    try:
        return json.loads(raw)
    except Exception:
        return {"action": "SKIP", "reason": "parse error", "speaker": "unclear"}


ANSWER_SYSTEM = """\
You are a real-time interview coach. Answer the question below in first person \
as the candidate. Write naturally — no JSON, no bullet prefixes, no preamble.
Rules:
- Answer in 2-5 sentences. Direct and confident.
- Use "I", "my", "I've built..." — always first person.
- For technical questions: clear explanation + one short code example if helpful.
- For personal questions: draw from the candidate profile provided.
- Never say "As an AI" or break character.\
"""

async def stream_answer(text: str, speaker: str):
    """
    Streams plain-text answer tokens one chunk at a time.
    Uses a separate plain-text system prompt — NOT the JSON agent prompt.
    """
    profile = load_profile()
    persona = build_persona_prompt(profile)

    # Use plain answer prompt — never the JSON classifier prompt
    system = (persona + "\n\n" + ANSWER_SYSTEM) if persona else ANSWER_SYSTEM

    async with client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=400,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Question asked in the interview: {text}"
        }],
    ) as stream:
        async for token in stream.text_stream:
            yield token

    # Update history after full stream completes
    _history.append(f"[{speaker.upper()}]: {text}")


async def process_utterance(text: str) -> dict:
    """Non-streaming fallback — returns full result dict."""
    profile = load_profile()
    persona = build_persona_prompt(profile)
    system = (persona + "\n\n" + AGENT_SYSTEM) if persona else AGENT_SYSTEM

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": _build_context_block(text)}],
    )
    raw = response.content[0].text.strip()
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                raw = part
                break
    try:
        result = json.loads(raw)
    except Exception:
        result = {"action": "SKIP", "reason": "parse error", "speaker": "unclear"}

    speaker = result.get("speaker", "unclear")
    _history.append(f"[{speaker.upper()}]: {text}")
    return result