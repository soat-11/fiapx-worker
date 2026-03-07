variable "vpc_id" {
  description = "ID da VPC vindo do módulo VPC"
  type        = string
}

variable "igw_id" {
  description = "ID do Internet Gateway vindo do módulo VPC"
  type        = string
}

variable "project_name" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}