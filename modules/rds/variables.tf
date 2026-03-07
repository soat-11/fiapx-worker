variable "project_name" {
    description = "Nome do projeto para prefixar recursos"
    type        = string
}

variable "private_subnet_ids" {
    type        = list(string)
}

variable "vpc_id" {
  type = string
}

variable "ecs_sg_id" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type = string
}