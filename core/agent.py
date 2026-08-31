"""Main agent loop with observe -> decide -> act -> verify cycle."""

from typing import Any, Dict, List, Optional
from .state import StateManager, AgentState
from .tools import ToolRegistry, Permission


class Agent:
    """Production-grade AI agent with durable execution."""

    def __init__(self, tool_registry: ToolRegistry, user_permissions: Optional[List[Permission]] = None, max_steps: int = 50):
        self.tools = tool_registry
        self.permissions = user_permissions or [Permission.READ]
        self.max_steps = max_steps
        self.state = StateManager()

    def run(self, task: str) -> Dict[str, Any]:
        """Execute a task through the agent loop."""
        self.state.context["task"] = task
        self.state.transition(AgentState.OBSERVING)
        for step in range(self.max_steps):
            observation = self._observe()
            self.state.transition(AgentState.PLANNING)
            plan = self._plan(observation)
            if plan.get("completed"):
                self.state.transition(AgentState.VERIFYING)
                self.state.transition(AgentState.COMPLETED)
                return {"success": True, "task": task, "steps": self.state.step_counter, "trace": self.state.get_trace()}
            self.state.transition(AgentState.ACTING)
            result = self._act(plan)
            self.state.transition(AgentState.VERIFYING)
        self.state.transition(AgentState.COMPLETED)
        return {"success": False, "task": task, "steps": self.state.step_counter, "trace": self.state.get_trace()}

    def _observe(self) -> Dict:
        return {"task": self.state.context.get("task", ""), "step": self.state.step_counter, "history": self.state.get_trace()[-5:]}

    def _plan(self, observation: Dict) -> Dict:
        return {"action": "think", "tool": None, "input": {}, "completed": False}

    def _act(self, plan: Dict) -> Dict:
        tool_name = plan.get("tool")
        if tool_name:
            call = self.tools.execute(tool_name, **plan.get("input", {}))
            self.state.record_step(action=f"tool_call:{tool_name}", tool=tool_name, input_data=plan.get("input"), output_data={"success": call.success})
            return {"success": call.success}
        return {"success": True}
