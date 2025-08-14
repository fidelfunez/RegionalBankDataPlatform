output "catalog_database_name" {
  description = "Glue catalog database name"
  value       = aws_glue_catalog_database.main.name
}

output "crawler_names" {
  description = "Glue crawler names"
  value       = [for crawler in aws_glue_crawler.main : crawler.name]
}

output "job_names" {
  description = "Glue job names"
  value       = [for job in aws_glue_job.main : job.name]
}

output "glue_role_arn" {
  description = "Glue service role ARN"
  value       = aws_iam_role.glue_role.arn
}
