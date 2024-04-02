terraform {
  backend "s3" {
    bucket = "hcl-playground"
    key    = "production"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
}