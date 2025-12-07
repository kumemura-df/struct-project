import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET")
USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "false").lower() == "true"

# Always import local_db (for functions that need it even in BigQuery mode)
from . import local_db


def get_client():
    if USE_LOCAL_DB:
        return None  # Not used in local mode
    return bigquery.Client(project=PROJECT_ID)


def _task_status_table_id() -> str:
    return f"{PROJECT_ID}.{DATASET_ID}.task_status"


def _risk_status_table_id() -> str:
    return f"{PROJECT_ID}.{DATASET_ID}.risk_status"


def _ensure_task_status_table():
    """Create task_status table if it doesn't exist (BigQuery only)."""
    client = get_client()
    table_id = _task_status_table_id()
    schema = [
        bigquery.SchemaField("task_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_by", "STRING"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.create_table(table)
    except Exception as e:
        if "Already Exists" not in str(e):
            print(f"[bigquery] task_status table check: {e}")


def _ensure_risk_status_table():
    """Create risk_status table if it doesn't exist (BigQuery only)."""
    client = get_client()
    table_id = _risk_status_table_id()
    schema = [
        bigquery.SchemaField("risk_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("risk_level", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_by", "STRING"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.create_table(table)
    except Exception as e:
        if "Already Exists" not in str(e):
            print(f"[bigquery] risk_status table check: {e}")


def _get_latest_task_statuses(task_ids: List[str]) -> Dict[str, str]:
    """Get latest status per task_id from task_status table."""
    if not task_ids:
        return {}
    
    client = get_client()
    query = f"""
        SELECT task_id, status, updated_at
        FROM `{_task_status_table_id()}`
        WHERE task_id IN UNNEST(@task_ids)
        ORDER BY task_id, updated_at DESC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("task_ids", "STRING", task_ids)
        ]
    )
    try:
        rows = client.query(query, job_config=job_config)
    except NotFound:
        # Status table not created yet
        return {}
    latest: Dict[str, str] = {}
    for row in rows:
        tid = row.task_id
        if tid not in latest:
            latest[tid] = row.status
    return latest


def _get_latest_risk_levels(risk_ids: List[str]) -> Dict[str, str]:
    """Get latest risk_level per risk_id from risk_status table."""
    if not risk_ids:
        return {}
    
    client = get_client()
    query = f"""
        SELECT risk_id, risk_level, updated_at
        FROM `{_risk_status_table_id()}`
        WHERE risk_id IN UNNEST(@risk_ids)
        ORDER BY risk_id, updated_at DESC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("risk_ids", "STRING", risk_ids)
        ]
    )
    try:
        rows = client.query(query, job_config=job_config)
    except NotFound:
        return {}
    latest: Dict[str, str] = {}
    for row in rows:
        rid = row.risk_id
        if rid not in latest:
            latest[rid] = row.risk_level
    return latest


# ===== SINGLE RECORD GET =====

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get a single task by ID, applying latest status override if present."""
    if USE_LOCAL_DB:
        return local_db.get_task(task_id)
    
    client = get_client()
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.tasks`
        WHERE task_id = @task_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("task_id", "STRING", task_id)]
    )
    result = list(client.query(query, job_config=job_config))
    if not result:
        return None
    
    task = dict(result[0])
    overrides = _get_latest_task_statuses([task_id])
    if task_id in overrides:
        task["status"] = overrides[task_id]
    return task


def get_risk(risk_id: str) -> Optional[Dict[str, Any]]:
    """Get a single risk by ID, applying latest risk_level override if present."""
    if USE_LOCAL_DB:
        return local_db.get_risk(risk_id)
    
    client = get_client()
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.risks`
        WHERE risk_id = @risk_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("risk_id", "STRING", risk_id)]
    )
    result = list(client.query(query, job_config=job_config))
    if not result:
        return None
    
    risk = dict(result[0])
    overrides = _get_latest_risk_levels([risk_id])
    if risk_id in overrides:
        risk["risk_level"] = overrides[risk_id]
    return risk


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Get a single project by ID."""
    if USE_LOCAL_DB:
        return local_db.get_project(project_id)
    
    client = get_client()
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.projects`
        WHERE project_id = @project_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("project_id", "STRING", project_id)]
    )
    result = list(client.query(query, job_config=job_config))
    return dict(result[0]) if result else None


def get_decision(decision_id: str) -> Optional[Dict[str, Any]]:
    """Get a single decision by ID."""
    if USE_LOCAL_DB:
        return local_db.get_decision(decision_id)
    
    client = get_client()
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.decisions`
        WHERE decision_id = @decision_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("decision_id", "STRING", decision_id)]
    )
    result = list(client.query(query, job_config=job_config))
    return dict(result[0]) if result else None


# ===== UPDATE FUNCTIONS =====

def update_task(task_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a task.
    
    Local DB: delegate to local_db.
    BigQuery: append status changes to task_status table (no DML on tasks table).
    """
    if USE_LOCAL_DB:
        return local_db.update_task(task_id, updates, user_id)
    
    if not updates:
        return get_task(task_id)
    
    # For BigQuery we only support status changes for now to avoid DML on
    # tables that receive streaming inserts (BigQuery restriction).
    status = updates.get("status")
    other_updates = {k: v for k, v in updates.items() if k != "status" and v is not None}
    
    if other_updates:
        raise NotImplementedError("Only status updates are supported for tasks in BigQuery backend")
    
    if status is None:
        return get_task(task_id)
    
    client = get_client()
    _ensure_task_status_table()
    
    row = {
        "task_id": task_id,
        "status": status,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": user_id or "",
    }
    errors = client.insert_rows_json(_task_status_table_id(), [row])
    if errors:
        raise Exception(f"Failed to insert task status: {errors}")
    
    # Return task with latest status applied
    return get_task(task_id)


def update_risk(risk_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a risk.
    
    Local DB: delegate to local_db.
    BigQuery: append risk_level changes to risk_status table.
    """
    if USE_LOCAL_DB:
        return local_db.update_risk(risk_id, updates, user_id)
    
    if not updates:
        return get_risk(risk_id)
    
    new_level = updates.get("risk_level")
    other_updates = {k: v for k, v in updates.items() if k != "risk_level" and v is not None}
    
    if other_updates:
        raise NotImplementedError("Only risk_level updates are supported for risks in BigQuery backend")
    
    if new_level is None:
        return get_risk(risk_id)
    
    client = get_client()
    _ensure_risk_status_table()
    
    row = {
        "risk_id": risk_id,
        "risk_level": new_level,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": user_id or "",
    }
    errors = client.insert_rows_json(_risk_status_table_id(), [row])
    if errors:
        raise Exception(f"Failed to insert risk status: {errors}")
    
    return get_risk(risk_id)


def update_project(project_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a project in BigQuery."""
    if USE_LOCAL_DB:
        return local_db.update_project(project_id, updates, user_id)
    
    if not updates:
        return get_project(project_id)
    
    client = get_client()
    set_clauses: List[str] = []
    params: List[bigquery.ScalarQueryParameter] = []
    
    # Only project_name is expected at the moment
    for key, value in updates.items():
        if value is None:
            continue
        if key == "project_name":
            set_clauses.append("project_name = @project_name")
            params.append(bigquery.ScalarQueryParameter("project_name", "STRING", value))
    
    # Always bump updated_at if we are updating anything
    if set_clauses:
        set_clauses.append("updated_at = CURRENT_TIMESTAMP()")
    
    if not set_clauses:
        return get_project(project_id)
    
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.projects`
        SET {', '.join(set_clauses)}
        WHERE project_id = @project_id
    """
    params.append(bigquery.ScalarQueryParameter("project_id", "STRING", project_id))
    
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    job = client.query(query, job_config=job_config)
    job.result()
    
    if not job.num_dml_affected_rows:
        return None
    
    return get_project(project_id)


def update_decision(decision_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a decision in BigQuery.
    
    Note: DecisionUpdate uses `decision_description`, which maps to the
    `decision_content` column in BigQuery. Other fields are currently ignored
    because they don't exist in the physical schema.
    """
    if USE_LOCAL_DB:
        return local_db.update_decision(decision_id, updates, user_id)
    
    if not updates:
        return get_decision(decision_id)
    
    client = get_client()
    set_clauses: List[str] = []
    params: List[bigquery.ScalarQueryParameter] = []
    
    # Map logical field names to physical columns
    description = updates.get("decision_description")
    if description is not None:
        set_clauses.append("decision_content = @decision_content")
        params.append(bigquery.ScalarQueryParameter("decision_content", "STRING", description))
    
    if not set_clauses:
        return get_decision(decision_id)
    
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.decisions`
        SET {', '.join(set_clauses)}
        WHERE decision_id = @decision_id
    """
    params.append(bigquery.ScalarQueryParameter("decision_id", "STRING", decision_id))
    
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    job = client.query(query, job_config=job_config)
    job.result()
    
    if not job.num_dml_affected_rows:
        return None
    
    return get_decision(decision_id)


# ===== DELETE FUNCTIONS =====

def delete_task(task_id: str, user_id: Optional[str] = None) -> bool:
    """Delete a task (hard delete in BigQuery, soft delete in local DB)."""
    if USE_LOCAL_DB:
        return local_db.delete_task(task_id, user_id)
    
    client = get_client()
    query = f"""
        DELETE FROM `{PROJECT_ID}.{DATASET_ID}.tasks`
        WHERE task_id = @task_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("task_id", "STRING", task_id)]
    )
    job = client.query(query, job_config=job_config)
    job.result()
    return bool(job.num_dml_affected_rows)


def delete_risk(risk_id: str, user_id: Optional[str] = None) -> bool:
    """Delete a risk (hard delete in BigQuery, soft delete in local DB)."""
    if USE_LOCAL_DB:
        return local_db.delete_risk(risk_id, user_id)
    
    client = get_client()
    query = f"""
        DELETE FROM `{PROJECT_ID}.{DATASET_ID}.risks`
        WHERE risk_id = @risk_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("risk_id", "STRING", risk_id)]
    )
    job = client.query(query, job_config=job_config)
    job.result()
    return bool(job.num_dml_affected_rows)


def delete_project(project_id: str, user_id: Optional[str] = None) -> bool:
    """Delete a project (hard delete in BigQuery, soft delete in local DB)."""
    if USE_LOCAL_DB:
        return local_db.delete_project(project_id, user_id)
    
    client = get_client()
    query = f"""
        DELETE FROM `{PROJECT_ID}.{DATASET_ID}.projects`
        WHERE project_id = @project_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("project_id", "STRING", project_id)]
    )
    job = client.query(query, job_config=job_config)
    job.result()
    return bool(job.num_dml_affected_rows)


def delete_decision(decision_id: str, user_id: Optional[str] = None) -> bool:
    """Delete a decision (hard delete in BigQuery, soft delete in local DB)."""
    if USE_LOCAL_DB:
        return local_db.delete_decision(decision_id, user_id)
    
    client = get_client()
    query = f"""
        DELETE FROM `{PROJECT_ID}.{DATASET_ID}.decisions`
        WHERE decision_id = @decision_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("decision_id", "STRING", decision_id)]
    )
    job = client.query(query, job_config=job_config)
    job.result()
    return bool(job.num_dml_affected_rows)


# ===== PAGINATED LIST FUNCTIONS =====

def list_tasks_paginated(
    project_id: Optional[str] = None,
    status: Optional[List[str]] = None,
    priority: Optional[List[str]] = None,
    owner: Optional[str] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "due_date",
    sort_order: str = "asc",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """List tasks with pagination, filtering, search, and sorting."""
    if USE_LOCAL_DB:
        return local_db.list_tasks_paginated(
            project_id=project_id,
            status=status,
            priority=priority,
            owner=owner,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
    
    # For BigQuery, use existing list_tasks but wrap with pagination and apply
    # latest status overrides from task_status.
    tasks = list_tasks(project_id)
    total = len(tasks)
    page = tasks[offset:offset + limit]
    if page:
        overrides = _get_latest_task_statuses([t["task_id"] for t in page if "task_id" in t])
        for t in page:
            tid = t.get("task_id")
            if tid and tid in overrides:
                t["status"] = overrides[tid]
    return {
        "items": page,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


def list_risks_paginated(
    project_id: Optional[str] = None,
    meeting_id: Optional[str] = None,
    risk_level: Optional[List[str]] = None,
    owner: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """List risks with pagination, filtering, search, and sorting."""
    if USE_LOCAL_DB:
        return local_db.list_risks_paginated(
            project_id=project_id,
            meeting_id=meeting_id,
            risk_level=risk_level,
            owner=owner,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
    
    # For BigQuery, use existing list_risks but wrap with pagination and apply
    # latest risk_level overrides from risk_status.
    risk_level_single = risk_level[0] if risk_level and len(risk_level) == 1 else None
    risks = list_risks(project_id, risk_level_single, meeting_id)
    total = len(risks)
    page = risks[offset:offset + limit]
    if page:
        overrides = _get_latest_risk_levels([r["risk_id"] for r in page if "risk_id" in r])
        for r in page:
            rid = r.get("risk_id")
            if rid and rid in overrides:
                r["risk_level"] = overrides[rid]
    return {
        "items": page,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


def list_projects_paginated(
    search: Optional[str] = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """List projects with pagination, search, and sorting."""
    if USE_LOCAL_DB:
        return local_db.list_projects_paginated(
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
    
    projects = list_projects()
    total = len(projects)
    return {
        "items": projects[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


def list_decisions_paginated(
    project_id: Optional[str] = None,
    meeting_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """List decisions with pagination, filtering, search, and sorting."""
    if USE_LOCAL_DB:
        return local_db.list_decisions_paginated(
            project_id=project_id,
            meeting_id=meeting_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
    
    decisions = list_decisions(project_id, meeting_id)
    total = len(decisions)
    return {
        "items": decisions[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


# ===== SEARCH FUNCTION =====

def search_all(query: str, limit: int = 20) -> Dict[str, List[Dict[str, Any]]]:
    """Search across all entities."""
    if USE_LOCAL_DB:
        return local_db.search_all(query, limit)
    
    # BigQuery full-text search would require different implementation
    return {"tasks": [], "risks": [], "projects": [], "decisions": []}


# ===== AUDIT LOG =====

def get_audit_log(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get audit log entries."""
    if USE_LOCAL_DB:
        return local_db.get_audit_log(entity_type, entity_id, limit, offset)
    
    return []  # Not implemented for BigQuery

def insert_meeting_metadata(meeting_data: Dict[str, Any]):
    if USE_LOCAL_DB:
        return local_db.insert_meeting_metadata(meeting_data)

    client = get_client()
    table_id = f"{PROJECT_ID}.{DATASET_ID}.meetings"
    errors = client.insert_rows_json(table_id, [meeting_data])
    if errors:
        raise Exception(f"Encountered errors while inserting rows: {errors}")

def list_projects() -> List[Dict[str, Any]]:
    """List all projects with parameterized query."""
    if USE_LOCAL_DB:
        return local_db.list_projects()

    client = get_client()
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.projects`
        ORDER BY updated_at DESC
    """
    query_job = client.query(query)
    return [dict(row) for row in query_job]

def list_tasks(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List tasks, optionally filtered by project_id using parameterized query."""
    if USE_LOCAL_DB:
        return local_db.list_tasks(project_id)

    client = get_client()
    
    if project_id:
        query = f"""
            SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.tasks`
            WHERE project_id = @project_id
            ORDER BY due_date ASC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_id", "STRING", project_id)
            ]
        )
        query_job = client.query(query, job_config=job_config)
    else:
        query = f"""
            SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.tasks`
            ORDER BY due_date ASC
        """
        query_job = client.query(query)
    
    return [dict(row) for row in query_job]

def list_risks(
    project_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    meeting_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List risks with optional filtering using parameterized query."""
    if USE_LOCAL_DB:
        return local_db.list_risks(project_id, risk_level, meeting_id)

    client = get_client()
    
    where_clauses = []
    query_params = []
    
    if project_id:
        where_clauses.append("project_id = @project_id")
        query_params.append(bigquery.ScalarQueryParameter("project_id", "STRING", project_id))
    
    if risk_level:
        where_clauses.append("risk_level = @risk_level")
        query_params.append(bigquery.ScalarQueryParameter("risk_level", "STRING", risk_level))
    
    if meeting_id:
        where_clauses.append("meeting_id = @meeting_id")
        query_params.append(bigquery.ScalarQueryParameter("meeting_id", "STRING", meeting_id))
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.risks`
        {where_clause}
        ORDER BY created_at DESC
    """
    
    if query_params:
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
    else:
        query_job = client.query(query)
    
    return [dict(row) for row in query_job]

def list_decisions(
    project_id: Optional[str] = None,
    meeting_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List decisions with optional filtering using parameterized query."""
    if USE_LOCAL_DB:
        return local_db.list_decisions(project_id, meeting_id)

    client = get_client()
    
    where_clauses = []
    query_params = []
    
    if project_id:
        where_clauses.append("project_id = @project_id")
        query_params.append(bigquery.ScalarQueryParameter("project_id", "STRING", project_id))
    
    if meeting_id:
        where_clauses.append("meeting_id = @meeting_id")
        query_params.append(bigquery.ScalarQueryParameter("meeting_id", "STRING", meeting_id))
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.decisions`
        {where_clause}
        ORDER BY created_at DESC
    """
    
    if query_params:
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
    else:
        query_job = client.query(query)
    
    return [dict(row) for row in query_job]

def list_meetings_paginated(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """List meetings with pagination, filtering, search, and sorting."""
    if USE_LOCAL_DB:
        return local_db.list_meetings_paginated(
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
    
    client = get_client()
    
    where_clauses = []
    query_params = []
    
    if status:
        where_clauses.append("status = @status")
        query_params.append(bigquery.ScalarQueryParameter("status", "STRING", status))
    
    if search:
        where_clauses.append("(title LIKE @search OR meeting_id LIKE @search)")
        query_params.append(bigquery.ScalarQueryParameter("search", "STRING", f"%{search}%"))
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    # Validate sort_by
    allowed_sort = ["created_at", "meeting_date", "title", "status"]
    if sort_by not in allowed_sort:
        sort_by = "created_at"
    
    sort_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM `{PROJECT_ID}.{DATASET_ID}.meetings` {where_clause}"
    if query_params:
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        count_job = client.query(count_query, job_config=job_config)
    else:
        count_job = client.query(count_query)
    total = list(count_job)[0].total
    
    # Get items with extraction counts
    query = f"""
        SELECT 
            m.*,
            (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.tasks` t WHERE t.meeting_id = m.meeting_id) as task_count,
            (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.risks` r WHERE r.meeting_id = m.meeting_id) as risk_count,
            (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.decisions` d WHERE d.meeting_id = m.meeting_id) as decision_count
        FROM `{PROJECT_ID}.{DATASET_ID}.meetings` m
        {where_clause}
        ORDER BY {sort_by} {sort_direction}
        LIMIT {limit} OFFSET {offset}
    """
    
    if query_params:
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
    else:
        query_job = client.query(query)
    
    items = [dict(row) for row in query_job]
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


def get_meeting(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Get a single meeting by ID with extraction counts."""
    if USE_LOCAL_DB:
        return local_db.get_meeting(meeting_id)
    
    client = get_client()
    query = f"""
        SELECT 
            m.*,
            (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.tasks` t WHERE t.meeting_id = m.meeting_id) as task_count,
            (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.risks` r WHERE r.meeting_id = m.meeting_id) as risk_count,
            (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.decisions` d WHERE d.meeting_id = m.meeting_id) as decision_count
        FROM `{PROJECT_ID}.{DATASET_ID}.meetings` m
        WHERE m.meeting_id = @meeting_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("meeting_id", "STRING", meeting_id)]
    )
    result = list(client.query(query, job_config=job_config))
    return dict(result[0]) if result else None


def get_project_stats(project_id: str) -> Optional[Dict[str, Any]]:
    """Get statistics for a specific project."""
    if USE_LOCAL_DB:
        return local_db.get_project_stats(project_id)
    
    client = get_client()
    
    # Check if project exists
    check_query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.projects`
        WHERE project_id = @project_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("project_id", "STRING", project_id)]
    )
    check_result = list(client.query(check_query, job_config=job_config))
    if not check_result:
        return None
    
    # Get task statistics
    task_query = f"""
        SELECT 
            COUNT(*) as total_tasks,
            COUNTIF(status != 'DONE') as incomplete_tasks,
            COUNTIF(status != 'DONE' AND due_date IS NOT NULL AND due_date < CURRENT_DATE()) as overdue_tasks
        FROM `{PROJECT_ID}.{DATASET_ID}.tasks`
        WHERE project_id = @project_id
    """
    task_result = list(client.query(task_query, job_config=job_config))[0]
    
    # Get risk statistics by level
    risk_query = f"""
        SELECT risk_level, COUNT(*) as count
        FROM `{PROJECT_ID}.{DATASET_ID}.risks`
        WHERE project_id = @project_id
        GROUP BY risk_level
    """
    risk_result = client.query(risk_query, job_config=job_config)
    risks_by_level = {row.risk_level: row.count for row in risk_result}
    total_risks = sum(risks_by_level.values())
    
    # Get decision count
    decision_query = f"""
        SELECT COUNT(*) as count
        FROM `{PROJECT_ID}.{DATASET_ID}.decisions`
        WHERE project_id = @project_id
    """
    decision_result = list(client.query(decision_query, job_config=job_config))[0]
    
    return {
        "project_id": project_id,
        "total_tasks": task_result.total_tasks,
        "incomplete_tasks": task_result.incomplete_tasks,
        "overdue_tasks": task_result.overdue_tasks,
        "total_risks": total_risks,
        "risks_by_level": risks_by_level,
        "total_decisions": decision_result.count,
    }


def get_risk_stats() -> Dict[str, Any]:
    """Get risk statistics (count by level, by project)."""
    if USE_LOCAL_DB:
        return local_db.get_risk_stats()

    client = get_client()
    
    # Count by risk level
    level_query = f"""
        SELECT risk_level, COUNT(*) as count
        FROM `{PROJECT_ID}.{DATASET_ID}.risks`
        GROUP BY risk_level
        ORDER BY risk_level
    """
    level_job = client.query(level_query)
    by_level = {row.risk_level: row.count for row in level_job}
    
    # Count by project
    project_query = f"""
        SELECT r.project_id, p.project_name, COUNT(*) as count
        FROM `{PROJECT_ID}.{DATASET_ID}.risks` r
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.projects` p ON r.project_id = p.project_id
        WHERE r.project_id IS NOT NULL
        GROUP BY r.project_id, p.project_name
        ORDER BY count DESC
        LIMIT 10
    """
    project_job = client.query(project_query)
    by_project = [
        {"project_id": row.project_id, "project_name": row.project_name, "count": row.count}
        for row in project_job
    ]
    
    # Total count
    total_query = f"SELECT COUNT(*) as total FROM `{PROJECT_ID}.{DATASET_ID}.risks`"
    total_job = client.query(total_query)
    total = list(total_job)[0].total
    
    return {
        "total": total,
        "by_level": by_level,
        "by_project": by_project
    }


# ===== WEEKLY REPORT FUNCTIONS =====

def get_weekly_summary(start_date: str, end_date: str) -> Dict[str, Any]:
    """Get weekly summary statistics."""
    if USE_LOCAL_DB:
        return local_db.get_weekly_summary(start_date, end_date)
    
    client = get_client()
    
    # Task statistics
    task_query = f"""
        SELECT 
            COUNT(*) as total_tasks,
            COUNTIF(status != 'DONE') as incomplete_tasks,
            COUNTIF(status != 'DONE' AND due_date IS NOT NULL AND due_date < CURRENT_DATE()) as overdue_tasks
        FROM `{PROJECT_ID}.{DATASET_ID}.tasks`
    """
    task_result = list(client.query(task_query))[0]
    
    # High risk count
    risk_query = f"""
        SELECT COUNT(*) as high_risks
        FROM `{PROJECT_ID}.{DATASET_ID}.risks`
        WHERE risk_level = 'HIGH'
    """
    risk_result = list(client.query(risk_query))[0]
    
    # Decisions this week
    decision_query = f"""
        SELECT COUNT(*) as weekly_decisions
        FROM `{PROJECT_ID}.{DATASET_ID}.decisions`
        WHERE DATE(created_at) BETWEEN @start_date AND @end_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    decision_result = list(client.query(decision_query, job_config=job_config))[0]
    
    return {
        "total_tasks": task_result.total_tasks,
        "incomplete_tasks": task_result.incomplete_tasks,
        "overdue_tasks": task_result.overdue_tasks,
        "high_risks": risk_result.high_risks,
        "weekly_decisions": decision_result.weekly_decisions,
    }


def get_overdue_tasks(limit: int = 10, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get overdue tasks sorted by days overdue."""
    if USE_LOCAL_DB:
        return local_db.get_overdue_tasks(limit, project_id)
    
    client = get_client()
    
    where_clause = "WHERE status != 'DONE' AND due_date IS NOT NULL AND due_date < CURRENT_DATE()"
    query_params = []
    
    if project_id:
        where_clause += " AND t.project_id = @project_id"
        query_params.append(bigquery.ScalarQueryParameter("project_id", "STRING", project_id))
    
    query = f"""
        SELECT 
            t.*,
            p.project_name,
            DATE_DIFF(CURRENT_DATE(), DATE(t.due_date), DAY) as days_overdue
        FROM `{PROJECT_ID}.{DATASET_ID}.tasks` t
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.projects` p ON t.project_id = p.project_id
        {where_clause}
        ORDER BY days_overdue DESC
        LIMIT {limit}
    """
    
    if query_params:
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        result = client.query(query, job_config=job_config)
    else:
        result = client.query(query)
    
    return [dict(row) for row in result]


def get_high_risks(limit: int = 10, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get high and medium priority risks."""
    if USE_LOCAL_DB:
        return local_db.get_high_risks(limit, project_id)
    
    client = get_client()
    
    where_clause = "WHERE r.risk_level IN ('HIGH', 'MEDIUM')"
    query_params = []
    
    if project_id:
        where_clause += " AND r.project_id = @project_id"
        query_params.append(bigquery.ScalarQueryParameter("project_id", "STRING", project_id))
    
    query = f"""
        SELECT 
            r.*,
            p.project_name
        FROM `{PROJECT_ID}.{DATASET_ID}.risks` r
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.projects` p ON r.project_id = p.project_id
        {where_clause}
        ORDER BY 
            CASE r.risk_level WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
            r.created_at DESC
        LIMIT {limit}
    """
    
    if query_params:
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        result = client.query(query, job_config=job_config)
    else:
        result = client.query(query)
    
    return [dict(row) for row in result]


def get_recent_decisions(start_date: str, end_date: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent decisions within date range."""
    if USE_LOCAL_DB:
        return local_db.get_recent_decisions(start_date, end_date, limit)
    
    client = get_client()
    
    query = f"""
        SELECT 
            d.*,
            p.project_name
        FROM `{PROJECT_ID}.{DATASET_ID}.decisions` d
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.projects` p ON d.project_id = p.project_id
        WHERE DATE(d.created_at) BETWEEN @start_date AND @end_date
        ORDER BY d.created_at DESC
        LIMIT {limit}
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    result = client.query(query, job_config=job_config)
    
    return [dict(row) for row in result]


# ===== DIFF DETECTION FUNCTIONS =====

def get_meeting_diff_summary(meeting_id: str) -> Dict[str, Any]:
    """Get summary of changes since a meeting."""
    if USE_LOCAL_DB:
        return local_db.get_meeting_diff_summary(meeting_id)
    
    # For BigQuery, return empty as history tables not implemented
    return {
        "meeting_id": meeting_id,
        "new_tasks": {"count": 0, "items": []},
        "status_changes": {"count": 0, "items": []},
        "escalated_risks": {"count": 0, "items": []}
    }


def get_new_tasks_since_meeting(meeting_id: str) -> List[Dict[str, Any]]:
    """Get tasks created after the given meeting."""
    if USE_LOCAL_DB:
        return local_db.get_new_tasks_since_meeting(meeting_id)
    return []


def get_new_tasks_since_date(since_date: str) -> List[Dict[str, Any]]:
    """Get tasks created after the given date."""
    if USE_LOCAL_DB:
        conn = local_db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, p.project_name
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.project_id
            WHERE t.deleted_at IS NULL AND t.created_at > ?
            ORDER BY t.created_at DESC
        """, (since_date,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    return []


def get_status_changes_since_meeting(meeting_id: str) -> List[Dict[str, Any]]:
    """Get task status changes since the given meeting."""
    if USE_LOCAL_DB:
        return local_db.get_status_changes_since_meeting(meeting_id)
    return []


def get_status_changes_since_date(since_date: str) -> List[Dict[str, Any]]:
    """Get task status changes since the given date."""
    if USE_LOCAL_DB:
        conn = local_db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                h.*,
                t.task_title,
                t.owner,
                p.project_name
            FROM task_history h
            JOIN tasks t ON h.task_id = t.task_id
            LEFT JOIN projects p ON t.project_id = p.project_id
            WHERE h.field_changed = 'status' AND h.changed_at > ?
            ORDER BY h.changed_at DESC
        """, (since_date,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    return []


def get_escalated_risks_since_meeting(meeting_id: str) -> List[Dict[str, Any]]:
    """Get risks that escalated since the given meeting."""
    if USE_LOCAL_DB:
        return local_db.get_escalated_risks_since_meeting(meeting_id)
    return []


def get_escalated_risks_since_date(since_date: str) -> List[Dict[str, Any]]:
    """Get risks that escalated since the given date."""
    if USE_LOCAL_DB:
        conn = local_db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                h.*,
                r.risk_description,
                r.owner,
                p.project_name
            FROM risk_history h
            JOIN risks r ON h.risk_id = r.risk_id
            LEFT JOIN projects p ON r.project_id = p.project_id
            WHERE h.changed_at > ?
            AND (
                (h.old_level = 'LOW' AND h.new_level IN ('MEDIUM', 'HIGH'))
                OR (h.old_level = 'MEDIUM' AND h.new_level = 'HIGH')
            )
            ORDER BY h.changed_at DESC
        """, (since_date,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    return []


def get_task_lifecycle(task_id: str) -> Dict[str, Any]:
    """Get complete lifecycle of a task."""
    if USE_LOCAL_DB:
        return local_db.get_task_lifecycle(task_id)
    return {}


# ===== USER MANAGEMENT FUNCTIONS =====

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    if USE_LOCAL_DB:
        return local_db.get_user_by_email(email)
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    if USE_LOCAL_DB:
        return local_db.get_user_by_id(user_id)
    return None


def create_user(email: str, name: str, role: str = 'member', tenant_id: str = 'default') -> Dict[str, Any]:
    """Create a new user."""
    if USE_LOCAL_DB:
        return local_db.create_user(email, name, role, tenant_id)
    return {}


def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user fields."""
    if USE_LOCAL_DB:
        return local_db.update_user(user_id, updates)
    return None


def list_users(tenant_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List users with pagination."""
    if USE_LOCAL_DB:
        return local_db.list_users(tenant_id, limit, offset)
    return {"items": [], "total": 0, "limit": limit, "offset": offset}


def update_user_last_login(email: str):
    """Update user's last login timestamp."""
    if USE_LOCAL_DB:
        local_db.update_user_last_login(email)


# ===== AUDIT LOG FUNCTIONS =====

def create_audit_log(
    entity_type: str,
    entity_id: str,
    action: str,
    user_id: Optional[str] = None,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    details: Optional[Dict] = None
):
    """Create an audit log entry."""
    if USE_LOCAL_DB:
        local_db.create_audit_log(entity_type, entity_id, action, user_id, old_value, new_value, details)


def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Get audit logs with filtering."""
    if USE_LOCAL_DB:
        return local_db.get_audit_logs(entity_type, entity_id, user_id, limit, offset)
    return {"items": [], "total": 0, "limit": limit, "offset": offset}


# ===== HEALTH SCORE FUNCTIONS =====

def calculate_project_health_score(project_id: str) -> Dict[str, Any]:
    """Calculate health score for a project."""
    if USE_LOCAL_DB:
        return local_db.calculate_project_health_score(project_id)
    return {"project_id": project_id, "score": 0, "details": {}}


def save_health_score_snapshot(project_id: str, score_data: Dict[str, Any]) -> str:
    """Save a health score snapshot."""
    if USE_LOCAL_DB:
        return local_db.save_health_score_snapshot(project_id, score_data)
    return ""


def get_health_score_history(project_id: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Get health score history for a project."""
    if USE_LOCAL_DB:
        return local_db.get_health_score_history(project_id, limit)
    return []


def get_all_projects_health_scores() -> List[Dict[str, Any]]:
    """Get health scores for all projects."""
    if USE_LOCAL_DB:
        return local_db.get_all_projects_health_scores()
    return []
