from __future__ import annotations

import argparse
import json
from typing import Any, Callable


ToolFn = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


def run_cli(tool_name: str, tool_fn: ToolFn) -> None:
    parser = argparse.ArgumentParser(prog=tool_name)
    parser.add_argument("--input", required=True, help="Primary input file path")
    parser.add_argument("--output", required=True, help="Artifact output path")
    parser.add_argument(
        "--config",
        default=None,
        help="JSON string with explicit config. Optional.",
    )
    args = parser.parse_args()
    config = json.loads(args.config) if args.config else None
    result = tool_fn(args.input, args.output, config)
    print(json.dumps(result, indent=2, sort_keys=True))

