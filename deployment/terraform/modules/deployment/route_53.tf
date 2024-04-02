data "aws_route53_zone" "hcl_playground_zone" {
  name         = "hcl-playground.com"
  private_zone = false
}

# TODO: the current order of operations doesn't allow for this to be provisioned until after the cluster is up and the
# loadbalancer controller does its magic
data "aws_resourcegroupstaggingapi_resources" "this" {
  resource_type_filters = ["elasticloadbalancing:loadbalancer"]
  tag_filter {
    key    = "elbv2.k8s.aws/cluster"
    values = [var.eks_cluster_name]
  }
}

data "aws_lb" "this" {
  arn = data.aws_resourcegroupstaggingapi_resources.this.resource_tag_mapping_list[0].resource_arn
}

resource "aws_route53_record" "this" {
  zone_id = aws_route53_zone
  name    = "development.hcl-playground.com"
  type    = "A"

  alias {
    name                   = data.aws_lb.this.dns_name
    zone_id                = data.aws_lb.this.zone_id
    evaluate_target_health = true
  }
}