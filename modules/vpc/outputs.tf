output "vpc_id" {
  description = "ID da VPC criada"
  value       = aws_vpc.main.id
}

output "igw_id" {
  description = "ID do Internet Gateway"
  value       = aws_internet_gateway.igw.id
}