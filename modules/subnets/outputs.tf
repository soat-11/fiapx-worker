output "public_subnet_ids" {
  value = [aws_subnet.public_1.id]
}

output "private_subnet_ids" {
  value = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}