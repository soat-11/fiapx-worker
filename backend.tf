terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.30"
    }
  }
  backend "s3" {
    bucket = "fiapx-hackaton-ep"
    key = "terraform.state"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
  profile = "fiapx"
}