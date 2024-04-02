resource "aws_efs_file_system" "this" {
  creation_token = var.eks_cluster_name
}

resource "aws_efs_mount_target" "this" {
  for_each       = toset(aws_subnet.this[*].id)
  file_system_id = aws_efs_file_system.this.id
  subnet_id      = each.value

  # TODO: eks made this behind the scenes
  security_groups = ["sg-091424d543f6f0ac7"]
}

output "efs_id" {
  value = aws_efs_file_system.this.id
}