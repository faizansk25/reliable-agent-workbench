"""Run an offline, deterministic demonstration of the safety boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents import ScriptedPlanner

from .agent import Agent, PlanStep
from .state import StateManager
from .tools import Permission, ToolRegistry, ToolSchema


def build_demo(checkpoint_dir: Path) -> Agent:
    registry = ToolRegistry()
    registry.register(
        ToolSchema(
            name="normalize",
            description="normalize user-supplied text",
            permissions=(Permission.READ,),
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        ),
        lambda text: " ".join(text.lower().split()),
    )
    planner = ScriptedPlanner(
        [PlanStep("normalize", {"text": "Reliable   Agent Demo"}, "normalize input")]
    )
    return Agent(
        registry,
        planner,
        permissions=(Permission.READ,),
        state=StateManager(checkpoint_dir),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reliable-agent-workbench")
    parser.add_argument("--task", default="run the offline reliability demo")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"))
    args = parser.parse_args(argv)
    outcome = build_demo(args.checkpoint_dir).run(args.task)
    print(json.dumps({"status": outcome.status, "checkpoint": outcome.checkpoint}, indent=2))
    return 0 if outcome.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
