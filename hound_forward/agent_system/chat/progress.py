from __future__ import annotations

from hound_forward.domain import ExecutionPlan


def build_progress_messages(plan: ExecutionPlan) -> list[str]:
    messages = ["Planning analysis...", "Running execution plan..."]
    stage_labels = {
        "decode_video": "Decoding video...",
        "extract_keypoints": "Extracting keypoints...",
        "compute_gait_metrics": "Computing metrics...",
        "generate_report": "Generating report...",
    }
    for stage in plan.stages:
        messages.append(stage_labels.get(stage.name, f"Running {stage.name}..."))
    messages.extend(["Explaining results...", "Done."])
    return messages
