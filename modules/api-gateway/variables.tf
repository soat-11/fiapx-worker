variable "api_name" { type = string }

# ARNs para Integração
variable "lambda_signup_arn" { type = string }
variable "lambda_login_arn" { type = string }

# Nomes para Permissão
variable "lambda_signup_name" { type = string }
variable "lambda_login_name" { type = string }
variable "cognito_app_client_id" { type = string }
variable "cognito_user_pool_id" { type = string }
variable "aws_region" { type = string }