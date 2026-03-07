# Production Environment Variables
# These override the defaults from the root variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnet egress"
  type        = bool
  default     = true
}

variable "ecs_task_cpu" {
  description = "Task CPU units - Production optimized to 256 for cost"
  type        = number
  default     = 256
}

variable "ecs_task_memory" {
  description = "Task memory in MB - Production optimized to 512 for cost"
  type        = number
  default     = 512
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks - 1 for off-peak, scales to 2-3 with traffic"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks for auto-scaling"
  type        = number
  default     = 3
}

variable "rds_instance_class" {
  description = "RDS instance class - t3.micro for cost optimization"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage for RDS auto-scaling"
  type        = number
  default     = 100
}

variable "rds_db_name" {
  description = "Database name"
  type        = string
  default     = "fiapxdb"
}

variable "rds_backup_retention_days" {
  description = "Number of days to retain RDS backups - 7 days for production"
  type        = number
  default     = 7
}

variable "alerts_email" {
  description = "Email for CloudWatch alerts"
  type        = string
  default     = "ops@fiapx.local"
}

variable "log_retention_days" {
  description = "CloudWatch log retention - 7 days for production"
  type        = number
  default     = 7
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Environment = "prod"
    Project     = "FIAP-X"
    ManagedBy   = "Terraform"
  }
}
