# Local Run Commands

This document defines the long-lived local run command contract for the repository.

It is intentionally written as a stable interface document. Tooling around these commands may evolve, but the role-based entrypoints below should remain the canonical local development surface.

## Command Contract

The repository exposes these local runtime roles:

- API
- worker
- agent runtime
- frontend

The canonical local commands are:

### API

```bash
uvicorn hound_forward.api.app:app --reload
```

This is the stable local HTTP entrypoint for the backend API.

### Worker

```bash
python -m hound_forward.worker.main
```

This is the stable local CLI entrypoint for worker-side queue processing.

### Agent Runtime

```bash
python -m hound_forward.agent.main
```

This is the stable local CLI entrypoint for the remote-style agent runtime.

Use it when the development task touches agent orchestration or agent job execution. Do not require it for every frontend or API-only change.

### Frontend

```bash
cd frontend/research_console
npm run dev
```

This is the stable local development entrypoint for the Next.js research console.

## Environment Setup Contract

The local runtime assumes:

- project dependencies are installed
- `.env` exists and is based on `.env.example`
- the default local environment keeps metadata, queueing, and artifacts local unless explicitly overridden

Current local defaults are defined in [`.env.example`](/Users/drava/Documents/Hound/hf-playground/.env.example).

## Recommended Daily Loops

### Backend Loop

Use this loop for API, worker, metric, and pipeline work:

```bash
uvicorn hound_forward.api.app:app --reload
python -m hound_forward.worker.main
```

### Agent Loop

Use this loop only when agent planning or orchestration is part of the change:

```bash
uvicorn hound_forward.api.app:app --reload
python -m hound_forward.agent.main
python -m hound_forward.worker.main
```

### Frontend Loop

Use this loop for UI work:

```bash
uvicorn hound_forward.api.app:app --reload
cd frontend/research_console
npm run dev
```

## Stability Rules

To keep this document valid over time, the following are the actual contract:

- `hound_forward.api.app:app` remains the local API entrypoint
- `python -m hound_forward.worker.main` remains the local worker entrypoint
- `python -m hound_forward.agent.main` remains the local agent entrypoint
- `frontend/research_console` remains the local frontend app root

Wrapper scripts, Make targets, task runners, container commands, and package-manager-specific bootstrapping may change without changing this document.

## Related Documents

- [docs/local_cloudrun_dev_workflow.md](/Users/drava/Documents/Hound/hf-playground/docs/local_cloudrun_dev_workflow.md)
- [docs/dev_data_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/dev_data_contract.md)
- [docs/worker_local_mode_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/worker_local_mode_contract.md)
