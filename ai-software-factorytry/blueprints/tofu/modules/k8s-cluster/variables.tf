variable "cloud" {
  description = "aks | gke | eks | local-k3s"
  type        = string
}

variable "name" {
  type = string
}

variable "region" {
  type = string
}

variable "oidc_issuer_url" {
  description = "Keycloak realm issuer for kubectl OIDC"
  type        = string
}

variable "node_size" {
  type    = string
  default = "medium"
}

variable "enable_gpu" {
  type    = bool
  default = false
}
