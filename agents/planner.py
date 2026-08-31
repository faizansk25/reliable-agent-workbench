"""Planner agent — decomposes tasks into sub-tasks."""

from typing import List, Dict


class PlannerAgent:
    """Decomposes complex tasks into manageable sub-tasks."""

    def __init__(self, llm=None):
        self.llm = llm

    def decompose(self, task: str) -> List[Dict]:
        """Break task into sub-tasks."""
        return [{"id": i, "description": f"Step {i+1}: {part.strip()}"} for i, part in enumerate(task.split(".")) if part.strip()]
