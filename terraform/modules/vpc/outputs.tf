output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "redshift_security_group_id" {
  description = "Redshift security group ID"
  value       = aws_security_group.redshift.id
}

output "glue_security_group_id" {
  description = "Glue security group ID"
  value       = aws_security_group.glue.id
}

output "airflow_security_group_id" {
  description = "Airflow security group ID"
  value       = aws_security_group.airflow.id
}
