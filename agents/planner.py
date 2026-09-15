"""Deterministic planner implementations for tests and local workflows."""

from __future__ import annotations

from collections.abc import Sequence

from core.agent import PlanStep


class ScriptedPlanner:
    """Replay a declared tool plan; progress is derived from the durable audit trace."""

    def __init__(self, steps: Sequence[PlanStep]) -> None:
        self.steps = tuple(steps)

    def __call__(self, task: str, trace: list[dict]) -> PlanStep | None:
        del task
        completed = sum(item["event"] == "tool_call" for item in trace)
        return self.steps[completed] if completed < len(self.steps) else None
