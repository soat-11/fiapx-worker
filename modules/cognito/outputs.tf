output "user_pool_id" {
  value       = aws_cognito_user_pool.this.id
  description = "ID do User Pool criado"
}

output "app_client_id" {
  value       = aws_cognito_user_pool_client.this.id
  description = "ID do Client App para a aplicação"
}

output "user_pool_arn" {
  value = aws_cognito_user_pool.this.arn
}

output "user_pool_endpoint" {
  value = "https://${aws_cognito_user_pool.this.endpoint}"
}