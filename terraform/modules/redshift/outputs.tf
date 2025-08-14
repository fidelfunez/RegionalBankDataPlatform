output "cluster_id" {
  description = "Redshift cluster ID"
  value       = aws_redshift_cluster.main.cluster_identifier
}

output "endpoint" {
  description = "Redshift cluster endpoint"
  value       = aws_redshift_cluster.main.endpoint
}

output "port" {
  description = "Redshift cluster port"
  value       = aws_redshift_cluster.main.port
}

output "database_name" {
  description = "Redshift database name"
  value       = aws_redshift_cluster.main.database_name
}

output "cluster_arn" {
  description = "Redshift cluster ARN"
  value       = aws_redshift_cluster.main.arn
}

output "iam_role_arn" {
  description = "Redshift IAM role ARN"
  value       = aws_iam_role.redshift_s3.arn
}
