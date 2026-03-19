import json
from pathlib import Path

PROFILE_PATH = Path("profile.json")

DEFAULT_PROFILE = {
    "name": "",
    "role": "",
    "experience": "",
    "skills": "",
    "projects": "",
    "education": "",
    "goal": "",
    "extra": "",
}

def load_profile() -> dict:
    if PROFILE_PATH.exists():
        try:
            return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_PROFILE.copy()

def save_profile(data: dict):
    PROFILE_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def build_persona_prompt(profile: dict) -> str:
    if not profile.get("name"):
        return ""

    lines = [
        f"You are assisting {profile['name']} in real-time during a live meeting or interview.",
        "Answer ALL questions in FIRST PERSON as if YOU ARE this person.",
        "NEVER say 'I am an AI' or 'As an AI' — you are speaking AS this person.",
        "NEVER break character. Always use 'I', 'my', 'I've built...' etc.",
        "",
        "=== CANDIDATE PROFILE ===",
    ]
    if profile.get("name"):        lines.append(f"Name: {profile['name']}")
    if profile.get("role"):        lines.append(f"Target role: {profile['role']}")
    if profile.get("experience"):  lines.append(f"Experience: {profile['experience']}")
    if profile.get("skills"):      lines.append(f"Skills: {profile['skills']}")
    if profile.get("projects"):    lines.append(f"Key projects: {profile['projects']}")
    if profile.get("education"):   lines.append(f"Education: {profile['education']}")
    if profile.get("goal"):        lines.append(f"Career goal: {profile['goal']}")
    if profile.get("extra"):       lines.append(f"Additional info: {profile['extra']}")
    lines += [
        "=========================",
        "",
        "ANSWER STYLE:",
        "- 'Tell me about yourself' → confident 3-sentence pitch using their background",
        "- 'What are your strengths?' → pick 2 from their skills/projects",
        "- 'Why this role?' → connect their goal to the role",
        "- Technical questions → answer correctly and directly",
        "- Experience questions → reference their actual projects above",
        "- Keep answers to 3-5 sentences. Confident, natural, first-person.",
    ]
    return "\n".join(lines)
