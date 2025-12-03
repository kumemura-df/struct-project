# Staging Environment Configuration
# Usage: terraform apply -var-file=environments/staging.tfvars

environment = "staging"

# Override these with your actual project ID
# project_id = "your-gcp-project-id"

region   = "asia-northeast1"
location = "ASIA-NORTHEAST1"

bigquery_dataset = "project_progress_db_staging"

# OAuth domain restrictions (empty allows all)
allowed_oauth_domains = []

# Frontend URL will be dynamically set after API deployment
# frontend_url = "https://project-progress-frontend-staging-xxx.run.app"

