variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "project_name" {
  type = string
}

variable "app_port" {
  type    = number
  default = 3000
}

variable "ecs_sg_id" {
  type    = string
  description = "ID do Security Group dos containers do ECS"
}