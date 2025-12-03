# 1. Requirements Specification

## 1.1. Feature List

### Input Features
*   **Meeting Minutes Upload**: Upload Text or Markdown files containing meeting notes.
*   **Meeting Meta Information**: Input meeting date, title, and participants.
*   **[Future] External Integration**: Integration with Google Docs, Google Meet, Zoom, and Calendar.

### AI Analysis & DB Features
*   **Task Extraction**: Automatically extract tasks with content, owner, due date, priority, and status.
*   **Project Estimation & Linking**: Auto-classify multiple projects within a meeting.
*   **Risk / Decision Extraction**: Extract risks (description, level, owner) and decisions.
*   **"Risk-like" Utterance Extraction**: Link original utterances to extracted risks.
*   **Inter-meeting Diff Detection**: Detect new tasks, status changes, and escalated risks since the last meeting. *(Implemented)*

### View / Dashboard Features
*   **Project List**: View projects with uncompleted tasks, delayed tasks, risk counts, and last updated dates.
*   **Task View**: Filter tasks by project, owner, date range, and status. Special views for overdue and due-this-week tasks.
*   **Risk View**: List risks per project, sorted by level, with previews of original utterances.
*   **[Future] Management Health Score**: Project health scores and trend analysis.

### Output / Notification Features
*   **CSV / Excel Export**: Export projects, tasks, and risks to CSV/Excel.
*   **Email Generation**: Auto-generate "Top 10 Delayed/Risk Tasks of the Week" draft emails.
*   **[Future] Slack / Chat Notifications**: Alerts for high risks and overdue tasks.
*   **[Future] Next Meeting Agenda Generation**: Auto-generate agenda topics based on history.

### Management & Settings
*   **User Management**: Simple Google OAuth login.
*   **[Future] Roles & Permissions**: Admin, PM, Member roles.
*   **[Future] Audit Logs**: Track system usage and data access.

## 1.2. Functional Requirements

### FR-01: File Upload
*   **Description**: Users must be able to upload meeting notes in `.txt` or `.md` format.
*   **Input**: File selection, Meeting Date (mandatory).
*   **Processing**: File is saved to Cloud Storage; metadata is saved to BigQuery. Analysis is triggered asynchronously.

### FR-02: AI Analysis (Extraction)
*   **Description**: The system must use LLM (Vertex AI Gemini) to parse the uploaded text.
*   **Output**: Structured JSON containing Projects, Tasks, Risks, and Decisions.
*   **Logic**:
    *   Dates like "next Friday" must be normalized to absolute dates based on the Meeting Date.
    *   Tasks must be linked to specific projects.

### FR-03: Dashboard Display
*   **Description**: Users must be able to view extracted data in a dashboard format.
*   **Requirements**:
    *   Display list of projects with summary metrics.
    *   Allow drilling down into specific projects to see tasks and risks.
    *   Support filtering by Owner and Status.

### FR-04: Export
*   **Description**: Users must be able to download data for offline use.
*   **Format**: CSV files for Projects, Tasks, and Risks.

### FR-05: Email Draft Generation
*   **Description**: The system must generate a summary email for project managers.
*   **Content**: Top 10 delayed tasks and high-priority risks.

## 1.3. Non-functional Requirements

### NFR-01: Performance
*   **Response Time**: Dashboard loading should complete within 2 seconds.
*   **Analysis Time**: File analysis should complete within 1 minute for typical meeting notes (approx. 1 hour meeting).

### NFR-02: Security
*   **Authentication**: All access must be authenticated via Google OAuth.
*   **Data Protection**: Data must be stored in the user's/customer's GCP environment (BigQuery/GCS).

### NFR-03: Availability
*   **Uptime**: The system relies on serverless GCP components (Cloud Run, BigQuery), inheriting their high availability.

### NFR-04: Maintainability
*   **Infrastructure**: Infrastructure must be managed as code (Terraform).
*   **Codebase**: Backend in Python (FastAPI), Frontend in TypeScript (Next.js).

### NFR-05: Scalability
*   **Volume**: The system should handle hundreds of projects and thousands of tasks without significant performance degradation (leveraging BigQuery).
