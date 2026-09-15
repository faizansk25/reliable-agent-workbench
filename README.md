# Reliable Agent Workbench

[![CI](https://github.com/faizansk25/reliable-agent-workbench/actions/workflows/ci.yml/badge.svg)](https://github.com/faizansk25/reliable-agent-workbench/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

A deterministic Python workbench for exercising the failure boundaries that make tool-using
agents difficult: state transitions, permissions, argument validation, rate limits, explicit
approval, checkpoint recovery, verification, and audit trails.

It is not an autonomous web agent, an MCP implementation, or a hosted production platform. It is
a compact reliability reference with executable tests and no required API key.

## Verified capabilities

- Explicit state machine with rejected invalid transitions
- Atomic, versioned JSON checkpoints and restoration
- Tool schemas with required arguments and basic JSON-type validation
- Least-privilege permission checks before tool execution
- Human approval pauses that survive checkpoint reload and resume
- Per-tool sliding-window rate limits
- Exception containment and structured call results
- Configurable post-action verification and hard step limits
- Durable execution trace plus tool audit log
- Bounded short-term memory and versioned local long-term memory
- Deterministic local document retrieval for offline demos
- Unit tests, static checks, compilation, and GitHub Actions CI

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

python -m core --checkpoint-dir checkpoints
pytest -q
```

The CLI runs one injected, offline tool and writes `checkpoints/latest.json`. It is deliberately
small: reliability behavior can be inspected without hiding it behind an LLM framework.

## Minimal agent

```python
from agents import ScriptedPlanner
from core import Agent, Permission, PlanStep, ToolRegistry, ToolSchema

registry = ToolRegistry()
registry.register(
    ToolSchema(
        name="uppercase",
        description="uppercase text",
        permissions=(Permission.READ,),
        parameters={
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
    ),
    lambda text: text.upper(),
)
planner = ScriptedPlanner([PlanStep("uppercase", {"text": "inspect me"})])
outcome = Agent(registry, planner, permissions=(Permission.READ,)).run("demo")
print(outcome.status, outcome.checkpoint)
```

## Approval recovery

Mark a `ToolSchema` with `requires_approval=True`. `Agent.run()` then returns a
`waiting_approval` outcome before calling the tool. Restore and continue explicitly:

```python
from core import Agent, StateManager

restored = StateManager.load_checkpoint("checkpoints/latest.json")
agent = Agent(registry, planner, permissions=(Permission.READ,), state=restored)
outcome = agent.resume(approved=True)  # False fails closed without invoking the tool
```

Approval is a control boundary, not a UI. A real application must authenticate the approver and
protect checkpoint files. Tool permissions describe allowed capabilities; they are not an OS
sandbox. Network, subprocess, and filesystem isolation remain deployment responsibilities.

## Repository layout

```text
core/       agent loop, state, tools, memory, CLI
agents/     deterministic planners and workflow composition
tools/      real offline tools (no fabricated network results)
tests/      state, permission, approval, recovery, limits, and memory tests
```

## Author

Faizan Muktar Shaikh — [LinkedIn](https://www.linkedin.com/in/faizansk25) · [GitHub](https://github.com/faizansk25)
