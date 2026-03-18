@description('Azure region for Hound Forward resources.')
param location string = resourceGroup().location

@description('Deployment environment name.')
param environmentName string = 'dev'

@description('Storage account name.')
param storageAccountName string

@description('Primary blob container used by the application.')
param storageContainerName string = 'hound-platform'

@description('Azure PostgreSQL server name.')
param postgresServerName string

@description('Application database name.')
param postgresDatabaseName string = 'houndforward'

@description('PostgreSQL administrator login.')
param postgresAdminLogin string

@description('PostgreSQL administrator password.')
@secure()
param postgresAdminPassword string

@description('Azure Service Bus namespace name.')
param serviceBusNamespaceName string

@description('Run queue name.')
param serviceBusRunQueueName string = 'runs'

@description('Agent queue name.')
param serviceBusAgentQueueName string = 'agent-runs'

@description('Container Apps environment name.')
param containerAppsEnvironmentName string

@description('API container app name.')
param apiAppName string = 'hound-api'

@description('Agent container app name.')
param agentAppName string = 'hound-agent'

@description('Worker job name.')
param workerJobName string = 'hound-worker'

@description('API container image.')
param apiImage string = 'ghcr.io/example/hound-api:latest'

@description('Agent container image.')
param agentImage string = 'ghcr.io/example/hound-agent:latest'

@description('Worker container image.')
param workerImage string = 'ghcr.io/example/hound-worker:latest'

module storage './modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    storageAccountName: storageAccountName
    storageContainerName: storageContainerName
  }
}

module postgres './modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    location: location
    postgresServerName: postgresServerName
    postgresDatabaseName: postgresDatabaseName
    postgresAdminLogin: postgresAdminLogin
    postgresAdminPassword: postgresAdminPassword
  }
}

module servicebus './modules/servicebus.bicep' = {
  name: 'servicebus'
  params: {
    location: location
    serviceBusNamespaceName: serviceBusNamespaceName
    runQueueName: serviceBusRunQueueName
    agentQueueName: serviceBusAgentQueueName
  }
}

module apps './modules/containerapps.bicep' = {
  name: 'containerapps'
  params: {
    location: location
    environmentName: environmentName
    containerAppsEnvironmentName: containerAppsEnvironmentName
    apiAppName: apiAppName
    agentAppName: agentAppName
    workerJobName: workerJobName
    apiImage: apiImage
    agentImage: agentImage
    workerImage: workerImage
    blobAccountUrl: storage.outputs.blobEndpoint
    blobContainerName: storage.outputs.containerName
    serviceBusNamespaceName: servicebus.outputs.serviceBusNamespaceName
    serviceBusRunQueueName: servicebus.outputs.runQueueName
    serviceBusAgentQueueName: servicebus.outputs.agentQueueName
    metadataDatabaseUrl: postgres.outputs.metadataDatabaseUrl
    storageAccountResourceId: storage.outputs.storageAccountId
    serviceBusNamespaceResourceId: servicebus.outputs.serviceBusNamespaceId
  }
}

output infraContract object = {
  blob: {
    account_url: storage.outputs.blobEndpoint
    container: storage.outputs.containerName
  }
  postgres: {
    host: postgres.outputs.postgresFqdn
    database: postgres.outputs.postgresDatabase
    user: postgres.outputs.postgresAdminLogin
    metadata_database_url_secret_name: apps.outputs.metadataDatabaseUrlSecretName
  }
  service_bus: {
    namespace: servicebus.outputs.serviceBusNamespaceName
    run_queue: servicebus.outputs.runQueueName
    agent_queue: servicebus.outputs.agentQueueName
  }
}

output storageAccountId string = storage.outputs.storageAccountId
output storageBlobEndpoint string = storage.outputs.blobEndpoint
output storageContainer string = storage.outputs.containerName
output postgresServerId string = postgres.outputs.postgresServerId
output postgresServerFqdn string = postgres.outputs.postgresFqdn
output postgresDatabase string = postgres.outputs.postgresDatabase
output metadataDatabaseUrlSecretName string = apps.outputs.metadataDatabaseUrlSecretName
output serviceBusNamespaceId string = servicebus.outputs.serviceBusNamespaceId
output containerAppsEnvironmentId string = apps.outputs.containerAppsEnvironmentId
