# Import blocks for the existing, hand-built footprint. Resource config is
# generated via:  tofu plan -generate-config-out=generated.tf
# These blocks are inert once imported (they just bind real resources to state).

# ── hcl-playground: compute + storage ───────────────────────────────────────
import {
  to = aws_ecr_repository.hcl_playground
  id = "hcl-playground"
}
import {
  to = aws_s3_bucket.engine_cache
  id = "hcl-playground-engine-cache"
}
import {
  to = aws_lambda_function.hcl_playground
  id = "hcl-playground"
}

# ── hcl-playground: IAM ─────────────────────────────────────────────────────
import {
  to = aws_iam_role.lambda
  id = "hcl-playground-lambda"
}
import {
  to = aws_iam_role_policy.engine_cache_s3
  id = "hcl-playground-lambda:engine-cache-s3"
}
import {
  to = aws_iam_role_policy_attachment.lambda_basic
  id = "hcl-playground-lambda/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ── hcl-playground: API Gateway (HTTP API) ──────────────────────────────────
import {
  to = aws_lambda_permission.apigw
  id = "hcl-playground/apigw-invoke"
}
import {
  to = aws_apigatewayv2_api.hcl
  id = "rpi508p8lc"
}
# NOTE: the integration, $default route, and $default stage (incl. the throttle
# settings) were created by API Gateway "quick create" (aws apigatewayv2
# create-api --target). The AWS provider refuses to import quick-create-managed
# resources, so they stay implicit and are intentionally not managed here.
import {
  to = aws_apigatewayv2_domain_name.hcl
  id = "hcl-playground.com"
}
import {
  to = aws_apigatewayv2_api_mapping.hcl
  id = "tha233/hcl-playground.com"
}

# ── hcl-playground: cert + DNS ──────────────────────────────────────────────
import {
  to = aws_acm_certificate.hcl
  id = "arn:aws:acm:us-east-1:386710959426:certificate/80d95123-56ca-484b-a749-ade91b3dcb53"
}
import {
  to = aws_route53_zone.hcl_playground
  id = "Z035277814CFDYM8JZZ2D"
}
import {
  to = aws_route53_record.hcl_apex
  id = "Z035277814CFDYM8JZZ2D_hcl-playground.com_A"
}
import {
  to = aws_route53_record.hcl_acm_validation
  id = "Z035277814CFDYM8JZZ2D__5f2a4095eaaf763cc36bc3256ed26025.hcl-playground.com_CNAME"
}

# ── guardrail ───────────────────────────────────────────────────────────────
import {
  to = aws_budgets_budget.guardrail
  id = "386710959426:hcl-playground-guardrail"
}

# ── duckoducko DNS (record only; the scott-ouellette.com zone is not managed here) ──
import {
  to = aws_route53_record.duckoducko
  id = "Z8JRI6C2BS8FM_duckoducko.scott-ouellette.com_CNAME"
}
