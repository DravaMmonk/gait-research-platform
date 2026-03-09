from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from gait_research_platform.agents.experiment_agent import ExperimentAgent
from gait_research_platform.agents.llm_client import OpenAICompatibleClient
from gait_research_platform.core.config_loader import load_config


def build_agent(
    config_path: str,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> ExperimentAgent:
    base_config = load_config(config_path)
    llm_client = None
    if api_key or base_url or model:
        llm_client = OpenAICompatibleClient(
            api_key=api_key,
            base_url=base_url,
            default_model=model or base_config["agent"]["model"],
        )
        base_config["agent"]["enabled"] = True
        if model:
            base_config["agent"]["model"] = model
    elif base_config.get("agent", {}).get("enabled", False) or os.getenv("OPENAI_API_KEY"):
        llm_client = OpenAICompatibleClient(default_model=base_config["agent"]["model"])
    return ExperimentAgent(base_config, llm_client=llm_client)


def main() -> None:
    parser = argparse.ArgumentParser(description="Thin CLI wrapper for the gait research agent.")
    parser.add_argument("--base-config", default="gait_research_platform/configs/experiments/contrastive.yaml")
    parser.add_argument("--api-key", help="Optional OpenAI-compatible API key. Falls back to OPENAI_API_KEY.")
    parser.add_argument("--base-url", help="Optional OpenAI-compatible base URL. Falls back to OPENAI_BASE_URL.")
    parser.add_argument("--model", help="Optional model name. Falls back to OPENAI_MODEL or config value.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Plan experiment configs.")
    plan_parser.add_argument("--goal", required=True)
    plan_parser.add_argument("--num-candidates", type=int, default=1)
    plan_parser.add_argument("--use-llm", action="store_true")

    run_parser = subparsers.add_parser("run", help="Run an approved experiment config.")
    run_parser.add_argument("--config", required=True)
    run_parser.add_argument("--approve", action="store_true")

    review_parser = subparsers.add_parser("review", help="Review an experiment by id.")
    review_parser.add_argument("--experiment-id", required=True)

    combined_parser = subparsers.add_parser("plan-run-review", help="Plan, run, and review in one command.")
    combined_parser.add_argument("--goal", required=True)
    combined_parser.add_argument("--use-llm", action="store_true")
    combined_parser.add_argument("--approve", action="store_true")

    args = parser.parse_args()
    agent = build_agent(
        config_path=args.base_config,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
    )

    if args.command == "plan":
        plans = agent.plan(goal=args.goal, use_llm=args.use_llm, num_candidates=args.num_candidates)
        print(json.dumps(plans, indent=2))
        return

    if args.command == "run":
        config_path = Path(args.config)
        config = load_config(config_path)
        run_request = agent.request_run(config)
        result = agent.run(run_request, approved=args.approve)
        print(json.dumps(result, indent=2))
        return

    if args.command == "review":
        result_dir = agent.data_manager.result_dir(args.experiment_id)
        result = {
            "experiment_id": args.experiment_id,
            "status": "failed" if agent.data_manager.load_error(result_dir) else "success",
            "result_dir": str(result_dir),
            "metrics": agent.data_manager.load_metrics(result_dir),
            "summary": agent.data_manager.load_summary(result_dir),
            "error": agent.data_manager.load_error(result_dir),
        }
        print(json.dumps(agent.review(result), indent=2))
        return

    if args.command == "plan-run-review":
        plans = agent.plan(goal=args.goal, use_llm=args.use_llm, num_candidates=1)
        run_request = agent.request_run(plans[0])
        result = agent.run(run_request, approved=args.approve)
        review = agent.review(result)
        print(json.dumps({"plan": plans[0], "result": result, "review": review}, indent=2))


if __name__ == "__main__":
    main()
