output "target_group_arn" {
  value = aws_lb_target_group.orchestrator_tg.arn
}

output "nlb_listener_arn" {
  description = "ARN do Listener do NLB para integração com API Gateway"
  value       = aws_lb_listener.main.arn
}