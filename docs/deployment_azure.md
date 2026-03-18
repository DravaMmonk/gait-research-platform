# Azure Deployment

## Delivery Model

This repository now follows an infra-first Azure delivery shape:

1. Define Azure storage, database, queue, and app resources in IaC first.
2. Use the same SDK-backed adapters locally against either Azure cloud resources or local emulators.
3. Treat Bicep as the source of truth for resource topology and runtime wiring.
4. Let CI/CD deploy infrastructure and then roll application images onto the provisioned resources.

## Step 1: Define Azure Resources

The stable base layer is managed in Bicep first, before app code rollout.

Use:

- [`main.bicep`](/Users/drava/Documents/Hound/hf-playground/infra/azure/main.bicep)
- [`parameters.dev.example.json`](/Users/drava/Documents/Hound/hf-playground/infra/azure/parameters.dev.example.json)

The parameter file is not just an example. It is the environment contract for a deployable dev environment.

### Required local setup

1. Copy `infra/azure/parameters.dev.example.json` to `infra/azure/parameters.dev.json`
2. Fill in environment-specific values
3. Keep secrets out of git

## Provisioned Resources

`infra/azure/main.bicep` provisions:

- one Blob Storage account
- one application Blob container for run and session assets
- one Azure PostgreSQL Flexible Server and application database
- one Service Bus namespace
- one `agent-runs` queue for remote agent jobs
- one `runs` queue for pipeline execution
- one Log Analytics workspace
- one Container Apps environment
- one API Container App
- one agent Container App
- one schedule-triggered worker Container App Job
- system-assigned managed identities for API, agent, and worker
- Blob Data Contributor RBAC assignments for those managed identities

## Step 1 Output Contract

The top-level deployment exports a stable `infraContract` object:

```json
{
  "blob": {
    "account_url": "...",
    "container": "..."
  },
  "postgres": {
    "host": "...",
    "database": "...",
    "user": "..."
  },
  "service_bus": {
    "namespace": "...",
    "run_queue": "runs",
    "agent_queue": "agent-runs"
  }
}
```

This is the boundary between infra and app runtime.

## Runtime Wiring

The Bicep template now injects or derives the core runtime settings expected by the app:

- `HF_METADATA_DATABASE_URL`
- `HF_AZURE_BLOB_ACCOUNT_URL`
- `HF_AZURE_BLOB_CONTAINER`
- `HF_AZURE_SERVICE_BUS_NAMESPACE`
- `HF_AZURE_SERVICE_BUS_QUEUE`
- `HF_AZURE_SERVICE_BUS_RUN_QUEUE`
- `HF_AZURE_SERVICE_BUS_AGENT_QUEUE`
- `HF_QUEUE_BACKEND`
- `HF_PLACEHOLDER_WORKER_MODE`

For local development and emulator usage, the runtime also supports:

- `HF_AZURE_BLOB_CONNECTION_STRING`

Use `HF_AZURE_BLOB_CONNECTION_STRING` when developing against Azurite or another emulator. Use `HF_AZURE_BLOB_ACCOUNT_URL` when developing against real Azure with `DefaultAzureCredential`.

## Step 2: Local Development

### Option A: Connect to Azure cloud resources

- point `HF_METADATA_DATABASE_URL` at the Azure PostgreSQL database
- set `HF_AZURE_BLOB_ACCOUNT_URL` to the Storage Account Blob endpoint
- set `HF_AZURE_BLOB_CONTAINER` to the Bicep-managed application container
- authenticate locally with `az login` so the SDK can use `DefaultAzureCredential`

### Option B: Connect to local emulators

- run a PostgreSQL instance locally
- run Azurite for Blob Storage
- set `HF_METADATA_DATABASE_URL` to the local PostgreSQL database
- set `HF_AZURE_BLOB_CONNECTION_STRING` to the Azurite connection string
- set `HF_AZURE_BLOB_CONTAINER` to the same logical container name used in cloud

This preserves adapter parity: the application still uses the Azure Blob adapter locally, rather than swapping to a different upload path.

## Step 3: Outputs To Env

Export deployment outputs:

```bash
az deployment group show \
  --resource-group "<resource-group>" \
  --name "<deployment-name>" \
  --query properties.outputs \
  --output json > infra/azure/outputs.dev.json
```

Then convert them to env vars:

```bash
python infra/azure/scripts/outputs_to_env.py infra/azure/outputs.dev.json .env.azure
```

At that point the application consumes env vars only. It does not need to know anything about Bicep internals.

## Step 4: Interface Development

The upload path should stay SDK-native. The backend already follows that pattern:

- FastAPI upload endpoint
- service-layer asset registration
- Azure Blob SDK upload in the storage adapter

Do not introduce a local-filesystem-first code path for the cloud upload contract.

## Step 5: Deployment Sequence

### 1. Deploy infrastructure

Use `az deployment group create` against `infra/azure/main.bicep` with the required parameters:

- storage account name
- blob container name
- PostgreSQL server name
- PostgreSQL database name
- PostgreSQL admin login and password
- Service Bus namespace name
- Service Bus run queue name
- Service Bus agent queue name
- Container Apps environment name
- worker schedule cron
- API, agent, and worker image references

### 2. Initialize schema

After PostgreSQL is provisioned, apply [`db/schema.sql`](/Users/drava/Documents/Hound/hf-playground/db/schema.sql) to the target database.

### 3. Build and publish images

Build and push the three runtime images:

- `Dockerfile.api`
- `Dockerfile.agent`
- `Dockerfile.worker`

The intended mapping is:

- API Container App -> `Dockerfile.api`
- Agent Container App -> `Dockerfile.agent`
- Worker Container Apps Job -> `Dockerfile.worker`

The worker image should process a bounded batch of queue messages and exit. The Azure Job restarts it on the configured cron schedule.

### 4. Deploy code

Update the Bicep parameters or deployment variables so the Container Apps resources point at the desired image tags.

## CI/CD Expectation

CI should verify tests and type/lint checks. CD should:

- authenticate to Azure
- deploy or update the Bicep stack
- apply database schema changes
- build and push the API, agent, and worker images
- update API, agent, and worker image references

This repository's current workflow should be extended in that order rather than pushing code to Azure before the resource contract exists.
