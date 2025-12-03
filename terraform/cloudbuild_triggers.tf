# Cloud Build Triggers for CI/CD Pipeline
# 
# Trigger Strategy:
#   - main branch push -> Staging deployment
#   - tag push (v*) -> Production deployment

# Enable Cloud Build API
resource "google_project_service" "cloudbuild_trigger_api" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# Enable Cloud Source Repositories API (if using Cloud Source Repos)
resource "google_project_service" "sourcerepo_api" {
  service            = "sourcerepo.googleapis.com"
  disable_on_destroy = false
}

# Cloud Build Trigger for Staging (main branch)
resource "google_cloudbuild_trigger" "staging" {
  name        = "project-progress-staging"
  description = "Deploy to staging on main branch push"
  
  # GitHub repository connection (requires manual setup in Cloud Build console)
  # Uncomment and configure if using GitHub
  # github {
  #   owner = "your-github-org"
  #   name  = "your-repo-name"
  #   push {
  #     branch = "^main$"
  #   }
  # }
  
  # For Cloud Source Repositories
  trigger_template {
    branch_name = "^main$"
    repo_name   = "project-progress-db"  # Update with your repo name
  }
  
  filename = "cloudbuild-staging.yaml"
  
  substitutions = {
    _REGION             = var.region
    _REPOSITORY         = "project-progress-db"
    _BIGQUERY_DATASET   = "project_progress_db_staging"
    _PUBSUB_TOPIC       = "upload-events-staging"
    _API_SA_EMAIL       = google_service_account.api_sa.email
    _WORKER_SA_EMAIL    = google_service_account.worker_sa.email
    _ALLOWED_OAUTH_DOMAINS = join(",", var.allowed_oauth_domains)
  }
  
  depends_on = [
    google_project_service.cloudbuild_trigger_api,
    google_project_service.sourcerepo_api,
  ]
}

# Cloud Build Trigger for Production (tag push)
resource "google_cloudbuild_trigger" "production" {
  name        = "project-progress-production"
  description = "Deploy to production on version tag push (v*)"
  
  # GitHub repository connection (requires manual setup in Cloud Build console)
  # Uncomment and configure if using GitHub
  # github {
  #   owner = "your-github-org"
  #   name  = "your-repo-name"
  #   push {
  #     tag = "^v[0-9]+\\.[0-9]+\\.[0-9]+$"
  #   }
  # }
  
  # For Cloud Source Repositories
  trigger_template {
    tag_name  = "^v[0-9]+\\.[0-9]+\\.[0-9]+$"
    repo_name = "project-progress-db"  # Update with your repo name
  }
  
  filename = "cloudbuild-prod.yaml"
  
  substitutions = {
    _REGION             = var.region
    _REPOSITORY         = "project-progress-db"
    _BIGQUERY_DATASET   = "project_progress_db"
    _PUBSUB_TOPIC       = "upload-events"
    _API_SA_EMAIL       = google_service_account.api_sa.email
    _WORKER_SA_EMAIL    = google_service_account.worker_sa.email
    _ALLOWED_OAUTH_DOMAINS = join(",", var.allowed_oauth_domains)
  }
  
  depends_on = [
    google_project_service.cloudbuild_trigger_api,
    google_project_service.sourcerepo_api,
  ]
}

# Grant Cloud Build service account permissions
data "google_project" "project" {
}

resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Outputs
output "staging_trigger_id" {
  value       = google_cloudbuild_trigger.staging.id
  description = "Staging build trigger ID"
}

output "production_trigger_id" {
  value       = google_cloudbuild_trigger.production.id
  description = "Production build trigger ID"
}

