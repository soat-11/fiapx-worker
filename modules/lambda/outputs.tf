output "signup_invoke_arn" {
  value = aws_lambda_function.signup.invoke_arn
}

output "login_invoke_arn" {
  value = aws_lambda_function.login.invoke_arn
}

output "signup_function_name" {
  value = aws_lambda_function.signup.function_name
}

output "login_function_name" {
  value = aws_lambda_function.login.function_name
}