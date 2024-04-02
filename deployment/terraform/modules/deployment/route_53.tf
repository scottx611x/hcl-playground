data "aws_route53_zone" "hcl_playground_zone" {
  name         = "hcl-playground.com"
  private_zone = false
}

# TODO: the current order of operations doesn't allow for this to be provisioned until after the cluster is up and the
# loadbalancer controller does its magic
data "aws_lb" "this" {
  filter {
    name   = "tag:elbv2.k8s.aws/cluster"
    values = [var.eks_cluster_name]
  }
}

resource "aws_route53_record" "example" {
  zone_id = "<your-hosted-zone-id>"
  name    = "example.yourdomain.com"
  type    = "A"

  alias {
    name                   = data.aws_lb.this.dns_name
    zone_id                = data.aws_lb.this.zone_id
    evaluate_target_health = true
  }
}