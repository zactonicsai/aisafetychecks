module "cluster" {
  source          = "../../modules/k8s-cluster"
  cloud           = "eks"
  name            = "forge-eks"
  region          = "us-east-1"
  oidc_issuer_url = "https://keycloak.forge.example/realms/internal"
  enable_gpu      = true
}
