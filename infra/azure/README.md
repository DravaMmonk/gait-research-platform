# Azure Infrastructure

`infra/azure/main.bicep` now acts as the orchestration layer for a modular Azure platform base.

## Layout

- [`main.bicep`](/Users/drava/Documents/Hound/hf-playground/infra/azure/main.bicep): top-level orchestration
- [`modules/storage.bicep`](/Users/drava/Documents/Hound/hf-playground/infra/azure/modules/storage.bicep): Blob Storage account and container
- [`modules/postgres.bicep`](/Users/drava/Documents/Hound/hf-playground/infra/azure/modules/postgres.bicep): PostgreSQL server and database
- [`modules/servicebus.bicep`](/Users/drava/Documents/Hound/hf-playground/infra/azure/modules/servicebus.bicep): Service Bus namespace plus `agent-runs` and `runs` queues
- [`modules/containerapps.bicep`](/Users/drava/Documents/Hound/hf-playground/infra/azure/modules/containerapps.bicep): Container Apps runtime, identities, and app wiring

## Environment Contract

The deployment parameter contract is represented by:

- [`parameters.dev.example.json`](/Users/drava/Documents/Hound/hf-playground/infra/azure/parameters.dev.example.json)

Create a local `infra/azure/parameters.dev.json` from that file and fill in secrets outside the repo. The concrete `.json` file is ignored by git.

## Output Contract

`main.bicep` exports an `infraContract` object with the stable platform outputs:

- `blob.account_url`
- `blob.container`
- `postgres.host`
- `postgres.database`
- `postgres.user`
- `service_bus.namespace`
- `service_bus.run_queue`
- `service_bus.agent_queue`

That contract is intentionally shaped to become application env vars without the app needing Azure-specific deployment context.

## Outputs To Env

Use [`outputs_to_env.py`](/Users/drava/Documents/Hound/hf-playground/infra/azure/scripts/outputs_to_env.py) to convert deployment outputs into runtime env variables:

```bash
python infra/azure/scripts/outputs_to_env.py infra/azure/outputs.dev.json .env.azure
```

This enforces the boundary:

`infra -> outputs -> env -> app`
