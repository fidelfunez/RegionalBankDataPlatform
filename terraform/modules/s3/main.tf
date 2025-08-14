resource "aws_s3_bucket" "data_lake" {
  bucket = var.bucket_name

  tags = {
    Name = "${var.environment}-regional-bank-data-lake"
  }
}

# Bucket versioning
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bucket lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "data_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555 # 7 years
    }
  }
}

# Bucket public access block
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Data lake folder structure
resource "aws_s3_object" "data_layers" {
  for_each = var.data_layers

  bucket = aws_s3_bucket.data_lake.id
  key    = "${each.value}/"
  source = "/dev/null"

  tags = {
    Name = "${var.environment}-${each.key}-layer"
  }
}

# Additional folders for specific data types
resource "aws_s3_object" "data_folders" {
  for_each = toset([
    "raw/economic",
    "raw/demographic", 
    "raw/transactional",
    "processed/economic",
    "processed/demographic",
    "processed/transactional",
    "curated/analytics",
    "curated/reporting",
    "streaming/transactions",
    "streaming/remittances"
  ])

  bucket = aws_s3_bucket.data_lake.id
  key    = "${each.value}/"
  source = "/dev/null"

  tags = {
    Name = "${var.environment}-${replace(each.value, "/", "-")}"
  }
}

# Scripts folder for Glue jobs
resource "aws_s3_object" "scripts_folder" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "scripts/"
  source = "/dev/null"

  tags = {
    Name = "${var.environment}-scripts"
  }
}
