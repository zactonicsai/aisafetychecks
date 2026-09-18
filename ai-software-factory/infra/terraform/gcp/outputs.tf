output "cluster_name" { value = google_container_cluster.this.name }
output "project_id" { value = var.project_id }
output "region" { value = var.region }
output "registry_url" { value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.factory.repository_id}/simulator" }
