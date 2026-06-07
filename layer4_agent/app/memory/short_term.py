# layer4_agent/app/memory/short_term.py
from datetime import datetime
from layer4_agent.app.memory.sqlite_store import save_turn

class ShortTermMemory:
    def __init__(self, session_id: str, channel: str = "telegram"):
        self.session_id = session_id
        self.channel = channel
        self.turns = []
        self.turn_counter = 0

    def add_turn(self, sender: str, message: str, p_scam: float = 0.0):
        self.turn_counter += 1
        turn = {
            "turn_number": self.turn_counter,
            "sender": sender,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "p_scam": p_scam,
            "channel": self.channel
        }
        self.turns.append(turn)

        # Persist to SQLite immediately
        save_turn(
            session_id=self.session_id,
            turn_number=self.turn_counter,
            sender=sender,
            message=message,
            p_scam=p_scam,
            channel=self.channel
        )
        print(f"[ShortTermMemory]: Turn {self.turn_counter} saved — {sender}: {message[:40]}...")

    def get_all_turns(self) -> list:
        return self.turns

    def get_last_n_turns(self, n: int) -> list:
        return self.turns[-n:]

    def clear(self):
        self.turns = []
        self.turn_counter = 0

    def get_turn_count(self) -> int:
        return self.turn_counter