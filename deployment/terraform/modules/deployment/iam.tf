resource "aws_iam_role" "eks_cluster_role" {
  name = "eksClusterRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  role       = aws_iam_role.eks_cluster_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role" "eks_worker_role" {
  name = "eksWorkerRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_policy" "eks_worker_policy" {
  name        = "eks-worker-policy"
  description = "Policy for EKS workers"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "acm:List*",
          "acm:Describe*",
          "elasticloadbalancing:Describe*",
          "ec2:Describe*",
          "ec2:CreateSecurityGroup",
          "ec2:CreateTags",
          "ec2:CreateVolume",
          "ec2:AttachVolume",
          "ec2:Revoke*",
          "ec2:AuthorizeSecurityGroupIngress",
          "elasticloadbalancing:ModifyRule",
          "elasticloadbalancing:RegisterTargets",
          "elasticloadbalancing:DeregisterTargets",
          "elasticloadbalancing:DeleteTargetGroup",
          "elasticloadbalancing:CreateTargetGroup",
          "elasticloadbalancing:CreateLoadBalancer",
          "elasticloadbalancing:CreateListener",
          "elasticloadbalancing:CreateRule",
          "elasticloadbalancing:AddTags",
          "wafv2:GetWebACLForResource",
          "waf-regional:GetWebACLForResource"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_policy_attachment" {
  role       = aws_iam_role.eks_worker_role.name
  policy_arn = aws_iam_policy.eks_worker_policy.arn
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  role       = aws_iam_role.eks_worker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  role       = aws_iam_role.eks_worker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "eks_ecr_policy" {
  role       = aws_iam_role.eks_worker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# https://github.com/terraform-aws-modules/terraform-aws-eks/issues/823#issuecomment-633783718
resource "aws_iam_service_linked_role" "AWSServiceRoleForAmazonEKSNodegroup" {
  aws_service_name = "eks-nodegroup.amazonaws.com"
}