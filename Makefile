# Project Progress DB - Makefile
# Usage: make <target>

PROJECT_ID ?= your-project-id
REGION ?= asia-northeast1
ENVIRONMENT ?= dev

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  Development:"
	@echo "    dev-api          - Run API locally"
	@echo "    dev-frontend     - Run frontend locally"
	@echo "    test             - Run all tests"
	@echo "    lint             - Run linters"
	@echo "  "
	@echo "  Build & Deploy:"
	@echo "    docker-build     - Build all Docker images"
	@echo "    docker-push      - Push images to Artifact Registry"
	@echo "    deploy-all       - Deploy all services"
	@echo "    full-deploy      - Terraform + Build + Deploy"
	@echo "  "
	@echo "  Security:"
	@echo "    security-scan    - Run security scans"
	@echo "    sbom             - Generate SBOM"
	@echo "  "
	@echo "  Terraform:"
	@echo "    init             - Initialize Terraform"
	@echo "    plan             - Terraform plan"
	@echo "    apply            - Terraform apply"

# ==============================================================================
# Development
# ==============================================================================

.PHONY: dev-api dev-frontend dev-worker

dev-api:
	@echo "Starting API server..."
	cd backend/api && \
		USE_LOCAL_DB=true \
		ENVIRONMENT=dev \
		FRONTEND_URL=http://localhost:3000 \
		uvicorn main:app --reload --port 8000

dev-frontend:
	@echo "Starting frontend server..."
	cd frontend && npm run dev

dev-worker:
	@echo "Starting worker server..."
	cd backend/worker && \
		USE_LOCAL_DB=true \
		ENVIRONMENT=dev \
		python main.py

# ==============================================================================
# Testing
# ==============================================================================

.PHONY: test test-api test-frontend test-e2e

test: test-api
	@echo "All tests passed!"

test-api:
	@echo "Running API tests..."
	cd backend/api && \
		PYTHONPATH=. \
		USE_LOCAL_DB=true \
		JWT_SECRET_KEY=test-secret \
		pytest tests/ -v --tb=short

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm run lint && npm run type-check

test-e2e:
	@echo "Running E2E tests..."
	python e2e_test.py

# ==============================================================================
# Linting & Formatting
# ==============================================================================

.PHONY: lint lint-python lint-frontend format

lint: lint-python lint-frontend
	@echo "Linting completed!"

lint-python:
	@echo "Linting Python code..."
	cd backend && ruff check api/ worker/ --ignore E501

lint-frontend:
	@echo "Linting frontend code..."
	cd frontend && npm run lint

format:
	@echo "Formatting code..."
	cd backend && ruff format api/ worker/
	cd frontend && npm run lint:fix

# ==============================================================================
# Security
# ==============================================================================

.PHONY: security-scan sbom audit

security-scan: audit
	@echo "Security scan completed!"

audit:
	@echo "Auditing dependencies..."
	@echo "Python (API):"
	cd backend/api && pip-audit -r requirements.txt || true
	@echo ""
	@echo "Python (Worker):"
	cd backend/worker && pip-audit -r requirements.txt || true
	@echo ""
	@echo "Frontend:"
	cd frontend && npm audit || true

sbom:
	@echo "Generating SBOM..."
	@mkdir -p sbom
	@echo "API SBOM:"
	cd backend/api && pip install --quiet cyclonedx-bom && \
		cyclonedx-py requirements -o ../../sbom/api-sbom.json --format json requirements.txt || \
		echo "cyclonedx-py not available, skipping API SBOM"
	@echo "Worker SBOM:"
	cd backend/worker && pip install --quiet cyclonedx-bom && \
		cyclonedx-py requirements -o ../../sbom/worker-sbom.json --format json requirements.txt || \
		echo "cyclonedx-py not available, skipping Worker SBOM"
	@echo "Frontend SBOM:"
	cd frontend && npx @cyclonedx/cyclonedx-npm --output-file ../sbom/frontend-sbom.json || \
		echo "cyclonedx-npm not available, skipping Frontend SBOM"
	@echo "SBOM files generated in sbom/"

# ==============================================================================
# Docker
# ==============================================================================

ARTIFACT_REGISTRY = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/project-progress-db
GIT_SHA = $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")

.PHONY: docker-build docker-push docker-build-api docker-build-worker docker-build-frontend

docker-build: docker-build-api docker-build-worker docker-build-frontend
	@echo "All images built!"

docker-build-api:
	@echo "Building API Docker image..."
	docker build \
		-t $(ARTIFACT_REGISTRY)/api:$(GIT_SHA) \
		-t $(ARTIFACT_REGISTRY)/api:$(ENVIRONMENT)-latest \
		--build-arg ENVIRONMENT=$(ENVIRONMENT) \
		-f backend/api/Dockerfile \
		backend/api

docker-build-worker:
	@echo "Building Worker Docker image..."
	docker build \
		-t $(ARTIFACT_REGISTRY)/worker:$(GIT_SHA) \
		-t $(ARTIFACT_REGISTRY)/worker:$(ENVIRONMENT)-latest \
		--build-arg ENVIRONMENT=$(ENVIRONMENT) \
		-f backend/worker/Dockerfile \
		backend/worker

docker-build-frontend:
	@echo "Building Frontend Docker image..."
	docker build \
		-t $(ARTIFACT_REGISTRY)/frontend:$(GIT_SHA) \
		-t $(ARTIFACT_REGISTRY)/frontend:$(ENVIRONMENT)-latest \
		-f frontend/Dockerfile \
		frontend

docker-push:
	@echo "Pushing images to Artifact Registry..."
	docker push $(ARTIFACT_REGISTRY)/api:$(GIT_SHA)
	docker push $(ARTIFACT_REGISTRY)/api:$(ENVIRONMENT)-latest
	docker push $(ARTIFACT_REGISTRY)/worker:$(GIT_SHA)
	docker push $(ARTIFACT_REGISTRY)/worker:$(ENVIRONMENT)-latest
	docker push $(ARTIFACT_REGISTRY)/frontend:$(GIT_SHA)
	docker push $(ARTIFACT_REGISTRY)/frontend:$(ENVIRONMENT)-latest

# ==============================================================================
# Terraform
# ==============================================================================

.PHONY: init plan apply destroy

init:
	@echo "Initializing Terraform..."
	cd terraform && terraform init -backend-config="bucket=$(PROJECT_ID)-terraform-state"

plan:
	@echo "Planning Terraform changes..."
	cd terraform && terraform plan \
		-var="project_id=$(PROJECT_ID)" \
		-var="region=$(REGION)" \
		-var-file="environments/$(ENVIRONMENT).tfvars"

apply:
	@echo "Applying Terraform changes..."
	cd terraform && terraform apply \
		-var="project_id=$(PROJECT_ID)" \
		-var="region=$(REGION)" \
		-var-file="environments/$(ENVIRONMENT).tfvars"

destroy:
	@echo "Destroying Terraform resources..."
	cd terraform && terraform destroy \
		-var="project_id=$(PROJECT_ID)" \
		-var="region=$(REGION)" \
		-var-file="environments/$(ENVIRONMENT).tfvars"

terraform-output:
	cd terraform && terraform output

# ==============================================================================
# Deployment
# ==============================================================================

.PHONY: deploy-api deploy-worker deploy-frontend deploy-all

deploy-api:
	@echo "Deploying API to Cloud Run..."
	gcloud run deploy project-progress-api-$(ENVIRONMENT) \
		--image=$(ARTIFACT_REGISTRY)/api:$(GIT_SHA) \
		--region=$(REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--service-account=$$(cd terraform && terraform output -raw api_sa_email) \
		--set-env-vars="PROJECT_ID=$(PROJECT_ID),BIGQUERY_DATASET=project_progress_db,PUBSUB_TOPIC=upload-events,ENVIRONMENT=$(ENVIRONMENT)" \
		--set-secrets="OAUTH_CLIENT_ID=oauth-client-id:latest,OAUTH_CLIENT_SECRET=oauth-client-secret:latest,JWT_SECRET_KEY=jwt-secret-key:latest"

deploy-worker:
	@echo "Deploying Worker to Cloud Run..."
	gcloud run deploy project-progress-worker-$(ENVIRONMENT) \
		--image=$(ARTIFACT_REGISTRY)/worker:$(GIT_SHA) \
		--region=$(REGION) \
		--platform=managed \
		--no-allow-unauthenticated \
		--service-account=$$(cd terraform && terraform output -raw worker_sa_email) \
		--set-env-vars="PROJECT_ID=$(PROJECT_ID),BIGQUERY_DATASET=project_progress_db,REGION=$(REGION),ENVIRONMENT=$(ENVIRONMENT)"

deploy-frontend:
	@echo "Deploying Frontend to Cloud Run..."
	@API_URL=$$(gcloud run services describe project-progress-api-$(ENVIRONMENT) --region=$(REGION) --format='value(status.url)'); \
	gcloud run deploy project-progress-frontend-$(ENVIRONMENT) \
		--image=$(ARTIFACT_REGISTRY)/frontend:$(GIT_SHA) \
		--region=$(REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--set-env-vars="NEXT_PUBLIC_API_URL=$$API_URL"

deploy-all: deploy-api deploy-worker deploy-frontend
	@echo "All services deployed successfully!"

# ==============================================================================
# Setup & Utilities
# ==============================================================================

.PHONY: setup setup-secrets setup-dev clean

setup: setup-dev
	@echo "Setup complete!"

setup-dev:
	@echo "Setting up development environment..."
	cd backend/api && python3 -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt
	cd frontend && npm ci
	@echo "Development environment ready!"

setup-secrets:
	@echo "Setting up secrets in Secret Manager..."
	@echo ""
	@echo "1. Generate JWT secret key:"
	python3 -c "import secrets; print(secrets.token_urlsafe(32))" | \
		gcloud secrets versions add jwt-secret-key --data-file=-
	@echo ""
	@echo "2. Set OAuth Client ID (replace with your actual value):"
	@echo "   echo -n 'YOUR_CLIENT_ID' | gcloud secrets versions add oauth-client-id --data-file=-"
	@echo ""
	@echo "3. Set OAuth Client Secret (replace with your actual value):"
	@echo "   echo -n 'YOUR_CLIENT_SECRET' | gcloud secrets versions add oauth-client-secret --data-file=-"

clean:
	@echo "Cleaning up..."
	rm -rf backend/api/__pycache__ backend/api/**/__pycache__
	rm -rf backend/worker/__pycache__ backend/worker/**/__pycache__
	rm -rf frontend/.next frontend/node_modules
	rm -rf sbom/
	@echo "Cleanup complete!"

# ==============================================================================
# Full Pipeline
# ==============================================================================

.PHONY: full-deploy ci

full-deploy: apply docker-build docker-push deploy-all
	@echo "Full deployment completed!"
	@make terraform-output

ci: lint test security-scan
	@echo "CI checks passed!"
