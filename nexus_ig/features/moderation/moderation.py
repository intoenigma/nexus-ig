"""Moderation Engine & Lurkers Detector."""
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

def format_lurkers_report(lurkers: list[dict], threshold_days: int = 7) -> str:
    if not lurkers:
        return f"👻 LURKER REPORT 👻\n━━━━━━━━━━━━━━━━━━━━\nAwesome! No silent lurkers found (silent for >{threshold_days} days)."
    lines = [f"👻 SILENT LURKERS (No msgs >{threshold_days} days) 👻", "━━━━━━━━━━━━━━━━━━━━"]
    for l in lurkers[:25]:
        uname = l.get("username", "User")
        days = l.get("inactive_days", 0)
        lines.append(f"• @{uname} - {days}d silent")
    return "\n".join(lines)
