terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # Remote state in S3 with native lockfile (OpenTofu 1.10+, no DynamoDB needed).
  backend "s3" {
    bucket       = "hcl-playground-tofu-state"
    key          = "hcl-playground/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

# All resources live in us-east-1 (account 386710959426).
provider "aws" {
  region = "us-east-1"
}
