from collections import deque
from config import CONTEXT_TURNS

class ConversationContext:
    def __init__(self):
        # Each turn = one user + one assistant message
        # deque maxlen = CONTEXT_TURNS * 2 to store both sides
        self._turns = deque(maxlen=CONTEXT_TURNS * 2)

    def add_user(self, text: str):
        self._turns.append({"role": "user", "content": text})

    def add_assistant(self, text: str):
        self._turns.append({"role": "assistant", "content": text})

    def get_messages(self) -> list:
        return list(self._turns)

    def clear(self):
        self._turns.clear()