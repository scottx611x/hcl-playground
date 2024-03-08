resource "aws_eks_cluster" "this" {
  name     = var.eks_cluster_name
  role_arn = aws_iam_role.this.arn

  vpc_config {
    subnet_ids = aws_subnet.this[*].id
    security_group_ids = [aws_security_group.eks_sg.id]
  }
}