variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"
}

# VPC Configuration
variable "project_name" {
  description = "Nome do projeto para identificação dos recursos"
  type        = string
  default     = "fiapx-project"
}

variable "orchestrator_image_url" {
  description = "URL da imagem do orchestrator no ECR"
  type        = string
}

variable "db_name" {
  description = "Nome do banco de dados"
}

variable "db_user" {
  description = "Nome do usuário do banco de dados"
}

variable "db_password" {
  description = "Senha do usuário do banco de dados"
}