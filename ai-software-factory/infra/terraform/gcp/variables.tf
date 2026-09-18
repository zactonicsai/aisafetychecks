variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "name" {
  type    = string
  default = "ai-factory-dev"
}

variable "kubernetes_version" {
  type    = string
  default = null
}
variable "admin_cidr" {
  type        = string
  description = "Trusted CIDR for the GKE control plane"
  validation {
    condition     = var.admin_cidr != "0.0.0.0/0"
    error_message = "Do not expose the control plane to 0.0.0.0/0."
  }
}
variable "machine_type" {
  type    = string
  default = "e2-standard-4"
}

variable "node_min" {
  type    = number
  default = 1
}

variable "node_max" {
  type    = number
  default = 4
}
