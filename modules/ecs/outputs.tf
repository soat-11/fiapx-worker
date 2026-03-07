output "service_sg_id" {
  description = "ID do Security Group dos containers do ECS"
  value       = aws_security_group.ecs_tasks.id
}