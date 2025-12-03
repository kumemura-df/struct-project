# Production Environment Configuration
# Usage: terraform apply -var-file=environments/prod.tfvars

environment = "prod"

# Override these with your actual project ID
# project_id = "your-gcp-project-id"

region   = "asia-northeast1"
location = "ASIA-NORTHEAST1"

bigquery_dataset = "project_progress_db"

# OAuth domain restrictions (set your organization's domain)
# allowed_oauth_domains = ["your-company.com"]
allowed_oauth_domains = []

# Frontend URL will be dynamically set after API deployment
# frontend_url = "https://project-progress-frontend-prod-xxx.run.app"

