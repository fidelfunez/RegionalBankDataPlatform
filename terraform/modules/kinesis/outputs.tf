output "stream_names" {
  description = "Kinesis stream names"
  value       = [for stream in aws_kinesis_stream.main : stream.name]
}

output "stream_arns" {
  description = "Kinesis stream ARNs"
  value       = [for stream in aws_kinesis_stream.main : stream.arn]
}

output "firehose_stream_names" {
  description = "Kinesis Firehose stream names"
  value       = [for stream in aws_kinesis_firehose_delivery_stream.s3 : stream.name]
}

output "firehose_role_arn" {
  description = "Firehose IAM role ARN"
  value       = aws_iam_role.firehose_role.arn
}
