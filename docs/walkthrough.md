# Project Progress DB MVP - Deployment Walkthrough

This guide explains how to deploy the application to Google Cloud Platform.

## Prerequisites

1.  **GCP Project**: You need a Google Cloud Project.
2.  **GCloud CLI**: Authenticated with `gcloud auth login` and `gcloud config set project [PROJECT_ID]`.
3.  **Terraform**: Installed.

## 1. Build and Push Docker Images

You need to build the Docker images and push them to Google Container Registry (GCR) or Artifact Registry.

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Enable Artifact Registry
gcloud services enable artifactregistry.googleapis.com

# Create repository (if not exists)
gcloud artifacts repositories create cloud-run-source-deploy --repository-format=docker --location=asia-northeast1 --description="Docker repository"

# Build and Push API
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/api-service backend/api

# Build and Push Worker
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/worker-service backend/worker

# Build and Push Frontend
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/frontend-service frontend
```

## 2. Update Terraform Configuration

Update `terraform/cloudrun.tf` to use the images you just pushed.
Replace `us-docker.pkg.dev/cloudrun/container/hello` with your actual image paths:
- `asia-northeast1-docker.pkg.dev/[PROJECT_ID]/cloud-run-source-deploy/api-service`
- `asia-northeast1-docker.pkg.dev/[PROJECT_ID]/cloud-run-source-deploy/worker-service`
- `asia-northeast1-docker.pkg.dev/[PROJECT_ID]/cloud-run-source-deploy/frontend-service`

## 3. Deploy Infrastructure

Run Terraform to create BigQuery tables, GCS buckets, Pub/Sub topics, and Cloud Run services.

```bash
cd terraform
terraform init
terraform apply -var="project_id=$PROJECT_ID"
```

## 4. Verify Deployment

1.  **Frontend**: Get the URL of the `frontend-service` from Cloud Run console or Terraform output.
2.  **Upload**: Open the frontend, upload a sample text file (e.g., meeting notes).
3.  **Check Logs**:
    - Go to Cloud Run logs for `worker-service`.
    - Verify it received the Pub/Sub message and called Gemini.
4.  **Check BigQuery**:
    - Go to BigQuery console.
    - Query `project_progress_db.projects` and `tasks` to see extracted data.
5.  **Dashboard**: Refresh the frontend to see the extracted projects and tasks.

## Troubleshooting

- **Gemini Errors**: Ensure Vertex AI API is enabled and you have quota.
- **Permission Errors**: Check IAM roles in `terraform/iam.tf`.
