"""Short-term and long-term memory for agents."""

from typing import Dict, List, Optional
from collections import deque
import json
from pathlib import Path


class ShortTermMemory:
    """Conversation buffer — remembers recent interactions."""

    def __init__(self, max_size: int = 20):
        self.buffer = deque(maxlen=max_size)

    def add(self, role: str, content: str) -> None:
        self.buffer.append({"role": role, "content": content})

    def get_context(self) -> List[Dict]:
        return list(self.buffer)

    def clear(self) -> None:
        self.buffer.clear()


class LongTermMemory:
    """Persistent memory — saves important facts to disk."""

    def __init__(self, path: str = "memory.json"):
        self.path = Path(path)
        self.facts: List[Dict] = []
        if self.path.exists():
            self.facts = json.loads(self.path.read_text())

    def store(self, fact: str, category: str = "general") -> None:
        self.facts.append({"fact": fact, "category": category})
        self.path.write_text(json.dumps(self.facts, indent=2))

    def recall(self, query: str, top_k: int = 5) -> List[Dict]:
        query_lower = query.lower()
        scored = [(f, sum(1 for w in query_lower.split() if w in f["fact"].lower())) for f in self.facts]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [f for f, s in scored[:top_k] if s > 0]
