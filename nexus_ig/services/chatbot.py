"""
Nexus IG 18-Feature Advanced Traditional NLP Group Chat Intelligence Engine.
Delegates directly to modular subpackages inside nexus_ig.nlp_engine (brain, nlp, memory, knowledge, learning, response).
"""


from ..nlp_engine import StrictNLPBot, ChatMessage, BotResponse, UserProfile, TopicState, KnowledgeFact

__all__ = [
    "StrictNLPBot",
    "ChatMessage",
    "BotResponse",
    "UserProfile",
    "TopicState",
    "KnowledgeFact",
]
