"""NLTK-free Tokenizer — uses simple regex splitting as fallback for Termux/low RAM."""

import re


class Tokenizer:
    """Lightweight Word Tokenizer & Lemmatizer (no nltk dependency)."""

    # Common English suffixes for basic lemmatization
    _SUFFIX_RULES = [
        ("ies", "y"), ("ves", "f"), ("ses", "s"), ("ing", ""),
        ("ed", ""), ("ly", ""), ("tion", "te"), ("ness", ""),
    ]

    def __init__(self):
        self._word_re = re.compile(r"[a-zA-Z0-9]+")

    def _basic_lemmatize(self, word: str) -> str:
        """Simple suffix-stripping lemmatizer (no nltk/wordnet needed)."""
        if len(word) <= 3:
            return word
        for suffix, replacement in self._SUFFIX_RULES:
            if word.endswith(suffix) and len(word) - len(suffix) >= 2:
                return word[: -len(suffix)] + replacement
        return word

    def tokenize_and_lemmatize(self, text: str):
        """Tokenize text into lowercase tokens & lemmatized roots."""
        tokens = self._word_re.findall(text.lower())
        lemmas = [self._basic_lemmatize(t) for t in tokens if t.isalnum()]
        return tokens, lemmas
