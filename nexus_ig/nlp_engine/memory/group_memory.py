import time
from dataclasses import dataclass, field, asdict
from typing import List, Set
from .long_term import LongTermMemory


@dataclass
class TopicState:
    """Group topic tracking model."""

    current_topic: str = "general"
    previous_topic: str = "general"
    topic_stack: List[str] = field(default_factory=lambda: ["general"])
    participants: Set[str] = field(default_factory=set)
    last_updated: float = field(default_factory=time.time)

    def model_dump(self):
        d = asdict(self)
        d["participants"] = list(self.participants)
        return d


class GroupMemoryManager:
    """Manages group-wide conversation context, active topic stack, and slang vocabulary."""

    def __init__(self, long_term: LongTermMemory):
        self.long_term = long_term
        self.topic_state = TopicState()

    def update_topic(self, new_topic: str, user_name: str):
        """Update active topic state if topic shifted."""
        if new_topic and new_topic != self.topic_state.current_topic:
            self.topic_state.previous_topic = self.topic_state.current_topic
            self.topic_state.current_topic = new_topic
            self.topic_state.topic_stack.append(new_topic)
            if len(self.topic_state.topic_stack) > 10:
                self.topic_state.topic_stack.pop(0)

        self.topic_state.participants.add(user_name)
        self.topic_state.last_updated = time.time()
        self.long_term.set("group_topic_state", self.topic_state.model_dump())

