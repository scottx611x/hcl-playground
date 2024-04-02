resource "aws_efs_file_system" "this" {
  creation_token = var.eks_cluster_name
}

resource "aws_efs_mount_target" "this" {
  for_each = aws_subnet.this[*].id
  file_system_id = aws_efs_file_system.this.id
  subnet_id      = each.value
}

output "efs_id" {
  value = aws_efs_file_system.this.id
}