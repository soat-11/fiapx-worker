# Função 1: Cadastro
resource "aws_lambda_function" "signup" {
  function_name = "signup"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = "nodejs18.x"

  s3_bucket = var.artifact_bucket_id
  s3_key    = var.s3_key
  
  handler   = "signup.handler" 

  environment {
    variables = {
      COGNITO_USER_POOL_ID  = var.cognito_user_pool_id
      COGNITO_APP_CLIENT_ID = var.cognito_app_client_id
    }
  }
}

# Função 2: Login
resource "aws_lambda_function" "login" {
  function_name = "login"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = "nodejs18.x"

  s3_bucket = var.artifact_bucket_id
  s3_key    = var.s3_key
  handler   = "login.handler"

  environment {
    variables = {
      COGNITO_USER_POOL_ID  = var.cognito_user_pool_id
      COGNITO_APP_CLIENT_ID = var.cognito_app_client_id
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "auth_lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_cognito_admin" {
  name = "lambda_cognito_admin_access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "cognito-idp:SignUp",
        "cognito-idp:AdminConfirmSignUp",
        "cognito-idp:AdminUpdateUserAttributes"
      ]
      Effect   = "Allow"
      Resource = var.cognito_user_pool_arn
    }]
  })
}