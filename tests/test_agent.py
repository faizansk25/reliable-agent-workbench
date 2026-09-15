from agents import ScriptedPlanner
from core import Agent, AgentState, Permission, PlanStep, StateManager, ToolRegistry, ToolSchema


def register_echo(requires_approval=False):
    registry = ToolRegistry()
    registry.register(
        ToolSchema(
            name="echo",
            description="echo",
            permissions=(Permission.READ,),
            parameters={
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
            requires_approval=requires_approval,
        ),
        lambda text: text.upper(),
    )
    return registry


def test_agent_executes_and_completes_with_audit_trace(tmp_path):
    registry = register_echo()
    planner = ScriptedPlanner([PlanStep("echo", {"text": "safe"})])
    agent = Agent(
        registry,
        planner,
        permissions=(Permission.READ,),
        state=StateManager(tmp_path),
    )

    outcome = agent.run("echo safely")

    assert outcome.status == "completed"
    assert agent.state.state is AgentState.COMPLETED
    assert registry.history[0].output_data == "SAFE"
    assert any(event["event"] == "tool_call" for event in outcome.trace)


def test_approval_checkpoint_can_be_loaded_and_resumed(tmp_path):
    registry = register_echo(requires_approval=True)
    planner = ScriptedPlanner([PlanStep("echo", {"text": "sensitive"})])
    first_agent = Agent(
        registry,
        planner,
        permissions=(Permission.READ,),
        state=StateManager(tmp_path),
    )

    waiting = first_agent.run("approval demo")
    restored = StateManager.load_checkpoint(waiting.checkpoint)
    resumed_agent = Agent(
        registry,
        planner,
        permissions=(Permission.READ,),
        state=restored,
    )
    completed = resumed_agent.resume(approved=True)

    assert waiting.status == "waiting_approval"
    assert completed.status == "completed"
    assert registry.history[-1].success


def test_denied_approval_fails_without_calling_tool(tmp_path):
    registry = register_echo(requires_approval=True)
    planner = ScriptedPlanner([PlanStep("echo", {"text": "sensitive"})])
    agent = Agent(
        registry,
        planner,
        permissions=(Permission.READ,),
        state=StateManager(tmp_path),
    )
    agent.run("approval demo")

    outcome = agent.resume(approved=False)

    assert outcome.status == "failed"
    assert registry.history == []
