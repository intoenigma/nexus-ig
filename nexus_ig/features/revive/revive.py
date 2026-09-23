"""Group Revive Feature for quiet group chats."""
import random
import time

REVIVE_MESSAGES = [
    "group mai sannata kyu pada hai? 🤐",
    "sab log kaha gayab hain? 👀",
    "kisi ki ungli chalti hai ya nahi? 😂",
    "shant kyu ho sab log? Koi mazedaar baat batao! ✨",
]

def check_revive(last_activity_time: int, threshold_seconds: int = 86400) -> bool:
    """Returns True if group has been inactive longer than threshold."""
    now = int(time.time())
    return (now - last_activity_time) >= threshold_seconds

def get_random_revive_message() -> str:
    return random.choice(REVIVE_MESSAGES)
