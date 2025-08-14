# Glue Catalog Database
resource "aws_glue_catalog_database" "main" {
  name = "${var.environment}-regional-bank-catalog"
  
  description = "Glue catalog database for Regional Bank data platform"
  
  tags = {
    Name = "${var.environment}-regional-bank-catalog"
  }
}

# Glue Crawler
resource "aws_glue_crawler" "main" {
  for_each = var.crawlers

  name          = each.value.name
  database_name = aws_glue_catalog_database.main.name
  role          = aws_iam_role.glue_role.arn

  s3_target {
    path = each.value.s3_path
  }

  schedule = each.value.schedule

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" }
    }
  })

  tags = {
    Name = "${var.environment}-${each.key}-crawler"
  }
}

# Glue Jobs
resource "aws_glue_job" "main" {
  for_each = var.glue_jobs

  name     = each.value.name
  role_arn = aws_iam_role.glue_role.arn

  command {
    script_location = each.value.script_path
    python_version  = "3"
  }

  max_retries = each.value.max_retries
  timeout     = each.value.timeout

  number_of_workers       = each.value.number_of_workers
  worker_type            = each.value.worker_type
  max_capacity           = each.value.max_capacity

  glue_version = "4.0"

  execution_property {
    max_concurrent_runs = each.value.max_concurrent_runs
  }

  default_arguments = merge({
    "--job-language" = "python"
    "--job-bookmark-option" = "job-bookmark-enable"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics" = "true"
  }, each.value.default_arguments)

  tags = {
    Name = "${var.environment}-${each.key}-job"
  }
}

# IAM Role for Glue
resource "aws_iam_role" "glue_role" {
  name = "${var.environment}-glue-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.environment}-glue-service-role"
  }
}

# Attach AWS managed policy for Glue
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Custom policy for S3 access
resource "aws_iam_role_policy" "glue_s3" {
  name = "${var.environment}-glue-s3-policy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

# Policy for CloudWatch Logs
resource "aws_iam_role_policy" "glue_cloudwatch" {
  name = "${var.environment}-glue-cloudwatch-policy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}
