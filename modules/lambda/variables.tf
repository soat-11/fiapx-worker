variable "artifact_bucket_id" {
  type        = string
  description = "ID do bucket S3 onde estão os ZIPs"
}

variable "s3_key" {
  type        = string
  description = "Caminho do ZIP no S3 (ex: auth-v1.zip)"
}

variable "cognito_user_pool_arn" {
  type = string
  description = "ARN do Cognito"
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_app_client_id" {
  type = string
}