import json

import pytest

from core import AgentState, StateManager


def test_state_machine_rejects_invalid_transition(tmp_path):
    state = StateManager(tmp_path)
    with pytest.raises(ValueError, match="invalid transition"):
        state.transition(AgentState.ACTING)


def test_checkpoint_round_trip_preserves_trace_and_context(tmp_path):
    state = StateManager(tmp_path)
    state.context["task"] = "demo"
    state.transition(AgentState.OBSERVING)
    state.transition(AgentState.PLANNING)
    path = state.checkpoint("after-plan")

    restored = StateManager.load_checkpoint(path)

    assert restored.state is AgentState.PLANNING
    assert restored.context == {"task": "demo"}
    assert restored.get_trace() == state.get_trace()
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1
