variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "log_groups" {
  description = "CloudWatch log groups configuration"
  type = map(object({
    name             = string
    retention_days   = number
  }))
  default = {}
}

variable "alarms" {
  description = "CloudWatch alarms configuration"
  type = map(object({
    name                = string
    metric_name         = string
    namespace           = string
    statistic           = string
    period              = number
    threshold           = number
    comparison_operator = string
    evaluation_periods  = number
    description         = string
    dimensions          = list(map(string))
  }))
  default = {}
}

variable "alert_emails" {
  description = "Email addresses for alert notifications"
  type        = list(string)
  default     = []
}
