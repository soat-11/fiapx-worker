# 1. Grupo de Subnets para o RDS (deve usar as subnets privadas)
resource "aws_db_subnet_group" "postgres" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = { Name = "${var.project_name}-db-subnet-group" }
}

# 2. Security Group do Banco de Dados
resource "aws_security_group" "postgres_sg" {
  name        = "${var.project_name}-postgres-sg"
  description = "Permite acesso apenas do Orchestrator"
  vpc_id      = var.vpc_id

  # Regra de Entrada: Porta 5432 vinda apenas do SG do ECS
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_sg_id] # O SG que isolamos anteriormente
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. Instância do Banco de Dados (Postgres)
resource "aws_db_instance" "postgres" {
  identifier           = "${var.project_name}-db"
  engine               = "postgres"
  engine_version       = "15" # Versão estável
  instance_class       = "db.t3.micro" # Nível gratuito/econômico
  allocated_storage    = 20
  db_name              = var.db_name
  username             = var.db_user
  password             = var.db_password # Use uma variável sensível
  db_subnet_group_name = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.postgres_sg.id]
  skip_final_snapshot  = true # Apenas para fins de desenvolvimento/estudo
  publicly_accessible  = false # Segurança: Banco não fica exposto na internet
}