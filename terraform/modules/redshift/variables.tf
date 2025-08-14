variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cluster_name" {
  description = "Redshift cluster name"
  type        = string
}

variable "node_type" {
  description = "Redshift node type"
  type        = string
  default     = "dc2.large"
}

variable "nodes" {
  description = "Number of Redshift nodes"
  type        = number
  default     = 2
}

variable "master_username" {
  description = "Redshift master username"
  type        = string
  default     = "admin"
}

variable "master_password" {
  description = "Redshift master password"
  type        = string
  sensitive   = true
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for Redshift"
  type        = list(string)
}

variable "security_groups" {
  description = "Security group IDs for Redshift"
  type        = list(string)
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
  default     = null
}

variable "logging_bucket" {
  description = "S3 bucket for Redshift logs"
  type        = string
  default     = null
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for data access"
  type        = string
}
