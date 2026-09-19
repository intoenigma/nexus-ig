import time
from collections import deque
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Incoming & Outgoing chat message data model."""

    message_id: str = Field(default_factory=lambda: str(int(time.time() * 1000)))
    thread_id: str = Field(default="global_thread")
    user_id: str = Field(default="user_default")
    user_name: str = Field(default="User")
    text: str = Field(..., min_length=1)
    timestamp: float = Field(default_factory=time.time)
    reply_to_user_id: Optional[str] = None
    replied_to_text: Optional[str] = None
    is_bot_mentioned: bool = False


class ShortTermMemory:
    """Ring buffer for recent message context & thread history."""

    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self.buffer: deque[ChatMessage] = deque(maxlen=capacity)

    def add(self, msg: ChatMessage):
        """Add message to ring buffer."""
        self.buffer.append(msg)

    def get_recent(self, count: int = 5) -> List[ChatMessage]:
        """Get last N messages."""
        return list(self.buffer)[-count:]
