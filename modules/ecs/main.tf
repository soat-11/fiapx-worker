# 1. Cluster ECS
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
}

# 2. IAM Roles (Permissões)
# --- ROLE 1: EXECUTION ROLE (INFRA) --- Necessária para o ECS executar a task, acessar logs, etc.
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_name}-ecs-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" } }]
  })
}

# --- ROLE 2: Orchestrator Task Role (APP) --- Necessária para a aplicação dentro do container acessar outros serviços AWS (SQS, S3, etc.)
resource "aws_iam_role" "orchestrator_task_role" {
  name = "${var.project_name}-app-orchestrator-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "orchestrator_policy" {
  name = "${var.project_name}-orchestrator-policy"
  role = aws_iam_role.orchestrator_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Permissões para o SQS (Mensageria) [cite: 15]
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "s3:PutObject",
          "s3:GetObject"
        ]
        Effect   = "Allow"
        Resource = "*" # Idealmente passe o ARN do seu módulo SQS
      },
      {
        # Permissões para o S3 (Persistência) [cite: 35]
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = "*" # Idealmente passe o ARN do seu módulo S3
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_task_definition" "app" {
  family                   = "orchestrator-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.orchestrator_task_role.arn

  container_definitions = jsonencode([{
    name  = "orchestrator"
    image = var.image_url
    essential = true
    portMappings = [{ containerPort = var.app_port, hostPort = var.app_port }]
    environment = var.env_vars
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}"
        "awslogs-region"        = "us-east-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# 4. ECS Service (Mantém o container rodando)
resource "aws_ecs_service" "main" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2 # Escalabilidade conforme requisito 
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "orchestrator"
    container_port   = var.app_port
  }

  depends_on = [var.target_group_arn] # Garante que o Target Group do NLB esteja criado antes
}

# Security Group para a Task
resource "aws_security_group" "ecs_tasks" {
  name   = "${var.project_name}-ecs-tasks-sg"
  vpc_id = var.vpc_id
  ingress {
    protocol    = "tcp"
    from_port   = var.app_port
    to_port     = var.app_port
    cidr_blocks = ["0.0.0.0/0"] # Em produção, restrinja ao SG do NLB
  }
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 1 
}