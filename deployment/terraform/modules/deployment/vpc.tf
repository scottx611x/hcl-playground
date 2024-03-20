resource "aws_vpc" "this" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true
  enable_dns_hostnames = true
}

resource "aws_subnet" "this" {
  count = 2
  vpc_id     = aws_vpc.this.id
  cidr_block = count.index == 0 ? "10.0.1.0/24" : "10.0.2.0/24"
  availability_zone = count.index == 0 ? "us-east-1a" : "us-east-1b"
}

resource "aws_internet_gateway" "my_igw" {
  vpc_id = aws_vpc.this.id
}

resource "aws_security_group" "eks_sg" {
  vpc_id = aws_vpc.this.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc_endpoint" "ec2" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.ec2"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    aws_security_group.eks_sg.id,
  ]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.ecr.api"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    aws_security_group.eks_sg.id,
  ]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.ecr.dkr"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    aws_security_group.eks_sg.id,
  ]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "sts" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.sts"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    aws_security_group.eks_sg.id,
  ]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.s3"
}