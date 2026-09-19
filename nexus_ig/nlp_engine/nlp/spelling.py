from symspellpy import SymSpell, Verbosity
import wordfreq
from ...core import console


class SpellCorrector:
    """Spell correction using symspellpy populated via wordfreq (Lazy Initialization)."""

    def __init__(self, vocabulary_size: int = 5000):
        self.vocabulary_size = vocabulary_size
        self.sym_spell = None

    def _ensure_initialized(self):
        """Lazy load SymSpell dictionary on first use for zero startup delay."""
        if self.sym_spell is not None:
            return
        self.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        try:
            top_words = wordfreq.top_n_list("en", self.vocabulary_size)
            for rank, word in enumerate(top_words):
                freq = max(1, self.vocabulary_size - rank)
                self.sym_spell.create_dictionary_entry(word, freq)
        except Exception as exc:
            console.warning(f"SymSpell init notice: {exc}")

    def correct(self, text: str) -> str:
        """Correct misspelled words while preserving format & Hinglish terms."""
        words = text.split()
        corrected = []
        for word in words:
            if len(word) <= 2 or not word.isalpha() or word.startswith("http"):
                corrected.append(word)
                continue
            try:
                self._ensure_initialized()
                suggestions = self.sym_spell.lookup(
                    word.lower(), Verbosity.TOP, max_edit_distance=2
                )
                if suggestions:
                    sug = suggestions[0].term
                    if word[0].isupper():
                        sug = sug.capitalize()
                    corrected.append(sug)
                else:
                    corrected.append(word)
            except Exception:
                corrected.append(word)
        return " ".join(corrected)
