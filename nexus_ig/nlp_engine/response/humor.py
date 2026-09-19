import random
from typing import Optional


class HumorEngine:
    """Contextual jokes, callbacks, and group banter."""

    JOKES = [
        "Why do programmers prefer dark mode? Because light attracts bugs! 😂",
        "There are 10 types of people in the world: those who understand binary, and those who don't.",
        "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?' 😂",
    ]

    def get_joke(self) -> str:
        """Return a random joke."""
        return random.choice(self.JOKES)

    def get_callback_joke(self, user_name: str, topic: str) -> Optional[str]:
        """Generate contextual callback joke if appropriate."""
        if "exam" in topic or "paper" in topic:
            return f"@{user_name} bhai padhai kar lo, warna result ke baad phone switched off rakhna padega! 😂"
        if "late" in topic:
            return f"@{user_name} tu aaj time pe aa gaya? Screenshot le leta hu! 📸"
        return None
