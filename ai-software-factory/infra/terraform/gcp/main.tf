resource "google_project_service" "services" {
  for_each = toset([
    "container.googleapis.com",
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "this" {
  name                    = var.name
  auto_create_subnetworks = false
  depends_on              = [google_project_service.services]
}

resource "google_compute_subnetwork" "this" {
  name          = var.name
  region        = var.region
  network       = google_compute_network.this.id
  ip_cidr_range = "10.60.0.0/20"
  private_ip_google_access = true
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.64.0.0/14"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.68.0.0/20"
  }
}

resource "google_compute_router" "this" {
  name    = var.name
  region  = var.region
  network = google_compute_network.this.id
}

resource "google_compute_router_nat" "this" {
  name                               = var.name
  router                             = google_compute_router.this.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_service_account" "nodes" {
  account_id   = "${substr(var.name, 0, 18)}-nodes"
  display_name = "GKE nodes for ${var.name}"
}

resource "google_project_iam_member" "node_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/artifactregistry.reader"
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.nodes.email}"
}

resource "google_container_cluster" "this" {
  name                     = var.name
  location                 = var.region
  network                  = google_compute_network.this.id
  subnetwork               = google_compute_subnetwork.this.id
  min_master_version       = var.kubernetes_version
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = false
  networking_mode          = "VPC_NATIVE"
  release_channel { channel = "REGULAR" }
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = var.admin_cidr
      display_name = "administrators"
    }
  }
  workload_identity_config { workload_pool = "${var.project_id}.svc.id.goog" }
  binary_authorization { evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE" }
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"
  depends_on = [google_project_service.services, google_compute_router_nat.this]
}

resource "google_container_node_pool" "system" {
  name       = "system"
  location   = var.region
  cluster    = google_container_cluster.this.name
  node_count = var.node_min
  autoscaling {
    min_node_count = var.node_min
    max_node_count = var.node_max
  }
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  node_config {
    machine_type    = var.machine_type
    service_account = google_service_account.nodes.email
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]
    labels          = { workload = "system" }
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
    workload_metadata_config { mode = "GKE_METADATA" }
  }
  depends_on = [google_project_iam_member.node_roles]
}

resource "google_artifact_registry_repository" "factory" {
  location      = var.region
  repository_id = "ai-factory"
  description   = "AI software factory OCI images"
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}
