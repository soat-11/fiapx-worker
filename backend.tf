terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  
  # Uncomment and configure for production
  # backend "s3" {
  #   bucket = "fiapx-hackaton-ep"
  #   key    = "terraform.state"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "FIAP-X"
      ManagedBy   = "Terraform"
    }
  }
}

provider "random" {}
