"""Tool registry with permissions, schemas, and rate limiting."""

import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class Permission(Enum):
    """Tool permission levels."""
    READ = "read"           # Read-only access
    WRITE = "write"         # File/data modification
    EXECUTE = "execute"     # Code execution
    NETWORK = "network"     # External API calls
    SENSITIVE = "sensitive" # Requires human approval


@dataclass
class ToolSchema:
    """Schema for a registered tool."""
    name: str
    description: str
    permissions: List[Permission]
    parameters: Dict[str, Any]  # JSON Schema style
    rate_limit: int = 10  # Max calls per minute
    requires_approval: bool = False


@dataclass
class ToolCall:
    """Record of a tool invocation."""
    tool_name: str
    input_data: Dict
    output_data: Any
    success: bool
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class ToolRegistry:
    """
    Registry for agent tools with permission checking and rate limiting.

    Tools must be registered before use. Each tool has:
    - A schema describing its inputs/outputs
    - Permission requirements
    - Rate limits
    - Optional approval requirements
    """

    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
        self._functions: Dict[str, Callable] = {}
        self._call_history: List[ToolCall] = []
        self._call_counts: Dict[str, List[float]] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        permissions: List[Permission],
        parameters: Dict[str, Any],
        rate_limit: int = 10,
        requires_approval: bool = False,
    ) -> None:
        """Register a tool."""
        schema = ToolSchema(
            name=name,
            description=description,
            permissions=permissions,
            parameters=parameters,
            rate_limit=rate_limit,
            requires_approval=requires_approval,
        )
        self._tools[name] = schema
        self._functions[name] = func
        self._call_counts[name] = []

    def check_permissions(self, tool_name: str, user_permissions: List[Permission]) -> bool:
        """Check if user has required permissions for a tool."""
        if tool_name not in self._tools:
            return False
        required = set(self._tools[tool_name].permissions)
        return required.issubset(set(user_permissions))

    def check_rate_limit(self, tool_name: str) -> bool:
        """Check if tool is within rate limit."""
        if tool_name not in self._tools:
            return False
        now = time.time()
        window = 60.0  # 1 minute window
        # Clean old calls
        self._call_counts[tool_name] = [
            t for t in self._call_counts[tool_name] if now - t < window
        ]
        return len(self._call_counts[tool_name]) < self._tools[tool_name].rate_limit

    def execute(self, tool_name: str, **kwargs) -> ToolCall:
        """Execute a tool with validation."""
        start = time.time()

        if tool_name not in self._tools:
            return ToolCall(
                tool_name=tool_name, input_data=kwargs,
      
