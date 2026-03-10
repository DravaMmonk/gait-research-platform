# Azure Infrastructure Scaffold

This Bicep template provisions the first-stage Azure footprint for the Hound Forward research platform:

- Azure Blob Storage for run artifacts
- Azure PostgreSQL Flexible Server for metadata
- Azure Service Bus for run queueing
- Azure Container Apps environment for API and agent services
- Azure Container Apps Job for workers
- Azure Monitor / Log Analytics for observability

The template intentionally avoids application-level secrets or hardcoded tenant-specific values. The application reads runtime values through environment variables and platform settings.
