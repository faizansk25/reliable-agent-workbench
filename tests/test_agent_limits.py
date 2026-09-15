from agents import ScriptedPlanner
from core import Agent, PlanStep, StateManager, ToolRegistry, ToolSchema


def test_exact_maximum_steps_can_complete(tmp_path):
    registry = ToolRegistry()
    registry.register(
        ToolSchema("noop", "no operation", (), {"properties": {}}),
        lambda: None,
    )
    agent = Agent(
        registry,
        ScriptedPlanner([PlanStep("noop", {})]),
        state=StateManager(tmp_path),
        max_steps=1,
    )
    assert agent.run("one step").status == "completed"


def test_additional_step_exceeding_limit_fails(tmp_path):
    registry = ToolRegistry()
    registry.register(
        ToolSchema("noop", "no operation", (), {"properties": {}}),
        lambda: None,
    )
    agent = Agent(
        registry,
        ScriptedPlanner([PlanStep("noop", {}), PlanStep("noop", {})]),
        state=StateManager(tmp_path),
        max_steps=1,
    )
    outcome = agent.run("two steps")
    assert outcome.status == "failed"
    assert "maximum step count" in outcome.error
