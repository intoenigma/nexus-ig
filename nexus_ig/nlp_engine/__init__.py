"""
Modular 18-Feature Traditional NLP Group Chat Engine Package.
Structured cleanly across brain, nlp, memory, knowledge, learning, and response subpackages.
"""

from .bot import StrictNLPBot, BotResponse
from .memory import ChatMessage, UserProfile, TopicState
from .knowledge import KnowledgeFact

__all__ = [
    "StrictNLPBot",
    "BotResponse",
    "ChatMessage",
    "UserProfile",
    "TopicState",
    "KnowledgeFact",
]
