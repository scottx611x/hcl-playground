# __generated__ by OpenTofu
# Please review these resources and move them into your main configuration files.

# __generated__ by OpenTofu from "hcl-playground-lambda/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = "hcl-playground-lambda"
}

# __generated__ by OpenTofu from "hcl-playground.com"
resource "aws_apigatewayv2_domain_name" "hcl" {
  domain_name = "hcl-playground.com"
  tags        = {}
  tags_all    = {}
  domain_name_configuration {
    certificate_arn                        = "arn:aws:acm:us-east-1:386710959426:certificate/80d95123-56ca-484b-a749-ade91b3dcb53"
    endpoint_type                          = "REGIONAL"
    ip_address_type                        = "ipv4"
    security_policy                        = "TLS_1_2"
  }
}

# __generated__ by OpenTofu from "hcl-playground"
resource "aws_ecr_repository" "hcl_playground" {
  force_delete         = null
  image_tag_mutability = "MUTABLE"
  name                 = "hcl-playground"
  tags                 = {}
  tags_all             = {}
  encryption_configuration {
    encryption_type = "AES256"
  }
  image_scanning_configuration {
    scan_on_push = false
  }
}

# __generated__ by OpenTofu from "tha233/hcl-playground.com"
resource "aws_apigatewayv2_api_mapping" "hcl" {
  api_id          = "rpi508p8lc"
  domain_name     = "hcl-playground.com"
  stage           = "$default"
}

# __generated__ by OpenTofu
resource "aws_route53_record" "hcl_apex" {
  allow_overwrite                  = null
  name                             = "hcl-playground.com"
  type                             = "A"
  zone_id                          = "Z035277814CFDYM8JZZ2D"
  alias {
    evaluate_target_health = false
    name                   = "d-d4cvb45nh5.execute-api.us-east-1.amazonaws.com"
    zone_id                = "Z1UJRXOUMOOFQ8"
  }
}

# __generated__ by OpenTofu
resource "aws_iam_role_policy" "engine_cache_s3" {
  name        = "engine-cache-s3"
  policy = jsonencode({
    Statement = [{
      Action   = ["s3:GetObject", "s3:PutObject"]
      Effect   = "Allow"
      Resource = "arn:aws:s3:::hcl-playground-engine-cache/engines/*"
    }]
    Version = "2012-10-17"
  })
  role = "hcl-playground-lambda"
}

# __generated__ by OpenTofu from "Z8JRI6C2BS8FM_duckoducko.scott-ouellette.com_CNAME"
resource "aws_route53_record" "duckoducko" {
  allow_overwrite                  = null
  name                             = "duckoducko.scott-ouellette.com"
  records                          = ["scottx611x.github.io"]
  ttl                              = 300
  type                             = "CNAME"
  zone_id                          = "Z8JRI6C2BS8FM"
}

# __generated__ by OpenTofu from "Z035277814CFDYM8JZZ2D"
resource "aws_route53_zone" "hcl_playground" {
  comment           = ""
  force_destroy     = null
  name              = "hcl-playground.com"
  tags              = {}
  tags_all          = {}
}

# __generated__ by OpenTofu
resource "aws_apigatewayv2_api" "hcl" {
  api_key_selection_expression = "$request.header.x-api-key"
  body                         = null
  credentials_arn              = null
  disable_execute_api_endpoint = false
  fail_on_warnings             = null
  ip_address_type              = "ipv4"
  name                         = "hcl-playground"
  protocol_type                = "HTTP"
  route_key                    = null
  route_selection_expression   = "$request.method $request.path"
  tags                         = {}
  tags_all                     = {}
  target                       = null
}

# __generated__ by OpenTofu
resource "aws_iam_role" "lambda" {
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
  force_detach_policies = false
  max_session_duration  = 3600
  name                  = "hcl-playground-lambda"
  path                  = "/"
  tags                  = {}
  tags_all              = {}
}

# __generated__ by OpenTofu from "Z035277814CFDYM8JZZ2D__5f2a4095eaaf763cc36bc3256ed26025.hcl-playground.com_CNAME"
resource "aws_route53_record" "hcl_acm_validation" {
  allow_overwrite                  = null
  name                             = "_5f2a4095eaaf763cc36bc3256ed26025.hcl-playground.com"
  records                          = ["_d7fe7e4e3df71712f35d9ff34d5852eb.wdrzrjwmwn.acm-validations.aws."]
  ttl                              = 300
  type                             = "CNAME"
  zone_id                          = "Z035277814CFDYM8JZZ2D"
}

# __generated__ by OpenTofu
resource "aws_acm_certificate" "hcl" {
  certificate_body          = null
  certificate_chain         = null
  domain_name               = "hcl-playground.com"
  key_algorithm             = "RSA_2048"
  private_key               = null # sensitive
  subject_alternative_names = ["hcl-playground.com"]
  tags                      = {}
  tags_all                  = {}
  validation_method         = "DNS"
  options {
    certificate_transparency_logging_preference = "ENABLED"
  }
}

# __generated__ by OpenTofu
resource "aws_lambda_permission" "apigw" {
  action                 = "lambda:InvokeFunction"
  event_source_token     = null
  function_name          = "hcl-playground"
  function_url_auth_type = null
  principal              = "apigateway.amazonaws.com"
  principal_org_id       = null
  source_account         = null
  source_arn             = "arn:aws:execute-api:us-east-1:386710959426:rpi508p8lc/*/*"
  statement_id           = "apigw-invoke"
}

# __generated__ by OpenTofu
resource "aws_s3_bucket" "engine_cache" {
  bucket              = "hcl-playground-engine-cache"
  force_destroy       = null
  object_lock_enabled = false
  tags                = {}
  tags_all            = {}
}

# __generated__ by OpenTofu
resource "aws_lambda_function" "hcl_playground" {
  architectures                      = ["arm64"]
  filename                           = null
  function_name                      = "hcl-playground"
  image_uri                          = "386710959426.dkr.ecr.us-east-1.amazonaws.com/hcl-playground:latest"
  layers                             = []
  memory_size                        = 3008
  package_type                       = "Image"
  publish                            = null
  replace_security_groups_on_destroy = null
  replacement_security_group_ids     = null
  reserved_concurrent_executions     = 5
  role                               = "arn:aws:iam::386710959426:role/hcl-playground-lambda"
  s3_bucket                          = null
  s3_key                             = null
  s3_object_version                  = null
  skip_destroy                       = false
  tags                               = {}
  tags_all                           = {}
  timeout                            = 30
  environment {
    variables = {
      AWS_LWA_READINESS_CHECK_PATH = "/health"
      HCL_CACHE_BUCKET             = "hcl-playground-engine-cache"
      HCL_RUNTIME_ROOT             = "/tmp/hcl-engines"
      HCL_SCRATCH_DIR              = "/tmp"
    }
  }
  ephemeral_storage {
    size = 1024
  }
  logging_config {
    log_format            = "Text"
    log_group             = "/aws/lambda/hcl-playground"
  }
  tracing_config {
    mode = "PassThrough"
  }
}

# __generated__ by OpenTofu
resource "aws_budgets_budget" "guardrail" {
  account_id        = "386710959426"
  budget_type       = "COST"
  limit_amount      = "20.0"
  limit_unit        = "USD"
  name              = "hcl-playground-guardrail"
  tags              = {}
  tags_all          = {}
  time_period_end   = "2087-06-15_00:00"
  time_period_start = "2026-06-01_00:00"
  time_unit         = "MONTHLY"
  cost_types {
    include_credit             = true
    include_discount           = true
    include_other_subscription = true
    include_recurring          = true
    include_refund             = true
    include_subscription       = true
    include_support            = true
    include_tax                = true
    include_upfront            = true
    use_amortized              = false
    use_blended                = false
  }
  notification {
    comparison_operator        = "GREATER_THAN"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["scottx611x@gmail.com"]
    subscriber_sns_topic_arns  = []
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
  }
  notification {
    comparison_operator        = "GREATER_THAN"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["scottx611x@gmail.com"]
    subscriber_sns_topic_arns  = []
    threshold                  = 90
    threshold_type             = "PERCENTAGE"
  }
  notification {
    comparison_operator        = "GREATER_THAN"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["scottx611x@gmail.com"]
    subscriber_sns_topic_arns  = []
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
  }
}

