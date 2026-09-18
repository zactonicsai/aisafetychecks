variable "name" {
  type    = string
  default = "ai-factory-dev"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "kubernetes_version" {
  type    = string
  default = null
}

variable "registry_name" {
  description = "Globally unique lowercase alphanumeric Azure Container Registry name"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9]{5,50}$", var.registry_name))
    error_message = "registry_name must be 5-50 lowercase alphanumeric characters."
  }
}
variable "admin_cidrs" {
  type        = list(string)
  description = "Trusted CIDRs for the AKS API server"
  validation {
    condition     = length(var.admin_cidrs) > 0 && !contains(var.admin_cidrs, "0.0.0.0/0")
    error_message = "Provide trusted CIDRs and do not use 0.0.0.0/0."
  }
}
variable "node_vm_size" {
  type    = string
  default = "Standard_D4s_v5"
}

variable "node_count" {
  type    = number
  default = 2
}

variable "node_min" {
  type    = number
  default = 1
}

variable "node_max" {
  type    = number
  default = 4
}
