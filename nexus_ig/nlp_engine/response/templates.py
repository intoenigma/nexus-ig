import random


class ResponseTemplates:
    """Rich natural casual Hinglish templates for all intents."""

    GREETINGS = [
        "Hey @{user_name}! Kya chal raha hai?",
        "Aur @{user_name}, kya haal chaal?",
        "Wassup @{user_name}! Sab badhiya?",
        "Aao aao @{user_name}, kya baat ho rahi hai?",
    ]

    STATUS_REPLIES = [
        "Bas ekdam mast @{user_name}! Aap batao kya chal raha hai?",
        "Sabb badhiya bhai! Group chat pe chill scene hai. Tu bata?",
        "Bas mast chal raha hai! Tu suna @{user_name}, kya plan hai?",
    ]

    FALLBACKS = [
        "Sahi baat hai @{user_name}! 👌",
        "Haan bilkul, sahi bol rahe ho!",
        "Achaa aisa? Badhiya hai!",
        "Haha sahi hai! 😂",
        "Haan bhai, bilkul!",
    ]

    @classmethod
    def get_greeting(cls, user_name: str) -> str:
        return random.choice(cls.GREETINGS).format(user_name=user_name)

    @classmethod
    def get_status(cls, user_name: str) -> str:
        return random.choice(cls.STATUS_REPLIES).format(user_name=user_name)

    @classmethod
    def get_fallback(cls, user_name: str) -> str:
        return random.choice(cls.FALLBACKS).format(user_name=user_name)
