"""Lightweight Sentiment Analyzer — keyword-based, no textblob dependency."""


class SentimentAnalyzer:
    """Keyword-based Sentiment Polarity & Label Analyzer (no textblob needed)."""

    _POSITIVE = {
        "good", "great", "nice", "awesome", "amazing", "love", "best", "happy",
        "excellent", "wonderful", "fantastic", "perfect", "beautiful", "thanks",
        "thank", "cool", "wow", "brilliant", "superb", "lit", "fire", "goat",
        "accha", "badhiya", "mast", "sahi", "kamaal", "zabardast", "shandar",
    }
    _NEGATIVE = {
        "bad", "worst", "hate", "terrible", "awful", "horrible", "disgusting",
        "stupid", "ugly", "useless", "boring", "annoying", "trash", "garbage",
        "sad", "angry", "frustrated", "pathetic", "bura", "ghatiya", "bakwas",
    }

    def analyze(self, text: str):
        """Return sentiment polarity (-1.0 to 1.0) and label."""
        words = set(text.lower().split())
        pos_count = len(words & self._POSITIVE)
        neg_count = len(words & self._NEGATIVE)
        total = pos_count + neg_count

        if total == 0:
            polarity = 0.0
        else:
            polarity = round((pos_count - neg_count) / total, 2)

        # Simple noun phrase extraction (capitalized consecutive words)
        noun_phrases = []

        if polarity > 0.2:
            label = "positive"
        elif polarity < -0.2:
            label = "negative"
        elif "?" in text:
            label = "questioning"
        else:
            label = "neutral"

        return polarity, label, noun_phrases
