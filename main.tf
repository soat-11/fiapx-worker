module "s3" {
  source      = "./modules/s3"
}

module "cognito" {
  source      = "./modules/cognito"
  pool_name   = "auth-service"
  environment = var.environment
}

module "auth_lambdas" {
  source             = "./modules/lambda"
  artifact_bucket_id = module.s3.bucket_id
  s3_key            = "lambda.zip"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_app_client_id = module.cognito.app_client_id
  cognito_user_pool_id = module.cognito.user_pool_id
}

module "api_gateway" {
  source                = "./modules/api-gateway"
  api_name              = "fiapx-api-${var.environment}"
  
  # Passando os ARNs das lambdas que vieram do módulo lambda
  lambda_signup_arn     = module.auth_lambdas.signup_invoke_arn
  lambda_login_arn      = module.auth_lambdas.login_invoke_arn
  
  # Necessário para as permissões de invocação (permission.tf)
  lambda_signup_name    = module.auth_lambdas.signup_function_name
  lambda_login_name     = module.auth_lambdas.login_function_name

  cognito_app_client_id          = module.cognito.app_client_id
  cognito_user_pool_id           = module.cognito.user_pool_id
  aws_region                     = var.aws_region

  depends_on = [ module.s3 ]
}