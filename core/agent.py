"""A deterministic agent loop with permission and approval boundaries."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from .state import AgentState, StateManager
from .tools import Permission, ToolCall, ToolRegistry


@dataclass(frozen=True)
class PlanStep:
    tool: str
    arguments: Mapping[str, Any]
    rationale: str = ""


@dataclass(frozen=True)
class AgentOutcome:
    status: str
    task: str
    trace: list[dict[str, Any]]
    checkpoint: str
    error: str | None = None


Planner = Callable[[str, list[dict[str, Any]]], PlanStep | None]
Verifier = Callable[[PlanStep, ToolCall], bool]


class Agent:
    """Execute planner steps with auditable controls and resumable approvals."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        planner: Planner,
        permissions: Sequence[Permission] = (Permission.READ,),
        *,
        verifier: Verifier | None = None,
        state: StateManager | None = None,
        max_steps: int = 20,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self.tools = tool_registry
        self.planner = planner
        self.permissions = tuple(permissions)
        self.verifier = verifier or (lambda step, call: call.success)
        self.state = state or StateManager()
        self.max_steps = max_steps

    def run(self, task: str) -> AgentOutcome:
        if self.state.state is not AgentState.IDLE:
            raise RuntimeError("run requires an idle agent; use resume for a checkpointed agent")
        if not task.strip():
            raise ValueError("task must not be empty")
        self.state.context = {"task": task, "completed_steps": 0}
        self.state.transition(AgentState.OBSERVING)
        return self._loop(task)

    def resume(self, approved: bool) -> AgentOutcome:
        if self.state.state is not AgentState.WAITING_APPROVAL:
            raise RuntimeError("resume requires a waiting_approval checkpoint")
        task = str(self.state.context["task"])
        raw_step = self.state.context.get("pending_step")
        if not isinstance(raw_step, dict):
            return self._fail(task, "checkpoint has no valid pending step")
        step = PlanStep(
            tool=str(raw_step["tool"]),
            arguments=dict(raw_step["arguments"]),
            rationale=str(raw_step.get("rationale", "")),
        )
        if not approved:
            return self._fail(task, "human approval denied")
        self.state.transition(AgentState.ACTING, approval="granted", tool=step.tool)
        outcome = self._execute_step(task, step, approved=True)
        if outcome:
            return outcome
        self.state.context.pop("pending_step", None)
        self.state.transition(AgentState.OBSERVING)
        return self._loop(task)

    def _loop(self, task: str) -> AgentOutcome:
        completed = int(self.state.context.get("completed_steps", 0))
        while completed < self.max_steps:
            step = self.planner(task, self.state.get_trace())
            self.state.transition(AgentState.PLANNING)
            if step is None:
                self.state.transition(AgentState.VERIFYING, reason="planner_finished")
                self.state.transition(AgentState.COMPLETED)
                return self._outcome(task, "completed")
            schema = self.tools.schema(step.tool)
            if schema.requires_approval:
                self.state.context["pending_step"] = {
                    "tool": step.tool,
                    "arguments": dict(step.arguments),
                    "rationale": step.rationale,
                }
                self.state.transition(AgentState.WAITING_APPROVAL, tool=step.tool)
                return self._outcome(task, "waiting_approval")
            self.state.transition(AgentState.ACTING, tool=step.tool)
            outcome = self._execute_step(task, step, approved=False)
            if outcome:
                return outcome
            completed = int(self.state.context["completed_steps"])
            if completed >= self.max_steps:
                if self.planner(task, self.state.get_trace()) is None:
                    self.state.transition(AgentState.COMPLETED)
                    return self._outcome(task, "completed")
                return self._fail(task, f"maximum step count ({self.max_steps}) reached")
            self.state.transition(AgentState.OBSERVING)
        return self._fail(task, "agent stopped unexpectedly")

    def _execute_step(
        self, task: str, step: PlanStep, *, approved: bool
    ) -> AgentOutcome | None:
        call = self.tools.execute(
            step.tool,
            step.arguments,
            self.permissions,
            approved=approved,
        )
        self.state.record("tool_call", plan=asdict(step), call=call.to_dict())
        if not call.success:
            return self._fail(task, call.error or "tool call failed")
        self.state.transition(AgentState.VERIFYING, tool=step.tool)
        if not self.verifier(step, call):
            return self._fail(task, "verification failed")
        self.state.context["completed_steps"] = int(
            self.state.context.get("completed_steps", 0)
        ) + 1
        self.state.checkpoint("latest")
        return None

    def _fail(self, task: str, error: str) -> AgentOutcome:
        self.state.transition(AgentState.FAILED, error=error)
        return self._outcome(task, "failed", error)

    def _outcome(self, task: str, status: str, error: str | None = None) -> AgentOutcome:
        checkpoint = self.state.checkpoint("latest")
        return AgentOutcome(
            status=status,
            task=task,
            trace=self.state.get_trace(),
            checkpoint=str(checkpoint),
            error=error,
        )
