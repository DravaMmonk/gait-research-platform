@description('Azure region for Hound Forward resources.')
param location string

@description('Azure Container Registry name.')
param registryName string

@description('SKU for Azure Container Registry.')
param sku string = 'Basic'

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
  }
}

output registryId string = registry.id
output registryName string = registry.name
output loginServer string = registry.properties.loginServer
