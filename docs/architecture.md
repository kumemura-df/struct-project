# GCP Architecture Design (MVP)

## Overview

The system is built on Google Cloud Platform (GCP) using serverless components for scalability and ease of management.

### Components

1.  **Cloud Run**
    *   `frontend-service`: UI (Next.js).
    *   `api-service`: REST API (FastAPI).
    *   `worker-service`: Async processing (Pub/Sub trigger).

2.  **Cloud Storage**
    *   `meeting-notes-raw`: Bucket for storing raw uploaded files.

3.  **Pub/Sub**
    *   `upload-events`: Topic for "File Uploaded" events to trigger analysis.

4.  **Vertex AI (Gemini)**
    *   Meeting minutes -> Structured JSON extraction.
    *   Email draft generation.

5.  **BigQuery**
    *   Data warehouse for `projects`, `tasks`, `risks`, `meetings`.

## Processing Flow

1.  **Upload**
    *   User uploads file via UI.
    *   UI calls `api-service` `/upload`.
    *   `api-service` saves file to GCS (`meeting-notes-raw`).
    *   `api-service` inserts metadata to BigQuery `meetings` (status="PENDING").
    *   `api-service` publishes message to Pub/Sub `upload-events`.

2.  **Async Analysis (Worker)**
    *   `worker-service` triggered by Pub/Sub.
    *   Reads file from GCS.
    *   Calls Vertex AI (Gemini) with prompt and JSON Schema.
    *   Parses JSON response.
    *   Inserts data into BigQuery `projects`, `tasks`, `risks`.
    *   Updates `meetings` status to "DONE".

3.  **Dashboard / Viewing**
    *   UI calls `api-service` endpoints (e.g., `/projects`, `/tasks`).
    *   `api-service` executes SQL queries on BigQuery.
    *   Returns JSON to UI.

4.  **Export**
    *   UI calls `api-service` `/export`.
    *   `api-service` queries BigQuery, generates CSV, saves to temp GCS.
    *   Returns signed URL.

5.  **Email Generation**
    *   UI calls `api-service` `/generate-email`.
    *   `api-service` fetches top delayed tasks from BigQuery.
    *   Calls Vertex AI to generate email text.
    *   Returns text to UI.
