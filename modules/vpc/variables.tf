variable "project_name" {
  description = "Nome do projeto para identificação [cite: 1]"
  type        = string
}

variable "vpc_cidr" {
  description = "Bloco CIDR da VPC"
  type        = string
  default     = "10.0.0.0/16"
}