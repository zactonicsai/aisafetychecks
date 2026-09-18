module "cluster" {
  source          = "../../modules/k8s-cluster"
  cloud           = "gke"
  name            = "forge-gke"
  region          = "us-central1"
  oidc_issuer_url = "https://keycloak.forge.example/realms/internal"
  enable_gpu      = true
}
