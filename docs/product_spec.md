# Product Specification: AI Meeting Minutes & Project Progress DB

## 1. Product Feature List

### 1-1. Input Features
*   **[MVP] Meeting Minutes Upload**
    *   Upload Text / Markdown files.
    *   Input meeting date (reference date for natural language deadlines).
*   **[MVP] Meeting Meta Information**
    *   Meeting Title.
    *   Participants (Text input).
*   **[Future] External Integration**
    *   Import from Google Docs / Google Drive.
    *   Transcript integration with Google Meet / Zoom.
    *   Auto-fetch meeting info from Calendar.

### 1-2. AI Analysis & DB Features
*   **[MVP] Task Extraction**
    *   Content, Owner, Due Date, Priority, Status.
*   **[MVP] Project Estimation & Linking**
    *   Auto-classify multiple projects within a meeting.
*   **[MVP] Risk / Decision Extraction**
    *   Risk description, Level (Low/Mid/High), Owner.
    *   Decisions (Agreed content) tabularized.
*   **[MVP] "Risk-like" Utterance Extraction**
    *   Link original utterance text to the risk.
*   **[Future] Inter-meeting Diff Detection**
    *   "New tasks since last time".
    *   "Status changed tasks".
    *   "Escalated risks".

### 1-3. View / Dashboard Features
*   **[MVP] Project List**
    *   Per project: Uncompleted tasks, Delayed tasks, Risk count, Last updated date.
*   **[MVP] Task View**
    *   Filters: Project, Owner, Date Range, Status.
    *   Special Views: Overdue tasks, Due this week.
*   **[MVP] Risk View**
    *   Risk list per project.
    *   Sort by Risk Level.
    *   Preview original utterance.
*   **[Future] Management Health Score**
    *   Project "Health Score".
    *   Delay trends (past n weeks).
    *   Risk trends (increase/decrease).

### 1-4. Output / Notification Features
*   **[MVP] CSV / Excel Export**
    *   projects.csv / tasks.csv / risks.csv.
    *   Export based on filter conditions.
*   **[MVP] "Top 10 Delayed/Risk Tasks of the Week" Email Generation**
    *   Auto-generate draft email for PMO/Managers.
*   **[Future] Slack / Chat Notifications**
    *   "New high risk detected", "Task overdue", etc.
*   **[Future] Next Meeting Agenda Generation**
    *   Auto-generate "Top 5 topics for next meeting".

### 1-5. Management & Settings
*   **[MVP] Simple User Management** (Google OAuth).
*   **[Future] Roles & Permissions** (Admin, PM, Member).
*   **[Future] Audit Logs**.

---

## 2. User Journeys

### Personas
*   **PM / PdM / PMO**: Organizes weekly meetings.
*   **Member**: Task owner.
*   **Manager / Exec**: Oversees multiple projects.

### Journey 1: PM Perspective (1 Project, 1 Week)
1.  **Pre-meeting**: Check dashboard for delayed tasks/high risks. Ask AI for agenda draft.
2.  **Post-meeting**: Upload minutes. AI proposes Tasks/Risks/Decisions. Review and "Confirm to DB".
3.  **Mid-week**: Check dashboard (filter by "Due this week", "Owner"). Click task to see original context.
4.  **Weekend**: Generate "Weekly Delay/Risk Top 10" email. Edit and send.

### Journey 2: Executive Perspective (Multi-project Overview)
1.  **Login**: View "All Projects".
2.  **Sort**: By "Risk Level".
3.  **Drill-down**: Click a project to see delayed tasks, high risks, decisions.
4.  **Ask AI**: "Where is this project stuck?" -> AI answers (e.g., "Testing phase is bottleneck").

---

## 3. Differentiation Features (The "Edge")

1.  **Cross-Meeting "Task/Risk History Timeline"**: Track task lifecycle across meetings (First mentioned -> Discussed -> Completed).
2.  **"Risk-like Score" Ranking**: Score utterances (0-1) to catch "bad feelings" or subtle risks.
3.  **Natural Language DB Query**: "Show me tasks due this month for Project A" -> AI converts to BigQuery -> Result.
4.  **AI-Proposed "Next Meeting Agenda"**: Based on recent history.
5.  **BigQuery Native & Customer GCP**: Data stays in customer's GCP. Easy JOIN with other data.
6.  **Japanese Business Context Tuning**: Reading "between the lines" (e.g., "pending", "homework", vague refusals).

---

## 4. "Willingness to Pay" Elements

*   **PM**: Drastic reduction in manual entry. No dropped balls. Instant task list after meeting. AI verbalization of bottlenecks.
*   **Manager**: One-screen overview of delays/risks. Copy-paste ready reports. Audit trail of "why it delayed".
*   **IT/Security**: Data stays in GCP. Access control. SSO integration.

---

## 5. Customization Points

*   **5-1. Terms/Rules**: Task types, Risk categories, Status names, Risk level definitions.
*   **5-2. Dashboard**: Aggregation axis (Project/Team/Client). Custom Home (PM vs Member vs Exec). Column toggle.
*   **5-3. AI Logic**: "Task vs Chat" threshold. Custom keywords. Feedback loop learning.
*   **5-4. Notifications**: Alert timing, Risk level thresholds.

---

## 6. AI-Native Refinements

*   **6-1. Chat + Dashboard Hybrid**: Always-on "Progress DB Bot".
*   **6-2. Proactive AI**: Weekly "Insight Report" (e.g., "Testing delay trend detected").
*   **6-3. Pre-meeting Insights**: "Decisions needed today" list.
*   **6-4. Feedback Loop UI**: User corrections train the tenant-specific model.
*   **6-5. Explainable AI**: AI explains *why* it extracted a task/risk.
