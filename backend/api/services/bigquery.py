import os
from google.cloud import bigquery
from typing import List, Dict, Any, Optional

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET")
USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "false").lower() == "true"

# Import local_db if in local mode
if USE_LOCAL_DB:
    from . import local_db

def get_client():
    if USE_LOCAL_DB:
        return None  # Not used in local mode
    return bigquery.Client(project=PROJECT_ID)

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
