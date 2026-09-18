locals {
  tags = {
    project     = "ai-software-factory"
    environment = "development"
    managed-by  = "opentofu"
  }
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${var.name}"
  location = var.location
  tags     = local.tags
}

resource "azurerm_virtual_network" "this" {
  name                = "vnet-${var.name}"
  address_space       = ["10.50.0.0/16"]
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  tags                = local.tags
}

resource "azurerm_subnet" "aks" {
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.this.name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = ["10.50.0.0/20"]
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "log-${var.name}"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_kubernetes_cluster" "this" {
  name                          = var.name
  location                      = azurerm_resource_group.this.location
  resource_group_name           = azurerm_resource_group.this.name
  dns_prefix                    = var.name
  kubernetes_version            = var.kubernetes_version
  local_account_disabled        = true
  oidc_issuer_enabled           = true
  workload_identity_enabled     = true
  role_based_access_control_enabled = true
  api_server_access_profile {
    authorized_ip_ranges = var.admin_cidrs
  }
  default_node_pool {
    name                 = "system"
    vm_size              = var.node_vm_size
    vnet_subnet_id       = azurerm_subnet.aks.id
    auto_scaling_enabled = true
    node_count           = var.node_count
    min_count            = var.node_min
    max_count            = var.node_max
    only_critical_addons_enabled = false
    os_disk_type         = "Managed"
  }
  identity { type = "SystemAssigned" }
  azure_active_directory_role_based_access_control {
    azure_rbac_enabled = true
  }
  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    network_policy      = "cilium"
    network_data_plane  = "cilium"
    load_balancer_sku   = "standard"
    outbound_type       = "loadBalancer"
  }
  oms_agent {
    log_analytics_workspace_id      = azurerm_log_analytics_workspace.this.id
    msi_auth_for_monitoring_enabled = true
  }
  key_vault_secrets_provider { secret_rotation_enabled = true }
  tags = local.tags
}

resource "azurerm_container_registry" "factory" {
  name                          = var.registry_name
  resource_group_name           = azurerm_resource_group.this.name
  location                      = azurerm_resource_group.this.location
  sku                           = "Standard"
  admin_enabled                 = false
  public_network_access_enabled = true
  tags                          = local.tags
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.factory.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
}
