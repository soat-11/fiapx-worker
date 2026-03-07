# A API propriamente dita
resource "aws_apigatewayv2_api" "this" {
  name          = var.api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET", "PUT", "OPTIONS"]
    allow_headers = ["content-type", "authorization", "x-user-id"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.this.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-authorizer"

  jwt_configuration {
    audience = [var.cognito_app_client_id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.cognito_user_pool_id}"
  }
}

# O "Estágio" (Stage) - necessário para publicar a API
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true
}

# --- INTEGRAÇÕES (Conexão API <-> Lambda) ---

resource "aws_apigatewayv2_integration" "signup" {
  api_id           = aws_apigatewayv2_api.this.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.lambda_signup_arn
}

resource "aws_apigatewayv2_integration" "login" {
  api_id           = aws_apigatewayv2_api.this.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.lambda_login_arn
}

# --- ROTAS (Endpoints) ---

resource "aws_apigatewayv2_route" "signup" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /auth/signup"
  target    = "integrations/${aws_apigatewayv2_integration.signup.id}"
}

resource "aws_apigatewayv2_route" "login" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /auth/login"
  target    = "integrations/${aws_apigatewayv2_integration.login.id}"
}


# --- permissões ---
resource "aws_lambda_permission" "signup" {
  statement_id  = "AllowAPIGatewaySignupV2"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_signup_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

resource "aws_lambda_permission" "login" {
  statement_id  = "AllowAPIGatewayLoginV2"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_login_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# --- orchestrator ---
resource "aws_apigatewayv2_vpc_link" "orchestrator_vpc_link" {
  name               = "${var.api_name}-vpc-link"
  security_group_ids = var.vpc_link_sg_ids
  subnet_ids         = var.private_subnet_ids

  tags = {
    Name = "${var.api_name}-vpc-link"
  }
}

resource "aws_apigatewayv2_integration" "orchestrator_integration" {
  api_id           = aws_apigatewayv2_api.this.id
  integration_type = "HTTP_PROXY"
  integration_uri  = var.nlb_listener_arn
  integration_method = "ANY"
  
  connection_type = "VPC_LINK"
  connection_id   = aws_apigatewayv2_vpc_link.orchestrator_vpc_link.id
  
  payload_format_version = "1.0"
  
  request_parameters = {
    "overwrite:header.x-user-id" = "$context.authorizer.claims.sub"
  }
}

resource "aws_apigatewayv2_route" "create_video" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /videos"
  target    = "integrations/${aws_apigatewayv2_integration.orchestrator_integration.id}"

  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "list_videos" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /videos"
  target    = "integrations/${aws_apigatewayv2_integration.orchestrator_integration.id}"

  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}