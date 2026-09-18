# Adapter module. Each cloud is a thin implementation behind the same variables.
# Real providers would be hashicorp/azurerm, hashicorp/google, hashicorp/aws.
# This file documents the contract the factory uses.

locals {
  labels = {
    "forge.aether.io/cluster" = var.name
    "forge.aether.io/cloud"   = var.cloud
    "forge.aether.io/managed" = "opentofu"
  }
}

# Pseudo-resources so the module is readable without cloud credentials.
# Replace with real azurerm_kubernetes_cluster / google_container_cluster /
# aws_eks_cluster blocks when wiring a subscription.

output "cluster_id" {
  value = "${var.cloud}-${var.name}-${var.region}"
}

output "deploy_contract" {
  value = {
    api           = "kubernetes"
    gitops_root   = "platform/gitops/${var.cloud}-${var.name}"
    registry      = "harbor.forge.internal"
    identity      = var.oidc_issuer_url
    notes         = "Apps never call cloud APIs directly. GitOps applies manifests."
  }
}
