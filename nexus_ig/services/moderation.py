"""ModerationEngine service for bad word detection and warnings."""
import re

LINK_RE = re.compile(r"https?://|www\.", re.IGNORECASE)

class ModerationEngine:
    def __init__(self, config=None, storage=None):
        self.config = config
        self.storage = storage

    def check_message(self, text: str, user_id: str, is_admin: bool = False) -> dict:
        if is_admin:
            return {"blocked": False, "reason": None, "word": None}

        lower_text = text.lower().strip()
        if LINK_RE.search(text):
            return {"blocked": True, "reason": "Links not allowed", "word": "link"}

        if self.storage:
            forbidden = self.storage.get_forbidden_words()
            for word in forbidden:
                clean_word = str(word).lower().strip()
                if clean_word and clean_word in lower_text:
                    return {"blocked": True, "reason": f"Forbidden word '{clean_word}' detected", "word": clean_word}

        return {"blocked": False, "reason": None, "word": None}
