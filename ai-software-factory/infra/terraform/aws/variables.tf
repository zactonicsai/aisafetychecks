variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "Short factory and cluster name"
  type        = string
  default     = "ai-factory-dev"
}

variable "kubernetes_version" {
  description = "Supported EKS minor version; verify before apply"
  type        = string
  default     = "1.34"
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "admin_cidrs" {
  description = "CIDRs allowed to reach the public EKS API; use trusted /32 addresses or VPN ranges"
  type        = list(string)
  validation {
    condition     = length(var.admin_cidrs) > 0 && !contains(var.admin_cidrs, "0.0.0.0/0")
    error_message = "Provide at least one trusted CIDR and do not use 0.0.0.0/0."
  }
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.large"]
}

variable "node_min" {
  type    = number
  default = 1
}

variable "node_desired" {
  type    = number
  default = 2
}

variable "node_max" {
  type    = number
  default = 4
}
