# Development Environment Configuration
# Usage: terraform apply -var-file=environments/dev.tfvars

environment = "dev"

# Override these with your actual project ID
# project_id = "your-gcp-project-id"

region   = "asia-northeast1"
location = "ASIA-NORTHEAST1"

bigquery_dataset = "project_progress_db_dev"

# OAuth domain restrictions (empty allows all for development)
allowed_oauth_domains = []

# Frontend URL for local development
frontend_url = "http://localhost:3000"

