import anthropic
from brain.context import ConversationContext
from brain.profile import load_profile, build_persona_prompt
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
context = ConversationContext()

FALLBACK_PROMPT = """You are a real-time meeting assistant.
Answer questions concisely in 2-4 sentences. Be direct.
No preamble like 'Great question!'. Start with the answer.
For coding questions give a short code example."""

async def generate_answer(question: str) -> str:
    # Reload profile every call — edits apply instantly, no restart needed
    profile = load_profile()
    persona = build_persona_prompt(profile)
    system = persona if persona else FALLBACK_PROMPT

    context.add_user(question)
    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=350,
        system=system,
        messages=context.get_messages(),
    )
    answer = response.content[0].text.strip()
    context.add_assistant(answer)
    return answer
