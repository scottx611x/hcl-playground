terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

# All resources live in us-east-1 (account 386710959426).
provider "aws" {
  region = "us-east-1"
}
