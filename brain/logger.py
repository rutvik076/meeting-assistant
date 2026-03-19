from pathlib import Path
from datetime import datetime

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def log_qa(question: str, answer: str, latency_ms: int):
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"session_{today}.txt"
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = (
        f"[{timestamp}] ({latency_ms}ms)\n"
        f"Q: {question}\n"
        f"A: {answer}\n"
        f"{'-' * 60}\n"
    )
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
