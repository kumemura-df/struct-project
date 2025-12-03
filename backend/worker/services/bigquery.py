import os
import uuid
from datetime import datetime
from google.cloud import bigquery
from typing import List, Dict, Any, Optional
from .date_parser import parse_date_with_meeting_context

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET")

def get_client():
    return bigquery.Client(project=PROJECT_ID)

def get_meeting_metadata(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Get meeting metadata by ID using parameterized query."""
    client = get_client()
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.meetings`
        WHERE meeting_id = @meeting_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("meeting_id", "STRING", meeting_id)
        ]
    )
    query_job = client.query(query, job_config=job_config)
    results = list(query_job)
    if not results:
        return None
    return dict(results[0])

def update_meeting_status(meeting_id: str, status: str, error_message: str = None):
    """Update meeting status using parameterized query."""
    client = get_client()
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.meetings`
        SET status = @status, error_message = @error_message
        WHERE meeting_id = @meeting_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("meeting_id", "STRING", meeting_id),
            bigquery.ScalarQueryParameter("status", "STRING", status),
            bigquery.ScalarQueryParameter("error_message", "STRING", error_message or ""),
        ]
    )
    client.query(query, job_config=job_config).result()

def save_extracted_data(meeting_id: str, extracted_data: dict):
    """Save extracted data to BigQuery with SQL injection protection and date parsing."""
    client = get_client()
    
    # Get meeting metadata for date context
    meeting_meta = get_meeting_metadata(meeting_id)
    meeting_date = str(meeting_meta.get("meeting_date")) if meeting_meta else None
    
    # 1. Projects
    projects_rows = []
    project_map = {} # project_name -> project_id
    
    for p in extracted_data.get("projects", []):
        p_name = p["project_name"]
        
        # Check if project exists using parameterized query
        query = f"""
            SELECT project_id FROM `{PROJECT_ID}.{DATASET_ID}.projects`
            WHERE project_name = @project_name
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_name", "STRING", p_name)
            ]
        )
        existing = list(client.query(query, job_config=job_config))
        
        if existing:
            p_id = existing[0].project_id
        else:
            p_id = str(uuid.uuid4())
            projects_rows.append({
                "project_id": p_id,
                "tenant_id": "default",
                "project_name": p_name,
                "latest_meeting_id": meeting_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
        project_map[p_name] = p_id

    if projects_rows:
        errors = client.insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.projects", projects_rows)
        if errors:
            print(f"Warning: Errors inserting projects: {errors}")

    # 2. Tasks with date parsing
    tasks_rows = []
    for t in extracted_data.get("tasks", []):
        p_name = t.get("project_name")
        p_id = project_map.get(p_name)
        
        # Parse due date
        due_date = None
        due_date_text = t.get("due_date_text")
        if due_date_text and meeting_date:
            due_date = parse_date_with_meeting_context(due_date_text, meeting_date)
        
        tasks_rows.append({
            "task_id": str(uuid.uuid4()),
            "tenant_id": "default",
            "meeting_id": meeting_id,
            "project_id": p_id,
            "task_title": t.get("task_title"),
            "task_description": t.get("task_description"),
            "owner": t.get("owner"),
            "due_date": due_date,
            "status": t.get("status", "UNKNOWN"),
            "priority": t.get("priority", "MEDIUM"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "source_sentence": t.get("source_sentence")
        })

    if tasks_rows:
        errors = client.insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.tasks", tasks_rows)
        if errors:
            raise Exception(f"BigQuery insert tasks error: {errors}")

    # 3. Risks
    risks_rows = []
    for r in extracted_data.get("risks", []):
        p_name = r.get("project_name")
        p_id = project_map.get(p_name)
        
        risks_rows.append({
            "risk_id": str(uuid.uuid4()),
            "tenant_id": "default",
            "meeting_id": meeting_id,
            "project_id": p_id,
            "risk_description": r.get("risk_description"),
            "risk_level": r.get("risk_level", "MEDIUM"),
            "owner": r.get("owner"),
            "created_at": datetime.utcnow().isoformat(),
            "source_sentence": r.get("source_sentence")
        })

    if risks_rows:
        errors = client.insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.risks", risks_rows)
        if errors:
            raise Exception(f"BigQuery insert risks error: {errors}")
    
    # 4. Decisions (FIXED: was missing)
    decisions_rows = []
    for d in extracted_data.get("decisions", []):
        p_name = d.get("project_name")
        p_id = project_map.get(p_name)
        
        decisions_rows.append({
            "decision_id": str(uuid.uuid4()),
            "tenant_id": "default",
            "meeting_id": meeting_id,
            "project_id": p_id,
            "decision_content": d.get("decision_content"),
            "created_at": datetime.utcnow().isoformat(),
            "source_sentence": d.get("source_sentence")
        })
    
    if decisions_rows:
        errors = client.insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.decisions", decisions_rows)
        if errors:
            raise Exception(f"BigQuery insert decisions error: {errors}")
    
    print(f"Successfully saved: {len(projects_rows)} projects, {len(tasks_rows)} tasks, "
          f"{len(risks_rows)} risks, {len(decisions_rows)} decisions")

    # Return stats for notification
    return {
        "projects_count": len(projects_rows),
        "tasks_count": len(tasks_rows),
        "risks_count": len(risks_rows),
        "decisions_count": len(decisions_rows)
    }


def get_setting(key: str) -> Optional[str]:
    """Get a setting value from BigQuery settings table."""
    client = get_client()
    query = f"""
        SELECT value FROM `{PROJECT_ID}.{DATASET_ID}.settings`
        WHERE key = @key
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("key", "STRING", key)
        ]
    )
    results = list(client.query(query, job_config=job_config))
    if results:
        return results[0].value
    return None


def get_high_risks() -> List[Dict[str, Any]]:
    """Get all HIGH level risks."""
    client = get_client()
    query = f"""
        SELECT r.*, p.project_name
        FROM `{PROJECT_ID}.{DATASET_ID}.risks` r
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.projects` p ON r.project_id = p.project_id
        WHERE r.risk_level = 'HIGH'
        ORDER BY r.created_at DESC
    """
    return [dict(row) for row in client.query(query)]
