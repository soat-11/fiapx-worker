module "s3" {
  source = "./modules/s3"
  project_name = var.project_name
}

module "sqs" {
  source = "./modules/sqs"
  project_name = var.project_name
}

module "vpc" {
  source       = "./modules/vpc"
  project_name = var.project_name
  vpc_cidr     = "10.0.0.0/16"
}

module "subnets" {
  source       = "./modules/subnets"
  vpc_id       = module.vpc.vpc_id
  igw_id       = module.vpc.igw_id
  project_name = var.project_name
  aws_region   = var.aws_region
}

module "nlb" {
  source             = "./modules/nlb"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.subnets.private_subnet_ids
  project_name       = var.project_name
  app_port           = 3000
  ecs_sg_id         = module.ecs.service_sg_id
}

module "db" {
  source             = "./modules/rds"
  project_name       = var.project_name
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.subnets.private_subnet_ids
  ecs_sg_id          = module.ecs.service_sg_id 
  db_name            = var.db_name
  db_user            = var.db_user
  db_password        = var.db_password
}

module "ecs" {
  source             = "./modules/ecs"
  project_name       = var.project_name
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.subnets.private_subnet_ids
  target_group_arn   = module.nlb.target_group_arn
  image_url          = var.orchestrator_image_url
  app_port           = 3000
  
  env_vars = [
    { name = "AWS_S3_BUCKET_RAW", value = module.s3.upload_bucket_id },
    { name = "AWS_SQS_UPLOAD_QUEUE_URL", value = module.sqs.queue_url_upload_video },
    { name = "AWS_SQS_PROCESSING_QUEUE_URL", value = module.sqs.queue_url_processing_video },
    { name = "AWS_SQS_RESULT_QUEUE_URL", value = module.sqs.queue_url_concluded_video },
    { name = "AWS_SQS_EMAIL_QUEUE_URL", value = module.sqs.queue_url_email_notification },
    { name = "AWS_REGION",    value = var.aws_region },
    { name = "DB_HOST",    value = module.db.db_instance_endpoint },
    { name = "DB_PORT",    value = "5432" },
    { name = "DB_NAME",    value = var.db_name },
    { name = "DB_USER",    value = var.db_user },
    { name = "DB_PASSWORD",    value = var.db_password },
    { name = "PORT",    value = 3000 }
  ]
}

module "cognito" {
  source      = "./modules/cognito"
  pool_name   = "auth-service"
  environment = var.environment
}

module "auth_lambdas" {
  source                = "./modules/lambda"
  artifact_bucket_id    = module.s3.bucket_id
  s3_key                = "auth-service.zip"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_app_client_id = module.cognito.app_client_id
  cognito_user_pool_id  = module.cognito.user_pool_id

  depends_on = [module.s3]
}

module "api_gateway" {
  source   = "./modules/api-gateway"
  api_name = "fiapx-api-${var.environment}"

  # Passando os ARNs das lambdas que vieram do módulo lambda
  lambda_signup_arn = module.auth_lambdas.signup_invoke_arn
  lambda_login_arn  = module.auth_lambdas.login_invoke_arn

  # Necessário para as permissões de invocação (permission.tf)
  lambda_signup_name = module.auth_lambdas.signup_function_name
  lambda_login_name  = module.auth_lambdas.login_function_name

  cognito_app_client_id = module.cognito.app_client_id
  cognito_user_pool_id  = module.cognito.user_pool_id
  aws_region            = var.aws_region

  vpc_link_sg_ids    = [module.ecs.service_sg_id]
  private_subnet_ids = module.subnets.private_subnet_ids
  nlb_listener_arn = module.nlb.nlb_listener_arn

  depends_on = [module.s3]
}