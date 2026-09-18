# Azure AKS — not EKS. EKS is AWS.
module "cluster" {
  source          = "../../modules/k8s-cluster"
  cloud           = "aks"
  name            = "forge-aks"
  region          = "eastus2"
  oidc_issuer_url = "https://keycloak.forge.example/realms/internal"
  enable_gpu      = true
}
