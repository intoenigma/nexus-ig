from ..knowledge.database import FactDatabase


class FeedbackProcessor:
    """Adjusts fact confidence scores based on user feedback and confirmations."""

    def __init__(self, db: FactDatabase):
        self.db = db

    def register_positive_feedback(self, subject: str, predicate: str):
        """Boost fact confidence score on user confirmation."""
        fact = self.db.get_fact(subject, predicate)
        if fact:
            fact.confidence = min(1.0, fact.confidence + 0.25)
            self.db.add_fact(subject, predicate, fact.object_val, initial_confidence=fact.confidence)

    def register_negative_feedback(self, subject: str, predicate: str):
        """Lower fact confidence score on rejection."""
        fact = self.db.get_fact(subject, predicate)
        if fact:
            fact.confidence = max(0.0, fact.confidence - 0.30)
            self.db.add_fact(subject, predicate, fact.object_val, initial_confidence=fact.confidence)
