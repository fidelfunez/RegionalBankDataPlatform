variable "environment" {
  description = "Environment name"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name for data lake"
  type        = string
}

variable "data_layers" {
  description = "Data lake layers configuration"
  type        = map(string)
  default = {
    raw       = "raw"
    processed = "processed"
    curated   = "curated"
    streaming = "streaming"
  }
}
