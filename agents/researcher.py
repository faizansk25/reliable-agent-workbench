"""A local research workflow assembled from explicit, injected tools."""

from __future__ import annotations

from core.agent import PlanStep

from .planner import ScriptedPlanner


def build_research_planner(query: str) -> ScriptedPlanner:
    """Create a one-step planner; callers decide which search provider is registered."""
    if not query.strip():
        raise ValueError("query must not be empty")
    return ScriptedPlanner(
        [PlanStep(tool="search", arguments={"query": query}, rationale="collect sources")]
    )
