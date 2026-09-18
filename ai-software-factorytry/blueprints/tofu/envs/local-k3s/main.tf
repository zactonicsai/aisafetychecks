module "cluster" {
  source          = "../../modules/k8s-cluster"
  cloud           = "local-k3s"
  name            = "forge-dev"
  region          = "laptop"
  oidc_issuer_url = "http://keycloak.forge.internal/realms/internal"
  enable_gpu      = false
}
