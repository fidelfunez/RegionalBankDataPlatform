output "bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.data_lake.bucket
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.data_lake.arn
}

output "bucket_id" {
  description = "S3 bucket ID"
  value       = aws_s3_bucket.data_lake.id
}
