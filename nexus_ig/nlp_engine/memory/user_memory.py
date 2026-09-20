import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
from .long_term import LongTermMemory


@dataclass
class UserProfile:
    """User personality & long-term memory model."""

    user_id: str
    user_name: str
    nickname: Optional[str] = None
    avg_msg_length: float = 0.0
    total_messages: int = 0
    question_count: int = 0
    emoji_count: int = 0
    favorite_topics: Dict[str, int] = field(default_factory=dict)
    known_facts: Dict[str, str] = field(default_factory=dict)
    communication_style: str = "casual"  # casual, technical, brief, verbose
    last_seen: float = field(default_factory=time.time)

    def model_dump(self):
        return asdict(self)


class UserMemoryManager:
    """Manages user profiles and personality tracking."""

    def __init__(self, long_term: LongTermMemory):
        self.long_term = long_term

    def get_profile(self, user_id: str, user_name: str) -> UserProfile:
        """Fetch user profile or return new default profile."""
        key = f"user_profile:{user_id}"
        data = self.long_term.get(key)
        if data:
            try:
                return UserProfile(**data)
            except Exception:
                pass
        return UserProfile(user_id=user_id, user_name=user_name)

    def save_profile(self, profile: UserProfile):
        """Save user profile to persistent long-term memory."""
        key = f"user_profile:{profile.user_id}"
        profile.last_seen = time.time()
        self.long_term.set(key, profile.model_dump())

