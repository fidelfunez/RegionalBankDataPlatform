# Kinesis Data Streams
resource "aws_kinesis_stream" "main" {
  for_each = var.streams

  name             = each.value.name
  shard_count      = each.value.shard_count
  retention_period = each.value.retention_period

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    Name = "${var.environment}-${each.key}-stream"
  }
}

# Kinesis Firehose for data delivery
resource "aws_kinesis_firehose_delivery_stream" "s3" {
  for_each = var.firehose_streams

  name        = each.value.name
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose_role.arn
    bucket_arn = each.value.bucket_arn

    prefix              = each.value.prefix
    error_output_prefix = each.value.error_prefix

    buffer_size     = each.value.buffer_size
    buffer_interval = each.value.buffer_interval

    compression_format = "GZIP"
  }

  tags = {
    Name = "${var.environment}-${each.key}-firehose"
  }
}

# IAM Role for Kinesis Firehose
resource "aws_iam_role" "firehose_role" {
  name = "${var.environment}-firehose-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "firehose.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.environment}-firehose-role"
  }
}

# IAM Policy for S3 access
resource "aws_iam_role_policy" "firehose_s3" {
  name = "${var.environment}-firehose-s3-policy"
  role = aws_iam_role.firehose_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
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
