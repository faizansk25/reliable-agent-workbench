"""Agent state machine with explicit transitions and checkpointing."""

import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


class AgentState(Enum):
    """Possible states for the agent loop."""
    IDLE = "idle"
    OBSERVING = "observing"
    PLANNING = "planning"
    ACTING = "acting"
    VERIFYING = "verifying"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    COMPLETED = "completed"


# Valid state transitions
TRANSITIONS = {
    AgentState.IDLE: [AgentState.OBSERVING],
    AgentState.OBSERVING: [AgentState.PLANNING, AgentState.ERROR],
    AgentState.PLANNING: [AgentState.ACTING, AgentState.WAITING_APPROVAL],
    AgentState.ACTING: [AgentState.VERIFYING, AgentState.ERROR],
    AgentState.VERIFYING: [AgentState.OBSERVING, AgentState.COMPLETED, AgentState.ERROR],
    AgentState.WAITING_APPROVAL: [AgentState.ACTING, AgentState.ERROR],
    AgentState.ERROR: [AgentState.OBSERVING, AgentState.IDLE],
    AgentState.COMPLETED: [AgentState.IDLE],
}


@dataclass
class StepRecord:
    """Record of a single agent step."""
    step_id: int
    state: str
    action: str
    tool: Optional[str] = None
    input_data: Optional[Dict] = None
    output_data: Optional[Dict] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None


class StateManager:
    """
    Manages agent state with explicit transitions and checkpointing.

    Every transition is validated and logged. State can be saved to disk
    and restored, enabling crash recovery and failure replay.
    """

    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.state = AgentState.IDLE
        self.steps: List[StepRecord] = []
        self.context: Dict[str, Any] = {}
        self.step_counter = 0
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

    def transition(self, new_state: AgentState) -> None:
        """Validate and execute state transition."""
        valid = TRANSITIONS.get(self.state, [])
        if new_state not in valid:
            raise ValueError(
                f"Invalid transition: {self.state.value} → {new_state.value}. "
                f"Valid transitions: {[s.value for s in valid]}"
            )
        old_state = self.state
        self.state = new_state
        self._log(f"State: {old_state.value} → {new_state.value}")

    def record_step(
        self,
        action: str,
        tool: Optional[str] = None,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        error: Optional[str] = None,
    ) -> StepRecord:
        """Record an agent step."""
        self.step_counter += 1
        step = StepRecord(
            step_id=self.step_counter,
            state=self.state.value,
            action=action,
            tool=tool,
            input_data=input_data,
            output_data=output_data,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            error=error,
        )
        self.steps.append(step)
        return step

    def checkpoint(self, name: Optional[str] = None) -> str:
        """Save current state to disk."""
        name = name or f"step_{self.step_counter}"
        path = self.checkpoint_dir / f"{name}.json"
        data = {
            "state": self.state.value,
            "step_counter": self.step_counter,
            "context": self.context,
            "steps": [asdict(s) for s in self.steps],
        }
        path.write_text(json.dumps(data, indent=2))
        self._log(f"Checkpoint saved: {path}")
        return str(path)

    @classmethod
    def load_checkpoint(cls, path: str) -> "StateManager":
        """Restore state from checkpoint."""
        data = json.loads(Path(path).read_text())
        mgr = cls()
        mgr.state = AgentState(data["state"])
        mgr.step_counter = data["step_counter"]
        mgr.context = data["context"]
        mgr.steps = [StepRecord(**s) for s in data["steps"]]
        mgr._log(f"Loaded checkpoint: {path}")
        return mgr

    def get_trace(self) -> List[Dict]:
        """Get execution trace for debugging."""
        return [asdict(s) for s in self.steps]

    def get_total_cost(self) -> float:
        """Get total cost across all steps."""
        return sum(s.cost_usd for s in self.steps)

    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return sum(s.tokens_used for s in self.steps)

    def _log(self, msg: str) -> None:
        print(f"[StateManager] {msg}")
