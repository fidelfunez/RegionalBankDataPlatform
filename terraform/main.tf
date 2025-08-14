terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "regional-bank-terraform-state"
    key    = "data-platform/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "regional-bank-data-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"
  
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  azs         = var.availability_zones
}

# S3 Data Lake
module "s3_data_lake" {
  source = "./modules/s3"
  
  environment = var.environment
  bucket_name = "${var.environment}-regional-bank-data-lake"
  
  data_layers = {
    raw        = "raw"
    processed  = "processed"
    curated    = "curated"
    streaming  = "streaming"
  }
}

# Redshift Data Warehouse
module "redshift" {
  source = "./modules/redshift"
  
  environment     = var.environment
  cluster_name    = "${var.environment}-regional-bank-redshift"
  node_type       = var.redshift_node_type
  nodes           = var.redshift_nodes
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  security_groups = [module.vpc.redshift_security_group_id]
}

# AWS Glue
module "glue" {
  source = "./modules/glue"
  
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnet_ids
  security_groups = [module.vpc.glue_security_group_id]
  
  glue_jobs = {
    batch_etl = {
      name        = "batch-etl-job"
      script_path = "s3://${module.s3_data_lake.bucket_name}/scripts/batch_etl.py"
      max_retries = 3
      timeout     = 2880
    }
    streaming_etl = {
      name        = "streaming-etl-job"
      script_path = "s3://${module.s3_data_lake.bucket_name}/scripts/streaming_etl.py"
      max_retries = 3
      timeout     = 2880
    }
  }
}

# Kinesis Data Streams
module "kinesis" {
  source = "./modules/kinesis"
  
  environment = var.environment
  streams = {
    transactions = {
      name             = "${var.environment}-transactions-stream"
      shard_count      = 2
      retention_period = 24
    }
    remittances = {
      name             = "${var.environment}-remittances-stream"
      shard_count      = 2
      retention_period = 24
    }
  }
}

# CloudWatch Monitoring
module "monitoring" {
  source = "./modules/monitoring"
  
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  
  alarms = {
    pipeline_failure = {
      name          = "pipeline-failure-alarm"
      metric_name   = "FailedTaskCount"
      namespace     = "AWS/Glue"
      threshold     = 1
      period        = 300
      evaluation_periods = 2
    }
    data_quality = {
      name          = "data-quality-alarm"
      metric_name   = "DataQualityCheckFailed"
      namespace     = "Custom/DataQuality"
      threshold     = 1
      period        = 300
      evaluation_periods = 1
    }
  }
}

# IAM Roles and Policies
module "iam" {
  source = "./modules/iam"
  
  environment = var.environment
  s3_bucket_arn = module.s3_data_lake.bucket_arn
  redshift_cluster_arn = module.redshift.cluster_arn
  kinesis_stream_arns = module.kinesis.stream_arns
}

# Outputs
output "s3_bucket_name" {
  description = "S3 Data Lake bucket name"
  value       = module.s3_data_lake.bucket_name
}

output "redshift_endpoint" {
  description = "Redshift cluster endpoint"
  value       = module.redshift.endpoint
}

output "kinesis_stream_names" {
  description = "Kinesis stream names"
  value       = module.kinesis.stream_names
}

output "glue_job_names" {
  description = "Glue job names"
  value       = module.glue.job_names
}
