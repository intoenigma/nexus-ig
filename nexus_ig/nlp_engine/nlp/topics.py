"""Lightweight Topic Extractor — no wordfreq dependency."""

from typing import List, Tuple

# Common English stop words (no external library needed)
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
    "him", "her", "his", "its", "they", "them", "their", "this", "that",
    "these", "those", "am", "not", "no", "nor", "but", "and", "or",
    "if", "then", "so", "too", "very", "just", "about", "for", "with",
    "from", "to", "in", "on", "at", "by", "of", "up", "out", "off",
    "over", "into", "what", "which", "who", "whom", "how", "when",
    "where", "why", "all", "each", "every", "both", "few", "more",
    "some", "any", "most", "other", "than", "such", "only", "own",
    "same", "also", "here", "there", "now", "then", "get", "got",
    "mai", "hai", "ka", "ki", "ke", "ko", "se", "ne", "par", "mein",
    "kya", "koi", "kuch", "yeh", "woh", "toh", "bhi", "nhi", "nahi",
    "haan", "aur", "ya", "jo", "jab", "tab", "ab", "hum", "tum",
}


class TopicExtractor:
    """Extract key topics using stop-word filtering and length scoring."""

    def extract_keywords(self, lemmas: List[str]) -> List[Tuple[str, float]]:
        """Return keyphrases scored by rarity (longer + non-stop = higher score)."""
        key_words = []
        seen = set()
        for token in lemmas:
            lower_t = token.lower()
            if len(lower_t) > 2 and lower_t not in _STOP_WORDS and lower_t not in seen:
                seen.add(lower_t)
                # Score based on word length (longer = more specific = higher score)
                score = round(min(len(lower_t) * 0.5, 5.0), 2)
                key_words.append((lower_t, score))
        key_words.sort(key=lambda x: x[1], reverse=True)
        return key_words[:5]
