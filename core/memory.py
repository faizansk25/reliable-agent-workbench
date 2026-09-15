"""Bounded conversation memory and atomic local fact storage."""

from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path


class ShortTermMemory:
    def __init__(self, max_size: int = 20) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._buffer: deque[dict[str, str]] = deque(maxlen=max_size)

    def add(self, role: str, content: str) -> None:
        if not role.strip() or not content.strip():
            raise ValueError("role and content must not be empty")
        self._buffer.append({"role": role, "content": content})

    def get_context(self) -> list[dict[str, str]]:
        return list(self._buffer)

    def clear(self) -> None:
        self._buffer.clear()


class LongTermMemory:
    SCHEMA_VERSION = 1

    def __init__(self, path: str | Path = "memory.json") -> None:
        self.path = Path(path)
        self.facts: list[dict[str, str]] = []
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != self.SCHEMA_VERSION:
                raise ValueError("unsupported memory schema_version")
            facts = payload.get("facts")
            if not isinstance(facts, list):
                raise ValueError("memory facts must be a list")
            self.facts = facts

    def store(self, fact: str, category: str = "general") -> None:
        if not fact.strip() or not category.strip():
            raise ValueError("fact and category must not be empty")
        item = {"fact": fact.strip(), "category": category.strip()}
        if item not in self.facts:
            self.facts.append(item)
            self._save()

    def recall(self, query: str, top_k: int = 5) -> list[dict[str, str]]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        ranked = []
        for position, fact in enumerate(self.facts):
            haystack = set(re.findall(r"[a-z0-9]+", fact["fact"].lower()))
            score = len(terms & haystack)
            if score:
                ranked.append((score, -position, fact))
        ranked.sort(reverse=True)
        return [fact for _, _, fact in ranked[:top_k]]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": self.SCHEMA_VERSION, "facts": self.facts}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.path)
