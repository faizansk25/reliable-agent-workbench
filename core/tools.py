"""Tool registry with explicit permissions, approval gates, and rate limits."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    SENSITIVE = "sensitive"


@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    permissions: tuple[Permission, ...]
    parameters: Mapping[str, Any]
    rate_limit: int = 10
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("tool name must not be empty")
        if self.rate_limit < 1:
            raise ValueError("rate_limit must be at least 1")


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    input_data: dict[str, Any]
    output_data: Any = None
    success: bool = False
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ToolRegistry:
    """Register callables and enforce controls before invocation."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._schemas: dict[str, ToolSchema] = {}
        self._functions: dict[str, Callable[..., Any]] = {}
        self._calls: dict[str, list[float]] = {}
        self.history: list[ToolCall] = []

    def register(self, schema: ToolSchema, function: Callable[..., Any]) -> None:
        if schema.name in self._schemas:
            raise ValueError(f"tool {schema.name!r} is already registered")
        self._schemas[schema.name] = schema
        self._functions[schema.name] = function
        self._calls[schema.name] = []

    def schema(self, name: str) -> ToolSchema:
        try:
            return self._schemas[name]
        except KeyError as error:
            raise KeyError(f"unknown tool: {name}") from error

    def execute(
        self,
        name: str,
        arguments: Mapping[str, Any],
        granted_permissions: Sequence[Permission],
        *,
        approved: bool = False,
    ) -> ToolCall:
        started = time.perf_counter()
        try:
            schema = self.schema(name)
            self._authorize(schema, granted_permissions, approved)
            self._validate_arguments(schema.parameters, arguments)
            self._consume_rate_limit(schema)
            output = self._functions[name](**dict(arguments))
            call = ToolCall(
                tool_name=name,
                input_data=dict(arguments),
                output_data=output,
                success=True,
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as error:  # A tool boundary converts failures into inspectable results.
            call = ToolCall(
                tool_name=name,
                input_data=dict(arguments),
                error=f"{type(error).__name__}: {error}",
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        self.history.append(call)
        return call

    @staticmethod
    def _authorize(
        schema: ToolSchema, granted_permissions: Sequence[Permission], approved: bool
    ) -> None:
        missing = set(schema.permissions) - set(granted_permissions)
        if missing:
            names = ", ".join(sorted(item.value for item in missing))
            raise PermissionError(f"missing permissions: {names}")
        if schema.requires_approval and not approved:
            raise PermissionError("explicit approval required")

    @staticmethod
    def _validate_arguments(schema: Mapping[str, Any], arguments: Mapping[str, Any]) -> None:
        if not isinstance(arguments, Mapping):
            raise TypeError("tool arguments must be an object")
        required = schema.get("required", [])
        missing = [name for name in required if name not in arguments]
        if missing:
            raise ValueError(f"missing required arguments: {', '.join(missing)}")
        properties = schema.get("properties", {})
        extra = set(arguments) - set(properties)
        if schema.get("additionalProperties") is False and extra:
            raise ValueError(f"unexpected arguments: {', '.join(sorted(extra))}")
        type_map = {"string": str, "integer": int, "number": (int, float), "boolean": bool}
        for name, value in arguments.items():
            expected_name = properties.get(name, {}).get("type")
            expected = type_map.get(expected_name)
            if expected and (isinstance(value, bool) and expected_name in {"integer", "number"}):
                raise TypeError(f"argument {name!r} must be {expected_name}")
            if expected and not isinstance(value, expected):
                raise TypeError(f"argument {name!r} must be {expected_name}")

    def _consume_rate_limit(self, schema: ToolSchema) -> None:
        now = self._clock()
        recent = [timestamp for timestamp in self._calls[schema.name] if now - timestamp < 60]
        if len(recent) >= schema.rate_limit:
            raise RuntimeError("rate limit exceeded")
        recent.append(now)
        self._calls[schema.name] = recent

    def audit_log(self) -> list[dict[str, Any]]:
        return [call.to_dict() for call in self.history]
