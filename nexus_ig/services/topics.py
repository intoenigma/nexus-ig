"""Discussion topics generator."""
import random

TOPICS = [
    "Anime vs Real life: konsa best hai?",
    "Aapki favorite movie konsi hai?",
    "Agar aapko 1 Million Dollars mile toh kya karoge?",
    "Gaming ya Travelling: aapko kya pasand hai?",
    "Which is the best food you ever tried?"
]

def get_random_topic() -> str:
    return f"🗣️ CHAT TOPIC: {random.choice(TOPICS)}"
