from ..knowledge.database import FactDatabase


class ContinuousLearner:
    """Safely extracts unverified facts with initial confidence = 0.20."""

    def __init__(self, db: FactDatabase):
        self.db = db

    def learn_from_message(self, user_name: str, text: str):
        """Extract unverified candidate facts without making them immediate truth."""
        lower = text.lower()
        if " is " in lower:
            parts = lower.split(" is ", 1)
            if len(parts) == 2 and len(parts[0]) < 20 and len(parts[1]) < 30:
                self.db.add_fact(parts[0].strip(), "is", parts[1].strip(), initial_confidence=0.20)
