resource "aws_efs_file_system" "this" {
  creation_token = var.eks_cluster_name
}

output "efs_id" {
  value = aws_efs_file_system.this.id
}