# Cloud Run Services

# Enable Cloud Run API
resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

# Enable Vertex AI API
resource "google_project_service" "aiplatform_api" {
  service = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Enable BigQuery API
resource "google_project_service" "bigquery_api" {
  service = "bigquery.googleapis.com"
  disable_on_destroy = false
}

# Enable Artifact Registry API
resource "google_project_service" "artifactregistry_api" {
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Enable Cloud Build API
resource "google_project_service" "cloudbuild_api" {
  service = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# API Service
resource "google_cloud_run_service" "api" {
  name     = "project-progress-api-${var.environment}"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.api_sa.email
      
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/project-progress-db/api:latest"
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "BIGQUERY_DATASET"
          value = var.bigquery_dataset
        }
        
        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.upload_events.name
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
        
        env {
          name  = "FRONTEND_URL"
          value = var.frontend_url
        }
        
        env {
          name = "ALLOWED_OAUTH_DOMAINS"
          value = join(",", var.allowed_oauth_domains)
        }
        
        env {
          name = "OAUTH_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.oauth_client_id.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "OAUTH_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.oauth_client_secret.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "JWT_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret_key.secret_id
              key  = "latest"
            }
          }
        }
        
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.run_api,
    google_secret_manager_secret_iam_member.api_oauth_client_id,
    google_secret_manager_secret_iam_member.api_oauth_client_secret,
    google_secret_manager_secret_iam_member.api_jwt_secret,
  ]
}

# Allow unauthenticated access to API (authentication handled by app)
resource "google_cloud_run_service_iam_member" "api_public" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Worker Service
resource "google_cloud_run_service" "worker" {
  name     = "project-progress-worker-${var.environment}"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.worker_sa.email
      
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/project-progress-db/worker:latest"
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "BIGQUERY_DATASET"
          value = var.bigquery_dataset
        }
        
        env {
          name  = "REGION"
          value = var.region
        }
        
        resources {
          limits = {
            cpu    = "2"
            memory = "1Gi"
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.run_api]
}

# Create service account for Pub/Sub to invoke Worker
resource "google_service_account" "pubsub_invoker" {
  account_id   = "pubsub-invoker-${random_id.sa_suffix.hex}"
  display_name = "Pub/Sub Cloud Run Invoker"
}

# Grant invoker role to Pub/Sub service account
resource "google_cloud_run_service_iam_member" "worker_pubsub_invoker" {
  service  = google_cloud_run_service.worker.name
  location = google_cloud_run_service.worker.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_invoker.email}"
}

# Frontend Service
resource "google_cloud_run_service" "frontend" {
  name     = "project-progress-frontend-${var.environment}"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/project-progress-db/frontend:latest"
        
        ports {
          container_port = 3000
        }
        
        env {
          name  = "NEXT_PUBLIC_API_URL"
          value = google_cloud_run_service.api.status[0].url
        }
        
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.run_api,
    google_cloud_run_service.api,
  ]
}

# Allow unauthenticated access to Frontend
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_service.frontend.name
  location = google_cloud_run_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "api_url" {
  value       = google_cloud_run_service.api.status[0].url
  description = "API service URL"
}

output "worker_url" {
  value       = google_cloud_run_service.worker.status[0].url
  description = "Worker service URL"
}

output "frontend_url" {
  value       = google_cloud_run_service.frontend.status[0].url
  description = "Frontend service URL"
}

output "pubsub_invoker_email" {
  value = google_service_account.pubsub_invoker.email
  description = "Pub/Sub invoker service account email"
}
