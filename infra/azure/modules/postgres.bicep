@description('Azure region for Hound Forward resources.')
param location string

@description('Azure PostgreSQL server name.')
param postgresServerName string

@description('Application database name.')
param postgresDatabaseName string

@description('PostgreSQL administrator login.')
param postgresAdminLogin string

@description('PostgreSQL administrator password.')
@secure()
param postgresAdminPassword string

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: postgresServerName
  location: location
  sku: {
    name: 'Standard_B2s'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
    storage: {
      storageSizeGB: 32
    }
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  name: postgresDatabaseName
  parent: postgres
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

var postgresFqdn = '${postgresServerName}.postgres.database.azure.com'
var metadataDatabaseUrl = 'postgresql+psycopg://${postgresAdminLogin}:${postgresAdminPassword}@${postgresFqdn}:5432/${postgresDatabaseName}?sslmode=require'

output postgresServerId string = postgres.id
output postgresServerName string = postgresServerName
output postgresFqdn string = postgresFqdn
output postgresDatabase string = postgresDatabaseName
output postgresAdminLogin string = postgresAdminLogin
output metadataDatabaseUrl string = metadataDatabaseUrl
