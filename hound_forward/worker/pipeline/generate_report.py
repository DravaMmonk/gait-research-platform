from __future__ import annotations

from hound_forward.domain import AssetRecord, RunRecord


def generate_report(*, video_asset: AssetRecord, run: RunRecord, metrics: dict) -> dict:
    return {
        "summary": {
            "run_id": run.run_id,
            "manifest_id": run.manifest.id,
            "status": "completed",
            "runtime_validation": True,
            "placeholder_flags": {"dummy": True, "fake": True, "placeholder": True},
            "input_video_asset_id": video_asset.asset_id,
        },
        "report_type": "placeholder",
        "notes": "This report comes from the dummy runtime validation pipeline, not a real CV model.",
        "metrics": metrics,
    }
