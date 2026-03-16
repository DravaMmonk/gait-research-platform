# Azure Deployment

## Target Resources

The `infra/azure/main.bicep` scaffold provisions:

- Storage Account with Blob containers
- Azure PostgreSQL Flexible Server
- Azure Service Bus namespace and run queue
- Container Apps environment
- API and agent container apps
- worker job
- Log Analytics workspace

## Runtime Configuration

The application expects environment-driven settings:

- `HF_METADATA_DATABASE_URL`
- `HF_AZURE_BLOB_ACCOUNT_URL`
- `HF_AZURE_BLOB_CONTAINER`
- `HF_AZURE_SERVICE_BUS_NAMESPACE`
- `HF_AZURE_SERVICE_BUS_QUEUE`
- `HF_DEFAULT_RUNNER`
- `HF_PLACEHOLDER_WORKER_MODE`
- `HF_RESEARCH_TOOL_EXECUTION_MODE`
- `HF_FORMULA_EVALUATION_MODE`

## Local Parity

Local development uses the same metadata schema and run model. The expected local loop is:

1. run a local PostgreSQL-compatible database or SQLite fallback for development
2. run the FastAPI service
3. run the placeholder local worker path with `python -m hound_forward.worker.main`
4. switch only adapter wiring when moving to Azure

## Infrastructure Status

Azure infrastructure remains a scaffold. The platform now has stronger application-layer infrastructure for formula lifecycle storage and staged execution, but Azure deployment still targets the existing API, agent, and worker service shape.
