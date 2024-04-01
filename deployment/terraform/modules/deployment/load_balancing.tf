# Load Balancer and Target Group for HTTPS
resource "aws_lb" "this" {
  name               = "hcl-playground-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.eks_sg.id]
  subnets            = aws_subnet.this[*].id
}

resource "aws_lb_target_group" "this" {
  name     = "hcl-playground-tg"
  port     = 443
  protocol = "HTTPS"
  vpc_id   = aws_vpc.this.id
  target_type = "ip"
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      protocol   = "HTTPS"
      port       = "443"
      status_code = "HTTP_301"
    }
  }
}


# Assuming you have an SSL certificate managed by AWS Certificate Manager (ACM)
resource "aws_lb_listener" "this" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.ssl_cert_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}