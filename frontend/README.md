# Project Progress DB

Meeting notes analysis tool with AI integration.

## Service URLs (Production)

- **Frontend**: https://project-progress-frontend-prod-29226667525.asia-northeast1.run.app
- **API**: https://project-progress-api-prod-29226667525.asia-northeast1.run.app
- **Worker**: https://project-progress-worker-prod-29226667525.asia-northeast1.run.app

## Deployment

### Prerequisites
- Google Cloud SDK (gcloud)
- Docker
- Project ID: `sandbox-471809`

### Steps

1. **Setup Secrets**
   ```bash
   # JWT Secret
   python3 -c "import secrets; print(secrets.token_urlsafe(32))" | gcloud secrets versions add jwt-secret-key --data-file=-
   
   # OAuth (Dev Bypass)
   echo "dev-bypass-client-id" | gcloud secrets versions add oauth-client-id --data-file=-
   echo "dev-bypass-client-secret" | gcloud secrets versions add oauth-client-secret --data-file=-
   ```

2. **Build & Push Docker Images**
   ```bash
   # Configure Docker
   gcloud auth configure-docker asia-northeast1-docker.pkg.dev
   
   # Build & Push API
   docker build -t asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/api:latest -f backend/api/Dockerfile backend/api
   docker push asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/api:latest
   
   # Build & Push Worker
   docker build -t asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/worker:latest -f backend/worker/Dockerfile backend/worker
   docker push asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/worker:latest
   
   # Build & Push Frontend
   docker build -t asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/frontend:latest -f frontend/Dockerfile frontend
   docker push asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/frontend:latest
   ```

3. **Deploy to Cloud Run**
   ```bash
   # Deploy API
   gcloud run deploy project-progress-api-prod \
     --image=asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/api:latest \
     --region=asia-northeast1 \
     --platform=managed \
     --allow-unauthenticated \
     --service-account=api-sa-8fd82014@sandbox-471809.iam.gserviceaccount.com \
     --memory=1Gi \
     --timeout=300 \
     --set-env-vars="PROJECT_ID=sandbox-471809,BIGQUERY_DATASET=project_progress_db,PUBSUB_TOPIC=upload-events,ENVIRONMENT=prod,USE_LOCAL_DB=false,USE_LOCAL_STORAGE=false" \
     --set-secrets="OAUTH_CLIENT_ID=oauth-client-id:latest,OAUTH_CLIENT_SECRET=oauth-client-secret:latest,JWT_SECRET_KEY=jwt-secret-key:latest"

   # Deploy Worker
   gcloud run deploy project-progress-worker-prod \
     --image=asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/worker:latest \
     --region=asia-northeast1 \
     --platform=managed \
     --no-allow-unauthenticated \
     --service-account=worker-sa-8fd82014@sandbox-471809.iam.gserviceaccount.com \
     --set-env-vars="PROJECT_ID=sandbox-471809,BIGQUERY_DATASET=project_progress_db,REGION=asia-northeast1"

   # Deploy Frontend
   gcloud run deploy project-progress-frontend-prod \
     --image=asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/frontend:latest \
     --region=asia-northeast1 \
     --platform=managed \
     --allow-unauthenticated \
     --set-env-vars="NEXT_PUBLIC_API_URL=https://project-progress-api-prod-29226667525.asia-northeast1.run.app"
   ```

4. **Configure Pub/Sub**
   ```bash
   gcloud pubsub subscriptions update upload-events-sub \
     --push-endpoint=https://project-progress-worker-prod-29226667525.asia-northeast1.run.app \
     --push-auth-service-account=pubsub-invoker-8fd82014@sandbox-471809.iam.gserviceaccount.com
   ```
