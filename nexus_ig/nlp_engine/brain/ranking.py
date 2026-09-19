import time
from typing import Tuple
from ..memory.short_term import ChatMessage
from ..memory.group_memory import TopicState
from ..nlp.entities import ExtractedEntities


class ShouldIReplyEngine:
    """
    3-Tier Weighted Group Chat Relevance Scorer.
    Score < 30 -> SILENCE (Decision.SILENCE)
    30 - 60    -> MAYBE (Opportunistic reply)
    > 60       -> RESPOND
    """

    def __init__(self):
        self.last_reply_time = 0.0

    def evaluate(self, msg: ChatMessage, entities: ExtractedEntities, topic_state: TopicState) -> Tuple[bool, float, str]:
        """Evaluate message score using user's weighted point rules."""
        now = time.time()
        time_since_last = now - self.last_reply_time

        score = 0.0

        # Mentioned? (+40)
        if msg.is_bot_mentioned or any(kw in msg.text.lower() for kw in ["bot", "nexus", "oli", "chotu", "@bot", "@nexus"]):
            score += 40.0


        # Direct Question? (+30)
        if "?" in msg.text:
            score += 30.0

        # User asked bot / Quoted reply? (+30)
        if msg.replied_to_text:
            score += 30.0

        # Relevant topic? (+20)
        if entities.technologies or any(kw in msg.text.lower() for kw in ["flask", "python", "exam", "paper", "ml", "os"]):
            score += 20.0

        # Conversation active? (+10)
        if time_since_last < 30.0:
            score += 10.0

        # Bot just replied? (-40)
        if time_since_last < 4.0 and not msg.is_bot_mentioned and not msg.replied_to_text:
            score -= 40.0

        if score >= 60.0 or msg.is_bot_mentioned or msg.replied_to_text:
            self.last_reply_time = now
            return True, score, "RESPOND"
        elif score >= 30.0:
            self.last_reply_time = now
            return True, score, "MAYBE"
        else:
            return False, score, "SILENCE"
