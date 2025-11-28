# 2. Use Case Definition

## 2.1. Use Case Diagram

```mermaid
usecaseDiagram
    actor "PM / PMO" as PM
    actor "Member" as Member
    actor "Executive" as Exec

    package "Project Progress DB" {
        usecase "Upload Meeting Minutes" as UC1
        usecase "View Dashboard" as UC2
        usecase "Check Delayed Tasks" as UC3
        usecase "Check Risks" as UC4
        usecase "Generate Weekly Report" as UC5
        usecase "Export Data" as UC6
    }

    PM --> UC1
    PM --> UC2
    PM --> UC3
    PM --> UC4
    PM --> UC5
    PM --> UC6

    Member --> UC2
    Member --> UC3

    Exec --> UC2
    Exec --> UC4
```

## 2.2. Use Case Descriptions

### UC-01: Upload Meeting Minutes
*   **Actor**: PM / PMO
*   **Goal**: Input meeting data into the system for analysis.
*   **Precondition**: User is logged in.
*   **Main Flow**:
    1.  User navigates to the "Upload" page.
    2.  User selects a text/markdown file.
    3.  User specifies the "Meeting Date".
    4.  User clicks "Upload".
    5.  System uploads file and triggers AI analysis.
    6.  System displays "Analysis In Progress" status.
*   **Postcondition**: Data is stored in BigQuery and visible on the dashboard.

### UC-02: View Dashboard
*   **Actor**: All Users
*   **Goal**: Get an overview of project status.
*   **Main Flow**:
    1.  User logs in.
    2.  System displays the "Project List" view.
    3.  User sees metrics for each project (Uncompleted Tasks, Risks).

### UC-03: Check Delayed Tasks
*   **Actor**: PM, Member
*   **Goal**: Identify tasks that are behind schedule.
*   **Main Flow**:
    1.  User navigates to "Task View".
    2.  User applies filter "Status: Overdue" or sorts by Due Date.
    3.  System displays list of delayed tasks.
    4.  User clicks a task to see the original context (utterance).

### UC-04: Generate Weekly Report
*   **Actor**: PM
*   **Goal**: Create a status report for stakeholders.
*   **Main Flow**:
    1.  User navigates to "Reports" or "Email Gen" section.
    2.  User clicks "Generate Weekly Summary".
    3.  System (AI) aggregates top delays and risks and generates an email draft.
    4.  User copies the draft for editing/sending.
