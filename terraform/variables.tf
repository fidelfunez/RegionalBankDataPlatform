variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "redshift_node_type" {
  description = "Redshift node type"
  type        = string
  default     = "dc2.large"
}

variable "redshift_nodes" {
  description = "Number of Redshift nodes"
  type        = number
  default     = 2
  
  validation {
    condition     = var.redshift_nodes >= 1 && var.redshift_nodes <= 16
    error_message = "Redshift nodes must be between 1 and 16."
  }
}

variable "kinesis_shard_count" {
  description = "Default number of shards for Kinesis streams"
  type        = number
  default     = 2
  
  validation {
    condition     = var.kinesis_shard_count >= 1
    error_message = "Kinesis shard count must be at least 1."
  }
}

variable "glue_job_timeout" {
  description = "Timeout for Glue jobs in minutes"
  type        = number
  default     = 2880
  
  validation {
    condition     = var.glue_job_timeout >= 1 && var.glue_job_timeout <= 2880
    error_message = "Glue job timeout must be between 1 and 2880 minutes."
  }
}

variable "data_retention_days" {
  description = "Data retention period in days"
  type        = number
  default     = 2555 # 7 years
  
  validation {
    condition     = var.data_retention_days >= 1
    error_message = "Data retention days must be at least 1."
  }
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
