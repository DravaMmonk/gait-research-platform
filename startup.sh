#!/usr/bin/env sh
set -eu

PORT_VALUE="${PORT:-8000}"

exec python -m uvicorn hound_forward.api.app:app --host 0.0.0.0 --port "${PORT_VALUE}"
