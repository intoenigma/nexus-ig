class ConfidenceScorer:
    """Evaluates fact and intent confidence scores."""

    def score_fact(self, confirmations: int, source: str) -> float:
        """Calculate confidence score (0.0 to 1.0) based on confirmations."""
        base = 0.3 if source == "user_input" else 0.8
        score = base + (confirmations - 1) * 0.2
        return round(min(1.0, score), 2)
