terraform {
  backend "s3" {
    bucket = "hcl-playground"
    key    = "development"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
}

# module "deployment" {
#   source           = "../modules/deployment"
#   ecr_repo_name    = "hcl-playground-development"
#   eks_cluster_name = "hcl-playground-development"
#   ssl_cert_arn     = "arn:aws:acm:us-east-1:386710959426:certificate/e4698b03-63d5-4133-a18a-7b692a41afd9"
#   subdomain        = "development"
# }
