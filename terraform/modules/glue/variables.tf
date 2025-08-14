variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for Glue jobs"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for Glue jobs"
  type        = list(string)
}

variable "security_groups" {
  description = "Security group IDs for Glue jobs"
  type        = list(string)
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for data access"
  type        = string
}

variable "crawlers" {
  description = "Glue crawlers configuration"
  type = map(object({
    name     = string
    s3_path  = string
    schedule = string
  }))
  default = {}
}

variable "glue_jobs" {
  description = "Glue jobs configuration"
  type = map(object({
    name                 = string
    script_path         = string
    max_retries         = number
    timeout             = number
    number_of_workers   = number
    worker_type         = string
    max_capacity        = number
    max_concurrent_runs = number
    default_arguments   = map(string)
  }))
}
