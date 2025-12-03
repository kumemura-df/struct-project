# Terraform State Bucket
# This bucket stores the Terraform state file for the project.
# NOTE: This resource should be created BEFORE initializing the backend.
#
# Bootstrap procedure:
# 1. Comment out the backend "gcs" block in provider.tf
# 2. Run: terraform init && terraform apply -target=google_storage_bucket.terraform_state
# 3. Uncomment the backend "gcs" block
# 4. Run: terraform init -migrate-state -backend-config="bucket=${var.project_id}-terraform-state"

resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_id}-terraform-state"
  location      = var.location
  force_destroy = false

  # Enable versioning for state file history
  versioning {
    enabled = true
  }

  # Lifecycle rule to clean up old versions
  lifecycle_rule {
    condition {
      num_newer_versions = 10
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }

  # Uniform bucket-level access
  uniform_bucket_level_access = true

  labels = {
    purpose     = "terraform-state"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Grant Cloud Build service account access to state bucket
resource "google_storage_bucket_iam_member" "cloudbuild_state_access" {
  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

output "terraform_state_bucket" {
  value       = google_storage_bucket.terraform_state.name
  description = "Terraform state bucket name"
}

