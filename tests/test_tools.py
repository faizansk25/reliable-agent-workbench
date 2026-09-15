from core import Permission, ToolRegistry, ToolSchema


def schema(**overrides):
    values = {
        "name": "echo",
        "description": "echo text",
        "permissions": (Permission.READ,),
        "parameters": {
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
        "rate_limit": 2,
    }
    values.update(overrides)
    return ToolSchema(**values)


def test_registry_enforces_permissions_and_schema():
    registry = ToolRegistry()
    registry.register(schema(), lambda text: text.upper())

    denied = registry.execute("echo", {"text": "hello"}, ())
    invalid = registry.execute("echo", {"text": 3}, (Permission.READ,))
    allowed = registry.execute("echo", {"text": "hello"}, (Permission.READ,))

    assert not denied.success and "missing permissions" in denied.error
    assert not invalid.success and "must be string" in invalid.error
    assert allowed.success and allowed.output_data == "HELLO"


def test_registry_requires_approval_and_rate_limits():
    now = [0.0]
    registry = ToolRegistry(clock=lambda: now[0])
    registry.register(schema(requires_approval=True, rate_limit=1), lambda text: text)

    waiting = registry.execute("echo", {"text": "a"}, (Permission.READ,))
    first = registry.execute("echo", {"text": "a"}, (Permission.READ,), approved=True)
    limited = registry.execute("echo", {"text": "b"}, (Permission.READ,), approved=True)
    now[0] = 61.0
    recovered = registry.execute("echo", {"text": "c"}, (Permission.READ,), approved=True)

    assert "approval required" in waiting.error
    assert first.success
    assert "rate limit exceeded" in limited.error
    assert recovered.success
