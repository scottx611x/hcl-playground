resource "aws_eks_cluster" "this" {
  name     = "my-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = aws_subnet.this[*].id
    security_group_ids = [aws_security_group.eks_sg.id]
  }
}