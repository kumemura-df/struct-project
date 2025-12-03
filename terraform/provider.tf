terraform {
  required_version = ">= 1.5.0"

  # GCS Backend for remote state management
  # Initialize with: terraform init -backend-config="bucket=<PROJECT_ID>-terraform-state"
  # Create bucket first: gsutil mb -l asia-northeast1 gs://<PROJECT_ID>-terraform-state
  backend "gcs" {
    # bucket is set via -backend-config or environment variable
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
