import random
from typing import List, Optional, Tuple
from ..memory.short_term import ChatMessage
from ..nlp.entities import ExtractedEntities
from .templates import ResponseTemplates
from .humor import HumorEngine


class ResponseGenerator:
    """Assembles final response dynamically from user input, choices, quoted replies, or group knowledge."""

    def __init__(self, humor: HumorEngine):
        self.humor = humor

    def generate(
        self,
        message: ChatMessage,
        intent: str,
        entities: ExtractedEntities,
        history: List[ChatMessage],
    ) -> Tuple[str, str]:
        """Generate dynamic natural Hinglish response without echoing raw text verbatim."""
        lower_raw = message.text.lower().strip()

        # A. Instagram Replied-To Message Handling (Quoted Reply)
        if message.replied_to_text:
            return f"Achaa! '{message.replied_to_text[:40]}' ke baare mein baat ho rahi hai? @{message.user_name}", "quoted_reply"

        # B. Choice Decisions ("X ya Y" or "X or Y")
        if " ya " in lower_raw or " or " in lower_raw:
            parts = lower_raw.split(" ya ") if " ya " in lower_raw else lower_raw.split(" or ")
            if len(parts) >= 2:
                choice = parts[0].strip() if random.random() > 0.5 else parts[1].strip()
                return f"Mujhe lagta hai '{choice}' ziada sahi hai! 🎯 @{message.user_name}", "choice_decision"

        # C. Intent: Joke
        if intent == "joke" or any(w in lower_raw for w in ["joke", "jokes"]):
            return self.humor.get_joke(), "humor_engine"

        # D. Greetings ("hi", "hello", "hey", "wassup")
        if any(w in lower_raw for w in ["hi", "hello", "hey", "wassup", "namaste"]):
            return f"Hey @{message.user_name}! Kya haal chaal?", "greeting"

        # E. How are you / Status Questions
        if any(phrase in lower_raw for phrase in ["how are you", "kaisa hai", "kaise ho", "kya haal"]):
            return f"Bas ekdam mast @{message.user_name}! Aap batao kya chal raha hai?", "status_chat"

        # F. Sleeping / Activity Questions
        if any(phrase in lower_raw for phrase in ["so giya", "so gaya", "so gyi", "kya kar"]):
            return f"Nahi so raha hu @{message.user_name}, group chat hi dekh raha hu! 😂", "activity_chat"

        # G. Curiosity Questions ("why", "kyun", "kyu")
        if any(w in lower_raw for w in ["why", "kyun", "kyu"]):
            return f"Arey @{message.user_name}, simple si baat hai! Baaki aap kya bolte ho?", "curiosity_chat"

        # H. Natural Dynamic Fallback
        return f"Achaa! Sahi baat hai @{message.user_name}, baaki group waale kya bolte hain?", "dynamic_conversation"


