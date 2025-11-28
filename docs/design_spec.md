# Project Progress DB MVP - Design Specification

## 1. Product Concept

**Concept:** A tool that automatically converts meeting notes into a "Project Progress DB" and "Risk Dashboard" by simply uploading them.

**Target Users:**
- PM / PdM / PMO in 50-500 employee companies.
- Project Leaders in Consulting/SIer.
- Corporate Planning (Company-wide project management).
- People who want to avoid increasing tools but have scattered progress/tasks.

**Use Cases:**
- Upload meeting notes (Notion, Confluence, Google Docs, Email).
- Automatically extract:
    - Project Name
    - Tasks (Content / Owner / Due Date)
    - Risks / Decisions
- Visualize as a dashboard by project and time period.

## 2. MVP Scope

### Input
- **Manual Upload**: Text or Markdown files (.txt / .md).
- **Future**: Google Docs / Meet transcript API integration.

### Automated Extraction Items
- **Meeting Metadata**:
    - `meeting_id` (Internal ID)
    - `meeting_title` (if available)
    - `meeting_date` (User input or inferred)
- **Project**:
    - `project_name` (Multiple possible)
- **Tasks**:
    - `task_title`
    - `task_description`
    - `owner`
    - `due_date` (Normalized from natural language)
    - `status` (Not Started / In Progress / Done / Unknown)
- **Risks / Decisions**:
    - `risk_description`
    - `risk_level` (Low / Medium / High)
    - `related_project`
    - `originating_sentence` (Source text)

### UI (MVP)
- **Upload Screen**:
    - File upload.
    - Meeting date input (mandatory).
    - Project candidate preview (AI extraction result confirmation/edit).
- **Dashboard**:
    - Project List + Unfinished Task Count + Risk Count.
    - "Overdue Tasks" List.
    - "Due This Week" List.
    - "Risk-like Statements" List (with source text).

### Output (MVP)
- **CSV/Excel Export**: `projects.csv`, `tasks.csv`, `risks.csv`.
- **Email Generation**: "Top 10 Delayed Risk Tasks of the Week" email draft generation.

### Non-functional Scope
- Single tenant (1 company 1 environment or 1 project PoC).
- Simple authentication (e.g., Google OAuth).
- Japanese/English support.

## 3. Data Model (BigQuery)

### `meetings`
| Column | Type | Description |
|---|---|---|
| meeting_id | STRING | PK |
| tenant_id | STRING | |
| meeting_date | DATE | |
| title | STRING | |
| source_file_uri | STRING | GCS URI |
| language | STRING | |
| created_at | TIMESTAMP | |
| status | STRING | PENDING / DONE / ERROR |
| error_message | STRING | |

### `projects`
| Column | Type | Description |
|---|---|---|
| project_id | STRING | PK |
| tenant_id | STRING | |
| project_name | STRING | |
| latest_meeting_id | STRING | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### `tasks`
| Column | Type | Description |
|---|---|---|
| task_id | STRING | PK |
| tenant_id | STRING | |
| meeting_id | STRING | FK |
| project_id | STRING | FK |
| task_title | STRING | |
| task_description | STRING | |
| owner | STRING | |
| owner_email | STRING | |
| due_date | DATE | |
| status | STRING | NOT_STARTED / IN_PROGRESS / DONE / UNKNOWN |
| priority | STRING | LOW / MEDIUM / HIGH |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |
| source_sentence | STRING | |

### `risks`
| Column | Type | Description |
|---|---|---|
| risk_id | STRING | PK |
| tenant_id | STRING | |
| meeting_id | STRING | FK |
| project_id | STRING | FK |
| risk_description | STRING | |
| risk_level | STRING | LOW / MEDIUM / HIGH |
| likelihood | STRING | OPTIONAL |
| impact | STRING | OPTIONAL |
| owner | STRING | |
| created_at | TIMESTAMP | |
| source_sentence | STRING | |

## 4. Vertex AI Extraction Design

**Model**: Gemini Flash (High speed, low cost).

**JSON Schema Strategy**: Use Structured Output to ensure valid JSON.

**Prompt Strategy**:
- Define "Meeting Purpose" and "Task vs Chat" boundaries.
- Input: Meeting Text, Meeting Date, Language.
- Output: Structured JSON.

**Date Logic**:
- LLM extracts `due_date_text` (e.g., "Next Friday").
- App logic normalizes to DATE based on `meeting_date`.
