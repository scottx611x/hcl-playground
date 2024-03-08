data "aws_route53_zone" "hcl_playground_zone" {
  name         = "hcl-playground.com"
  private_zone = false
}

resource "aws_route53_record" "this" {
  zone_id = data.aws_route53_zone.hcl_playground_zone.zone_id
  name    = "${var.subdomain}.hcl-playground.com"
  type    = "A"

  alias {
    name                   = aws_lb.this.dns_name
    zone_id                = aws_lb.this.zone_id
    evaluate_target_health = true
  }
}