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
  map_public_ip_on_launch = true

  tags = {
    kubernetes.io/role/elb = "1"
  }
}

resource "aws_internet_gateway" "my_igw" {
  vpc_id = aws_vpc.this.id
}

resource "aws_route_table" "eks_route_table" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.my_igw.id
  }
}

resource "aws_route_table_association" "eks_rta" {
  count          = length(aws_subnet.this)
  subnet_id      = aws_subnet.this[count.index].id
  route_table_id = aws_route_table.eks_route_table.id
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
  subnet_ids = aws_subnet.this[*].id
  private_dns_enabled = true
}
resource "aws_vpc_endpoint_policy" "ec2" {
  vpc_endpoint_id = aws_vpc_endpoint.ec2.id
}

resource "aws_vpc_endpoint" "ecr" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.ecr.api"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    aws_security_group.eks_sg.id,
  ]
  subnet_ids = aws_subnet.this[*].id
  private_dns_enabled = true
}
resource "aws_vpc_endpoint_policy" "ecr" {
  vpc_endpoint_id = aws_vpc_endpoint.ecr.id
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.ecr.dkr"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    aws_security_group.eks_sg.id,
  ]
  subnet_ids = aws_subnet.this[*].id
  private_dns_enabled = true
}
resource "aws_vpc_endpoint_policy" "ecr_dkr" {
  vpc_endpoint_id = aws_vpc_endpoint.ecr_dkr.id
}

resource "aws_vpc_endpoint" "sts" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.sts"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    aws_security_group.eks_sg.id,
  ]
  subnet_ids = aws_subnet.this[*].id
  private_dns_enabled = true
}
resource "aws_vpc_endpoint_policy" "sts" {
  vpc_endpoint_id = aws_vpc_endpoint.sts.id
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.this.id
  service_name = "com.amazonaws.us-east-1.s3"
}
resource "aws_vpc_endpoint_policy" "s3" {
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
}