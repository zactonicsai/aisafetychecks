output "cluster_name" { value = azurerm_kubernetes_cluster.this.name }
output "resource_group_name" { value = azurerm_resource_group.this.name }
output "location" { value = var.location }
output "registry_url" { value = azurerm_container_registry.factory.login_server }
