variable "env_vars" {
  type = list(object({
    name  = string
    value = string
  }))
  description = "Lista de variáveis de ambiente para o container"
}

variable "project_name" {
  type        = string
  description = "Nome do projeto para prefixar recursos"
}

variable "vpc_id" {
  type = string
  description = "ID da VPC"
}

variable "private_subnet_ids" {
  type = list(string)
  description = "IDs das subnets privadas para os serviços" 
}

variable "target_group_arn" {
  type = string
  description = "ARN do Target Group do NLB"
}

variable "app_port" {
  type        = number
  description = "Porta que a aplicação no container irá expor"
}

variable "image_url" {
  type = string
  description = "URL da imagem Docker (ECR ou DockerHub)"
}