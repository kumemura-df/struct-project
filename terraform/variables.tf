variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "location" {
  description = "The GCP location for multi-region resources (like BigQuery/GCS)"
  type        = string
  default     = "ASIA-NORTHEAST1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "allowed_oauth_domains" {
  description = "List of allowed email domains for OAuth (e.g., ['example.com']). Empty list allows all domains."
  type        = list(string)
  default     = []
}

variable "bigquery_dataset" {
  description = "BigQuery dataset name"
  type        = string
  default     = "project_progress_db"
}

variable "frontend_url" {
  description = "Frontend URL for CORS and OAuth redirects"
  type        = string
  default     = "http://localhost:3000"
}
