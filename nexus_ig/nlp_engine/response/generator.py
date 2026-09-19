from typing import List, Optional, Tuple
from ..memory.short_term import ChatMessage
from ..nlp.entities import ExtractedEntities
from .templates import ResponseTemplates
from .humor import HumorEngine


class ResponseGenerator:
    """Assembles final response, handles quoted Instagram replies & casual natural Hinglish templates."""

    def __init__(self, humor: HumorEngine):
        self.humor = humor

    def generate(
        self,
        message: ChatMessage,
        intent: str,
        entities: ExtractedEntities,
        history: List[ChatMessage],
    ) -> Tuple[str, str]:
        """Generate response text and source module tag."""
        lower_raw = message.text.lower().strip()

        # A. Instagram Replied-To Message Handling (Quoted Reply)
        if message.replied_to_text:
            if "kaisi ho" in lower_raw or "kaisa hai" in lower_raw or "kaise ho" in lower_raw:
                return f"Bas ekdam mast @{message.user_name}! Aap batao kya chal raha hai?", "quoted_reply"
            elif "kya kar" in lower_raw or "kya kr" in lower_raw:
                return f"Bas group chat mein baatein sun raha hu! 😂 Tu bata @{message.user_name}?", "quoted_reply"
            elif "sahi" in lower_raw or "bilkul" in lower_raw or "agree" in lower_raw:
                return f"Haan na @{message.user_name}! Ekdam sahi bola tune!", "quoted_reply"
            elif "kyun" in lower_raw or "kyu" in lower_raw or "why" in lower_raw:
                return f"Arey @{message.user_name}, simple si baat hai! Baaki tu kya bolta hai?", "quoted_reply"
            elif "haha" in lower_raw or "lol" in lower_raw or "lmao" in lower_raw:
                return "Haha sahi hai! 😂", "quoted_reply"
            else:
                return f"Achaa! '{message.replied_to_text[:30]}' ke baare mein baat ho rahi hai? Haan bilkul sahi @{message.user_name}!", "quoted_reply"

        # B. Intent: Greeting
        if intent == "greeting" or any(w in lower_raw for w in ["hi", "hello", "hey", "sup", "namaste", "wassup"]):
            return ResponseTemplates.get_greeting(message.user_name), "greeting"

        # C. Casual Status Questions ("kaisi ho", "kaisa hai", "kya chal raha hai", "kya kar rahe ho")
        if any(phrase in lower_raw for phrase in ["kaisi ho", "kaisa hai", "kaise ho", "kaise ho?", "kya chal raha", "kya kr rahe", "kya kar rahe"]):
            return ResponseTemplates.get_status(message.user_name), "status_chat"

        # D. Intent: Exam / Study
        if intent == "exam_study" or any(w in lower_raw for w in ["exam", "ppr", "padhai", "syllabus"]):
            return f"Padhai kar lo guys! Best of luck @{message.user_name}, paper phodna hai! 💪", "study_assistant"

        # E. Intent: Joke
        if intent == "joke" or any(w in lower_raw for w in ["joke", "jokes", "funny", "lmao", "lol"]):
            return self.humor.get_joke(), "humor_engine"

        # F. Fallback: Natural Conversational Response
        if "?" in message.text:
            return f"Achaa sawal hai @{message.user_name}! Waise tu is baare mein kya sochta hai?", "natural_question"

        return ResponseTemplates.get_fallback(message.user_name), "natural_conversation"
