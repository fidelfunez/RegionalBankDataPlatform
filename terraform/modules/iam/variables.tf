variable "environment" {
  description = "Environment name"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for data access"
  type        = string
}

variable "kinesis_stream_arns" {
  description = "Kinesis stream ARNs"
  type        = list(string)
  default     = []
}

variable "redshift_cluster_arn" {
  description = "Redshift cluster ARN"
  type        = string
  default     = ""
}
