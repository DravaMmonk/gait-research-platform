from __future__ import annotations

import json
import sys
from pathlib import Path


def _load_outputs(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("properties", {}).get("outputs", payload)


def _read_output(outputs: dict, name: str, default=None):
    value = outputs.get(name, default)
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: python infra/azure/scripts/outputs_to_env.py <outputs.json> [target.env]", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    target_path = Path(sys.argv[2]) if len(sys.argv) == 3 else None

    outputs = _load_outputs(input_path)
    contract = _read_output(outputs, "infraContract", {}) or {}
    blob = contract.get("blob", {})
    postgres = contract.get("postgres", {})
    service_bus = contract.get("service_bus", {})

    env_lines = [
      "HF_ARTIFACT_BACKEND=azure_blob",
      f"HF_AZURE_BLOB_ACCOUNT_URL={blob.get('account_url', '')}",
      f"HF_AZURE_BLOB_CONTAINER={blob.get('container', '')}",
      f"HF_AZURE_SERVICE_BUS_NAMESPACE={service_bus.get('namespace', '')}",
      f"HF_AZURE_SERVICE_BUS_RUN_QUEUE={service_bus.get('run_queue', '')}",
      f"HF_AZURE_SERVICE_BUS_AGENT_QUEUE={service_bus.get('agent_queue', '')}",
    ]

    host = postgres.get("host", "")
    database = postgres.get("database", "")
    user = postgres.get("user", "")
    if host and database and user:
        env_lines.append(
          "HF_METADATA_DATABASE_URL="
          f"postgresql+psycopg://{user}:REPLACE_ME@{host}:5432/{database}?sslmode=require"
        )

    body = "\n".join(env_lines) + "\n"
    if target_path is not None:
        target_path.write_text(body, encoding="utf-8")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
