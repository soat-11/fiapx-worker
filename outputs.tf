output "api_endpoint" {
  description = "URL base do API Gateway para os endpoints de Auth"
  value       = module.api_gateway.api_url
}