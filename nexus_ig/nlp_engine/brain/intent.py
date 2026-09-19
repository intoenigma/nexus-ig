from typing import Tuple
from rapidfuzz import process, fuzz


class IntentEngine:
    """Multi-Category Intent Classifier using rapidfuzz."""

    INTENT_PATTERNS = {
        "greeting": ["hello", "hi", "hey", "greetings", "good morning", "good evening", "howdy", "sup", "namaste"],
        "farewell": ["bye", "goodbye", "see you later", "exit", "quit", "cya", "tata"],
        "question": ["what", "why", "how", "when", "where", "who", "which", "konsa", "kaunsa", "kab", "kyun", "?"],
        "exam_study": ["exam", "paper", "ppr", "study", "syllabus", "marks", "test", "result", "padhai"],
        "coding_tech": ["python", "flask", "code", "programming", "developer", "bug", "error", "function", "api"],
        "plans_meetup": ["meetup", "plan", "milte hai", "chaloge", "bikaner", "goa", "trip", "party"],
        "joke": ["joke", "jokes", "funny", "lmao", "lol", "hahaha", "laugh"],
        "help": ["help", "commands", "menu", "what can you do", "bot info"],
    }

    def detect(self, text: str) -> Tuple[str, float]:
        """Detect intent and confidence score using rapidfuzz."""
        text_lower = text.lower()
        best_intent = "general_chat"
        best_score = 0.0

        if "?" in text or any(text_lower.startswith(q) for q in ["what", "why", "how", "when", "where", "who", "konsa", "kab"]):
            best_intent = "question"
            best_score = 0.85

        for intent, patterns in self.INTENT_PATTERNS.items():
            res = process.extractOne(text_lower, patterns, scorer=fuzz.token_sort_ratio)
            if res:
                match_pattern, score, idx = res
                norm_score = round(score / 100.0, 2)
                if norm_score > best_score:
                    best_score = norm_score
                    best_intent = intent

        return best_intent, best_score
