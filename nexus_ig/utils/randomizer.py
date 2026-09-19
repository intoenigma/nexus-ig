"""Random selection utilities."""
import random
import re

def pick_random_revive_message(raw_messages: str) -> str:
    if not raw_messages:
        return "kha ho saalo aa jao group mai"
    parts = [p.strip() for p in re.split(r"[,|;]", raw_messages) if p.strip()]
    if not parts:
        return raw_messages.strip()
    return random.choice(parts)
