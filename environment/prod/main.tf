terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use remote backend
  # backend "s3" {
  #   bucket         = "fiapx-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "FIAP-X"
      ManagedBy   = "Terraform"
      Workspace   = terraform.workspace
    }
  }
}

# Import root-level providers and modules
# This file uses the same provider and modules as the root
# Production-specific variable overrides can be done via terraform.prod.tfvars
