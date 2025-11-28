PROJECT_ID ?= your-project-id
REGION ?= asia-northeast1

.PHONY: init plan apply deploy-api deploy-worker deploy-frontend

init:
	cd terraform && terraform init

plan:
	cd terraform && terraform plan -var="project_id=$(PROJECT_ID)" -var="region=$(REGION)"

apply:
	cd terraform && terraform apply -var="project_id=$(PROJECT_ID)" -var="region=$(REGION)"

# Docker image management
ARTIFACT_REGISTRY = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/project-progress-db

.PHONY: docker-build docker-push docker-build-api docker-build-worker docker-build-frontend

docker-build: docker-build-api docker-build-worker docker-build-frontend

docker-build-api:
	@echo "Building API Docker image..."
	docker build -t $(ARTIFACT_REGISTRY)/api:latest -t $(ARTIFACT_REGISTRY)/api:$(shell git rev-parse --short HEAD) \
		-f backend/api/Dockerfile backend/api

docker-build-worker:
	@echo "Building Worker Docker image..."
	docker build -t $(ARTIFACT_REGISTRY)/worker:latest -t $(ARTIFACT_REGISTRY)/worker:$(shell git rev-parse --short HEAD) \
		-f backend/worker/Dockerfile backend/worker

docker-build-frontend:
	@echo "Building Frontend Docker image..."
	docker build -t $(ARTIFACT_REGISTRY)/frontend:latest -t $(ARTIFACT_REGISTRY)/frontend:$(shell git rev-parse --short HEAD) \
		-f frontend/Dockerfile frontend

docker-push:
	@echo "Pushing images to Artifact Registry..."
	docker push $(ARTIFACT_REGISTRY)/api:latest
	docker push $(ARTIFACT_REGISTRY)/api:$(shell git rev-parse --short HEAD)
	docker push $(ARTIFACT_REGISTRY)/worker:latest
	docker push $(ARTIFACT_REGISTRY)/worker:$(shell git rev-parse --short HEAD)
	docker push $(ARTIFACT_REGISTRY)/frontend:latest
	docker push $(ARTIFACT_REGISTRY)/frontend:$(shell git rev-parse --short HEAD)

# Deployment commands
.PHONY: deploy-api deploy-worker deploy-frontend deploy-all

deploy-api:
	@echo "Deploying API to Cloud Run..."
	gcloud run deploy project-progress-api-dev \
		--image=$(ARTIFACT_REGISTRY)/api:latest \
		--region=$(REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--service-account=$$(cd terraform && terraform output -raw api_sa_email) \
		--set-env-vars="PROJECT_ID=$(PROJECT_ID),BIGQUERY_DATASET=project_progress_db,PUBSUB_TOPIC=upload-events,ENVIRONMENT=dev,FRONTEND_URL=http://localhost:3000" \
		--set-secrets="OAUTH_CLIENT_ID=oauth-client-id:latest,OAUTH_CLIENT_SECRET=oauth-client-secret:latest,JWT_SECRET_KEY=jwt-secret-key:latest"

deploy-worker:
	@echo "Deploying Worker to Cloud Run..."
	gcloud run deploy project-progress-worker-dev \
		--image=$(ARTIFACT_REGISTRY)/worker:latest \
		--region=$(REGION) \
		--platform=managed \
		--no-allow-unauthenticated \
		--service-account=$$(cd terraform && terraform output -raw worker_sa_email) \
		--set-env-vars="PROJECT_ID=$(PROJECT_ID),BIGQUERY_DATASET=project_progress_db,REGION=$(REGION)"

deploy-frontend:
	@echo "Deploying Frontend to Cloud Run..."
	@API_URL=$$(gcloud run services describe project-progress-api-dev --region=$(REGION) --format='value(status.url)'); \
	gcloud run deploy project-progress-frontend-dev \
		--image=$(ARTIFACT_REGISTRY)/frontend:latest \
		--region=$(REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--set-env-vars="NEXT_PUBLIC_API_URL=$$API_URL"

deploy-all: deploy-api deploy-worker deploy-frontend
	@echo "All services deployed successfully!"

# Helper commands
.PHONY: setup-secrets terraform-output

setup-secrets:
	@echo "Setting up secrets in Secret Manager..."
	@echo ""
	@echo "1. Generate JWT secret key:"
	@python3 -c "import secrets; print(secrets.token_urlsafe(32))" | gcloud secrets versions add jwt-secret-key --data-file=-
	@echo ""
	@echo "2. Set OAuth Client ID (replace with your actual value):"
	@echo "   gcloud secrets versions add oauth-client-id --data-file=- <<< 'YOUR_CLIENT_ID'"
	@echo ""
	@echo "3. Set OAuth Client Secret (replace with your actual value):"
	@echo "   gcloud secrets versions add oauth-client-secret --data-file=- <<< 'YOUR_CLIENT_SECRET'"

terraform-output:
	cd terraform && terraform output

# Full deployment pipeline
.PHONY: full-deploy

full-deploy: apply docker-build docker-push deploy-all
	@echo "Full deployment completed!"
	@make terraform-output

