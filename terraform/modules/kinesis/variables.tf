variable "environment" {
  description = "Environment name"
  type        = string
}

variable "streams" {
  description = "Kinesis streams configuration"
  type = map(object({
    name             = string
    shard_count      = number
    retention_period = number
  }))
}

variable "firehose_streams" {
  description = "Kinesis Firehose streams configuration"
  type = map(object({
    name           = string
    bucket_arn     = string
    prefix         = string
    error_prefix   = string
    buffer_size    = number
    buffer_interval = number
  }))
  default = {}
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for Firehose delivery"
  type        = string
}
