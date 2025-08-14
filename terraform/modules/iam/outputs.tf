output "airflow_role_arn" {
  description = "Airflow IAM role ARN"
  value       = aws_iam_role.airflow_role.arn
}

output "lambda_role_arn" {
  description = "Lambda IAM role ARN"
  value       = aws_iam_role.lambda_role.arn
}

output "data_engineer_user_name" {
  description = "Data engineer IAM user name"
  value       = aws_iam_user.data_engineer.name
}
