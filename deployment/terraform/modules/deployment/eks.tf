resource "aws_eks_cluster" "this" {
  name     = var.eks_cluster_name
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = aws_subnet.this[*].id
    security_group_ids = [aws_security_group.eks_sg.id]
    endpoint_private_access = true
    endpoint_public_access = false
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Cluster handling.
  # Otherwise, EKS will not be able to properly delete EKS managed EC2 infrastructure such as Security Groups.
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]
}

data "aws_ssm_parameter" "eks_ami_release_version" {
  name = "/aws/service/eks/optimized-ami/${aws_eks_cluster.this.version}/amazon-linux-2/recommended/release_version"
}

data "aws_ssm_parameter" "eks_ami_image_id" {
  name = "/aws/service/eks/optimized-ami/${aws_eks_cluster.this.version}/amazon-linux-2/recommended/image_id"
}

resource "aws_launch_template" "this" {
  name_prefix   = "${var.eks_cluster_name}-"
  image_id      = nonsensitive(data.aws_ssm_parameter.eks_ami_image_id.value)
  instance_type = "t3.micro"

  user_data = <<-USERDATA
  #!/bin/bash
  set -o xtrace
  /etc/eks/bootstrap.sh ${var.eks_cluster_name}
  USERDATA
}

resource "aws_eks_node_group" "this" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "hcl-playground-development-node-group"
  node_role_arn   = aws_iam_role.eks_worker_role.arn
  subnet_ids      = aws_subnet.this[*].id
  version         = aws_eks_cluster.this.version
  release_version = nonsensitive(data.aws_ssm_parameter.eks_ami_release_version.value)

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }

  launch_template {
    id = aws_launch_template.this.id
    version = "$Latest"
  }

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }

  instance_types = ["t3.micro"]

  capacity_type = "SPOT"

  depends_on = [
    aws_iam_service_linked_role.AWSServiceRoleForAmazonEKSNodegroup,
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
  ]
}