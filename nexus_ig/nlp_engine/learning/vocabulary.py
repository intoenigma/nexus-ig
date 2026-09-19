from typing import Dict


class GroupVocabulary:
    """Tracks group inside jokes and custom terminology."""

    def __init__(self):
        self.term_counts: Dict[str, int] = {}

    def track_term(self, term: str):
        """Increment frequency of group-specific terms."""
        t_lower = term.lower()
        self.term_counts[t_lower] = self.term_counts.get(t_lower, 0) + 1
