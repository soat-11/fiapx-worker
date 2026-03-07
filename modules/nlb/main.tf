# --- Network Load Balancer (Interno) ---
resource "aws_lb" "main" {
  name               = "${var.project_name}-nlb"
  internal           = true # Mantém a aplicação isolada da internet direta
  load_balancer_type = "network"
  subnets            = var.private_subnet_ids

  tags = { Name = "${var.project_name}-nlb" }
}

# --- Target Group ---
# Define para onde o tráfego deve ir (os containers do Orchestrator)
resource "aws_lb_target_group" "orchestrator_tg" {
  name        = "${var.project_name}-tg"
  port        = var.app_port
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled  = true
    protocol = "TCP"
    port     = var.app_port
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
  }
}

# --- Listener ---
resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.orchestrator_tg.arn
  }
}

# VPC Link para HTTP API (v2)
resource "aws_apigatewayv2_vpc_link" "main" {
  name               = "${var.project_name}-http-vpc-link"
  security_group_ids = [var.ecs_sg_id]
  subnet_ids         = var.private_subnet_ids

  tags = { Name = "${var.project_name}-vpc-link" }
}