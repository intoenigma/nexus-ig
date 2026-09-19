from enum import Enum


class Decision(str, Enum):
    RESPOND = "RESPOND"
    MAYBE = "MAYBE"
    SILENCE = "SILENCE"


class DecisionEngine:
    """Selects appropriate response mode & enforces Decision.SILENCE as a first-class feature."""

    def decide_mode(self, should_reply: bool, score: float, intent: str) -> Decision:
        if not should_reply or score < 30.0:
            return Decision.SILENCE
        if score >= 60.0:
            return Decision.RESPOND
        return Decision.MAYBE
