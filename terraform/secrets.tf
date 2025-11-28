# Secret Manager Secrets
resource "google_secret_manager_secret" "oauth_client_id" {
  secret_id = "oauth-client-id"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "oauth_client_secret" {
  secret_id = "oauth-client-secret"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "jwt_secret_key" {
  secret_id = "jwt-secret-key"
  
  replication {
    auto {}
  }
}

# Grant API service account access to secrets
resource "google_secret_manager_secret_iam_member" "api_oauth_client_id" {
  secret_id = google_secret_manager_secret.oauth_client_id.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "api_oauth_client_secret" {
  secret_id = google_secret_manager_secret.oauth_client_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "api_jwt_secret" {
  secret_id = google_secret_manager_secret.jwt_secret_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_sa.email}"
}

# Outputs for manual secret population
output "secrets_to_populate" {
  value = <<-EOT
  Please populate the following secrets manually:
  
  1. OAuth Client ID:
     gcloud secrets versions add ${google_secret_manager_secret.oauth_client_id.secret_id} --data-file=- <<< "YOUR_OAUTH_CLIENT_ID"
  
  2. OAuth Client Secret:
     gcloud secrets versions add ${google_secret_manager_secret.oauth_client_secret.secret_id} --data-file=- <<< "YOUR_OAUTH_CLIENT_SECRET"
  
  3. JWT Secret Key (generate a random key):
     python3 -c "import secrets; print(secrets.token_urlsafe(32))" | gcloud secrets versions add ${google_secret_manager_secret.jwt_secret_key.secret_id} --data-file=-
  EOT
  description = "Instructions for populating secrets"
}
