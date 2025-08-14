# Redshift Subnet Group
resource "aws_redshift_subnet_group" "main" {
  name       = "${var.environment}-regional-bank-redshift-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.environment}-regional-bank-redshift-subnet-group"
  }
}

# Redshift Parameter Group
resource "aws_redshift_parameter_group" "main" {
  family = "redshift-1.0"
  name   = "${var.environment}-regional-bank-redshift-params"

  parameter {
    name  = "enable_user_activity_logging"
    value = "true"
  }

  parameter {
    name  = "require_ssl"
    value = "true"
  }

  parameter {
    name  = "max_concurrency_scaling_clusters"
    value = "2"
  }

  tags = {
    Name = "${var.environment}-regional-bank-redshift-params"
  }
}

# Redshift Cluster
resource "aws_redshift_cluster" "main" {
  cluster_identifier        = var.cluster_name
  database_name            = "regional_bank_analytics"
  master_username          = var.master_username
  master_password          = var.master_password
  node_type                = var.node_type
  cluster_type             = var.nodes > 1 ? "multi-node" : "single-node"
  number_of_nodes          = var.nodes > 1 ? var.nodes : null
  skip_final_snapshot      = var.environment == "dev"
  final_snapshot_identifier = "${var.cluster_name}-final-snapshot"

  vpc_security_group_ids = var.security_groups
  cluster_subnet_group_name = aws_redshift_subnet_group.main.name
  cluster_parameter_group_name = aws_redshift_parameter_group.main.name

  # Encryption
  encrypted = true
  kms_key_id = var.kms_key_id

  # Logging
  logging {
    enable        = true
    bucket_name   = var.logging_bucket
    s3_key_prefix = "redshift-logs/"
  }

  # Maintenance window
  preferred_maintenance_window = "sun:05:00-sun:06:00"

  # Backup retention
  automated_snapshot_retention_period = 7

  tags = {
    Name = "${var.environment}-regional-bank-redshift"
  }
}

# Redshift IAM Role for S3 access
resource "aws_iam_role" "redshift_s3" {
  name = "${var.environment}-redshift-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.environment}-redshift-s3-role"
  }
}

# IAM Policy for S3 access
resource "aws_iam_role_policy" "redshift_s3" {
  name = "${var.environment}-redshift-s3-policy"
  role = aws_iam_role.redshift_s3.id

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

# Attach IAM role to Redshift cluster
resource "aws_redshift_cluster_iam_roles" "main" {
  cluster_identifier = aws_redshift_cluster.main.cluster_identifier
  iam_role_arns      = [aws_iam_role.redshift_s3.arn]
}
