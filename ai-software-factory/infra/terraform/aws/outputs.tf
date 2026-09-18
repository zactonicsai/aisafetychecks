output "cluster_name" { value = aws_eks_cluster.this.name }
output "region" { value = var.region }
output "cluster_endpoint" {
  value     = aws_eks_cluster.this.endpoint
  sensitive = true
}
output "vpc_id" { value = aws_vpc.this.id }
output "registry_url" { value = aws_ecr_repository.factory.repository_url }
