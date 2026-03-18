from __future__ import annotations

from typing import Any

from .interfaces import Job


def serialize_job(job: Job) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "job_type": job.job_type,
        "run_id": job.run_id,
        "session_id": job.session_id,
        "payload": job.payload,
        "metadata": job.metadata,
    }


def deserialize_job(payload: dict[str, Any]) -> Job:
    return Job(
        job_id=payload["job_id"],
        job_type=payload["job_type"],
        run_id=payload["run_id"],
        session_id=payload.get("session_id"),
        payload=payload.get("payload", {}),
        metadata=payload.get("metadata", {}),
    )
