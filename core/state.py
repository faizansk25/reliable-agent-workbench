"""Validated agent state transitions and durable JSON checkpoints."""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AgentState(str, Enum):
    IDLE = "idle"
    OBSERVING = "observing"
    PLANNING = "planning"
    WAITING_APPROVAL = "waiting_approval"
    ACTING = "acting"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


TRANSITIONS: dict[AgentState, frozenset[AgentState]] = {
    AgentState.IDLE: frozenset({AgentState.OBSERVING}),
    AgentState.OBSERVING: frozenset({AgentState.PLANNING}),
    AgentState.PLANNING: frozenset(
        {AgentState.ACTING, AgentState.VERIFYING, AgentState.WAITING_APPROVAL, AgentState.FAILED}
    ),
    AgentState.WAITING_APPROVAL: frozenset({AgentState.ACTING, AgentState.FAILED}),
    AgentState.ACTING: frozenset({AgentState.VERIFYING, AgentState.FAILED}),
    AgentState.VERIFYING: frozenset(
        {AgentState.OBSERVING, AgentState.COMPLETED, AgentState.FAILED}
    ),
    AgentState.COMPLETED: frozenset({AgentState.IDLE}),
    AgentState.FAILED: frozenset({AgentState.IDLE, AgentState.OBSERVING}),
}


@dataclass(frozen=True)
class TraceEvent:
    sequence: int
    event: str
    state: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class StateManager:
    """Own state, context, audit events, and atomic checkpoints."""

    SCHEMA_VERSION = 1

    def __init__(self, checkpoint_dir: str | Path = "checkpoints") -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.state = AgentState.IDLE
        self.context: dict[str, Any] = {}
        self.trace: list[TraceEvent] = []

    def transition(self, new_state: AgentState, **details: Any) -> None:
        if new_state not in TRANSITIONS[self.state]:
            allowed = ", ".join(sorted(state.value for state in TRANSITIONS[self.state]))
            raise ValueError(
                f"invalid transition {self.state.value!r} -> {new_state.value!r}; "
                f"allowed: {allowed or 'none'}"
            )
        previous = self.state
        self.state = new_state
        self.record("transition", previous=previous.value, current=new_state.value, **details)

    def record(self, event: str, **details: Any) -> TraceEvent:
        if not event.strip():
            raise ValueError("event must not be empty")
        item = TraceEvent(
            sequence=len(self.trace) + 1,
            event=event,
            state=self.state.value,
            details=details,
        )
        self.trace.append(item)
        return item

    def checkpoint(self, name: str = "latest") -> Path:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-.")
        if not safe_name:
            raise ValueError("checkpoint name must contain a safe character")
        path = self.checkpoint_dir / f"{safe_name}.json"
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "state": self.state.value,
            "context": self.context,
            "trace": [asdict(item) for item in self.trace],
        }
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(path)
        return path

    @classmethod
    def load_checkpoint(cls, path: str | Path) -> "StateManager":
        source = Path(path)
        payload = json.loads(source.read_text(encoding="utf-8"))
        if payload.get("schema_version") != cls.SCHEMA_VERSION:
            raise ValueError("unsupported or missing checkpoint schema_version")
        manager = cls(source.parent)
        manager.state = AgentState(payload["state"])
        context = payload.get("context", {})
        trace = payload.get("trace", [])
        if not isinstance(context, dict) or not isinstance(trace, list):
            raise ValueError("checkpoint context or trace has an invalid type")
        manager.context = context
        manager.trace = [TraceEvent(**item) for item in trace]
        return manager

    def get_trace(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.trace]
