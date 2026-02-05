resource "aws_cognito_user_pool" "this" {
  name = "${var.pool_name}-${var.environment}"

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
  }
}

resource "aws_cognito_user_pool_client" "this" {
  name         = "${var.pool_name}-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.this.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_CUSTOM_AUTH"
  ]

  generate_secret = false
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.pool_name}-${var.environment}-auth"
  user_pool_id = aws_cognito_user_pool.this.id
}