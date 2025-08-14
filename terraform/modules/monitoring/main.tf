# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "main" {
  for_each = var.log_groups

  name              = each.value.name
  retention_in_days = each.value.retention_days

  tags = {
    Name = "${var.environment}-${each.key}-log-group"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "main" {
  for_each = var.alarms

  alarm_name          = each.value.name
  comparison_operator = each.value.comparison_operator
  evaluation_periods  = each.value.evaluation_periods
  metric_name         = each.value.metric_name
  namespace           = each.value.namespace
  period              = each.value.period
  statistic           = each.value.statistic
  threshold           = each.value.threshold
  alarm_description   = each.value.description

  dimensions = each.value.dimensions

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Name = "${var.environment}-${each.key}-alarm"
  }
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.environment}-regional-bank-alerts"

  tags = {
    Name = "${var.environment}-regional-bank-alerts"
  }
}

# SNS Topic subscription (email)
resource "aws_sns_topic_subscription" "email" {
  count     = length(var.alert_emails)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_emails[count.index]
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-regional-bank-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Glue", "FailedTaskCount", "JobName", "${var.environment}-batch-etl-job"],
            [".", "SucceededTaskCount", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Glue Job Status"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Redshift", "CPUUtilization"],
            ["AWS/Redshift", "DatabaseConnections"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Redshift Performance"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["Custom/DataQuality", "DataQualityScore"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Data Quality Score"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "ServiceName", "AWSGlue"],
            [".", ".", ".", "AmazonRedshift"],
            [".", ".", ".", "AmazonS3"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Cost Monitoring"
          period  = 86400
        }
      }
    ]
  })
}

# Data source for current region
data "aws_region" "current" {}
