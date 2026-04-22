"""
Session — Manages conversation history with a model.
"""

import time
import uuid
from typing import Optional


class Session:
    """A conversation session with an agent."""

    def __init__(self, session_id: str = None):
        self.id = session_id or uuid.uuid4().hex[:12]
        self.history: list = []
        self.created_at: float = time.time()
        self.tokens_used: int = 0

    def add(self, role: str, content: str):
        """Add a message to the conversation."""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })

    def get_messages(self) -> list:
        """Get messages in API format (role, content only)."""
        return [{"role": m["role"], "content": m["content"]} for m in self.history]

    def last_response(self) -> str:
        """Get the last assistant response."""
        for msg in reversed(self.history):
            if msg["role"] == "assistant":
                return msg["content"]
        return ""

    def clear(self):
        """Clear conversation history."""
        self.history = []

    def info(self) -> dict:
        return {
            "id": self.id,
            "messages": len(self.history),
            "tokens_used": self.tokens_used,
            "created_at": self.created_at,
        }
