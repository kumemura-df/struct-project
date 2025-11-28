# 3. Architecture & Overall Design

## 3.1. Technology Stack

| Category | Technology | Selection Reason |
|---|---|---|
| **Frontend** | Next.js (TypeScript) | React-based framework for SEO, performance, and developer experience. |
| **Backend API** | FastAPI (Python) | High performance, easy integration with AI libraries, auto-generated docs. |
| **Async Worker** | Python | Shared logic with API, ideal for data processing and AI calls. |
| **Database** | BigQuery | Serverless data warehouse, handles large datasets, SQL interface. |
| **Storage** | Cloud Storage (GCS) | Durable object storage for raw meeting files. |
| **AI / LLM** | Vertex AI (Gemini) | Native GCP integration, high context window, cost-effective. |
| **Messaging** | Pub/Sub | Decouples upload from processing, ensures reliability. |
| **Compute** | Cloud Run | Serverless container platform, scales to zero, easy deployment. |
| **IaC** | Terraform | Infrastructure as Code for reproducible environments. |

## 3.2. System Configuration Diagram

```mermaid
graph TB
    User[User (Browser)]
    
    subgraph GCP Project
        LB[Load Balancer]
        
        subgraph Cloud Run
            FE[Frontend Service<br/>(Next.js)]
            API[API Service<br/>(FastAPI)]
            Worker[Worker Service<br/>(Python)]
        end
        
        subgraph Data & Storage
            GCS[Cloud Storage<br/>(Raw Files)]
            BQ[(BigQuery<br/>Data Warehouse)]
        end
        
        subgraph Messaging
            PubSub[Pub/Sub<br/>(Upload Events)]
        end
        
        subgraph AI Services
            Vertex[Vertex AI<br/>(Gemini)]
        end
    end

    User -->|HTTPS| LB
    LB --> FE
    LB --> API
    
    FE -->|API Calls| API
    API -->|Upload| GCS
    API -->|Publish Event| PubSub
    API -->|Query| BQ
    
    PubSub -->|Trigger| Worker
    Worker -->|Read| GCS
    Worker -->|Analyze| Vertex
    Worker -->|Insert| BQ
```

## 3.3. Connection Patterns

| Source | Destination | Protocol | Description |
|---|---|---|---|
| **Frontend** | **API Service** | REST (HTTP/JSON) | Standard API calls for UI data. |
| **API Service** | **Cloud Storage** | Google Cloud API (gRPC/HTTP) | Uploading raw meeting files. |
| **API Service** | **Pub/Sub** | Google Cloud API (gRPC) | Publishing "File Uploaded" events. |
| **API Service** | **BigQuery** | Google Cloud API (gRPC/HTTP) | Querying data for dashboard. |
| **Worker** | **Cloud Storage** | Google Cloud API | Reading raw files for analysis. |
| **Worker** | **Vertex AI** | Google Cloud API (gRPC) | Sending text for extraction. |
| **Worker** | **BigQuery** | Google Cloud API | Inserting extracted data. |
