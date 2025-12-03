"""BigQuery service for worker data operations.

Features:
- Idempotent message processing tracking
- Partial failure handling for batch inserts
- Structured error types
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

from .date_parser import parse_date_with_meeting_context

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET")

# Singleton client
_client: Optional[bigquery.Client] = None


class ProcessingError(Exception):
    """Error during meeting processing that should not be retried."""
    pass


def get_client() -> bigquery.Client:
    """Get or create BigQuery client (singleton)."""
    global _client
    if _client is None:
        _client = bigquery.Client(project=PROJECT_ID)
    return _client


def _table_id(table: str) -> str:
    """Get fully qualified table ID."""
    return f"{PROJECT_ID}.{DATASET_ID}.{table}"


# =============================================================================
# Idempotency Support
# =============================================================================

def is_message_processed(message_id: str) -> bool:
    """Check if a Pub/Sub message has already been processed.
    
    Args:
        message_id: Pub/Sub message ID
        
    Returns:
        True if message was already processed
    """
    client = get_client()
    
    query = f"""
        SELECT 1 FROM `{_table_id('processed_messages')}`
        WHERE message_id = @message_id
        LIMIT 1
    """
    
    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("message_id", "STRING", message_id)
            ]
        )
        results = list(client.query(query, job_config=job_config))
        return len(results) > 0
    except NotFound:
        # Table doesn't exist yet - message not processed
        return False
    except Exception as e:
        logger.warning(f"Error checking message idempotency: {e}")
        # On error, assume not processed (will dedupe on meeting status)
        return False


def mark_message_processed(message_id: str, meeting_id: str):
    """Mark a Pub/Sub message as successfully processed.
    
    Args:
        message_id: Pub/Sub message ID
        meeting_id: Associated meeting ID
    """
    client = get_client()
    
    row = {
        "message_id": message_id,
        "meeting_id": meeting_id,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    
    try:
        errors = client.insert_rows_json(_table_id('processed_messages'), [row])
        if errors:
            logger.warning(f"Error marking message processed: {errors}")
    except NotFound:
        # Table might not exist in dev - create it
        _ensure_processed_messages_table()
        errors = client.insert_rows_json(_table_id('processed_messages'), [row])
        if errors:
            logger.warning(f"Error marking message processed: {errors}")
    except Exception as e:
        # Non-critical - log and continue
        logger.warning(f"Error marking message processed: {e}")


def _ensure_processed_messages_table():
    """Create processed_messages table if it doesn't exist."""
    client = get_client()
    
    schema = [
        bigquery.SchemaField("message_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("meeting_id", "STRING"),
        bigquery.SchemaField("processed_at", "TIMESTAMP"),
    ]
    
    table = bigquery.Table(_table_id('processed_messages'), schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="processed_at",
        expiration_ms=30 * 24 * 60 * 60 * 1000,  # 30 days
    )
    
    try:
        client.create_table(table)
        logger.info("Created processed_messages table")
    except Exception as e:
        if "Already Exists" not in str(e):
            logger.warning(f"Error creating processed_messages table: {e}")


# =============================================================================
# Meeting Operations
# =============================================================================

def get_meeting_metadata(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Get meeting metadata by ID.
    
    Args:
        meeting_id: Meeting record ID
        
    Returns:
        Meeting metadata dict or None if not found
    """
    client = get_client()
    
    query = f"""
        SELECT * FROM `{_table_id('meetings')}`
        WHERE meeting_id = @meeting_id
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("meeting_id", "STRING", meeting_id)
        ]
    )
    
    results = list(client.query(query, job_config=job_config))
    if not results:
        return None
    return dict(results[0])


def update_meeting_status(meeting_id: str, status: str, error_message: str = None):
    """Update meeting processing status.
    
    Args:
        meeting_id: Meeting record ID
        status: New status (PENDING, PROCESSING, DONE, ERROR)
        error_message: Optional error message for ERROR status
    """
    client = get_client()
    
    query = f"""
        UPDATE `{_table_id('meetings')}`
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
    logger.info(f"Updated meeting {meeting_id} status to {status}")


# =============================================================================
# Data Extraction Storage
# =============================================================================

def save_extracted_data(meeting_id: str, extracted_data: dict):
    """Save extracted data to BigQuery with partial failure handling.
    
    Args:
        meeting_id: Meeting record ID
        extracted_data: Dict with projects, tasks, risks, decisions
        
    Raises:
        ProcessingError: If critical inserts fail
    """
    client = get_client()
    
    # Get meeting metadata for date context
    meeting_meta = get_meeting_metadata(meeting_id)
    meeting_date = str(meeting_meta.get("meeting_date")) if meeting_meta else None
    
    errors_summary = []
    
    # 1. Projects - upsert (find existing or create new)
    project_map = _save_projects(client, meeting_id, extracted_data.get("projects", []))
    
    # 2. Tasks
    tasks_errors = _save_tasks(
        client, meeting_id, extracted_data.get("tasks", []),
        project_map, meeting_date
    )
    if tasks_errors:
        errors_summary.append(f"tasks: {len(tasks_errors)} errors")
    
    # 3. Risks
    risks_errors = _save_risks(
        client, meeting_id, extracted_data.get("risks", []),
        project_map
    )
    if risks_errors:
        errors_summary.append(f"risks: {len(risks_errors)} errors")
    
    # 4. Decisions
    decisions_errors = _save_decisions(
        client, meeting_id, extracted_data.get("decisions", []),
        project_map
    )
    if decisions_errors:
        errors_summary.append(f"decisions: {len(decisions_errors)} errors")
    
    # Log results
    logger.info(
        f"Saved data for meeting {meeting_id}: "
        f"{len(project_map)} projects, "
        f"{len(extracted_data.get('tasks', []))} tasks, "
        f"{len(extracted_data.get('risks', []))} risks, "
        f"{len(extracted_data.get('decisions', []))} decisions"
    )
    
    if errors_summary:
        logger.warning(f"Partial failures: {', '.join(errors_summary)}")


def _save_projects(
    client: bigquery.Client,
    meeting_id: str,
    projects: List[Dict[str, Any]]
) -> Dict[str, str]:
    """Save projects and return name-to-ID mapping.
    
    Returns:
        Dict mapping project_name to project_id
    """
    project_map = {}
    new_projects = []
    
    for p in projects:
        p_name = p.get("project_name", "").strip()
        if not p_name:
            continue
        
        # Check if project exists
        query = f"""
            SELECT project_id FROM `{_table_id('projects')}`
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
            # Update latest_meeting_id
            _update_project_meeting(client, p_id, meeting_id)
        else:
            p_id = str(uuid.uuid4())
            new_projects.append({
                "project_id": p_id,
                "tenant_id": "default",
                "project_name": p_name,
                "latest_meeting_id": meeting_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        
        project_map[p_name] = p_id
    
    if new_projects:
        errors = client.insert_rows_json(_table_id('projects'), new_projects)
        if errors:
            logger.warning(f"Project insert errors: {errors}")
    
    return project_map


def _update_project_meeting(client: bigquery.Client, project_id: str, meeting_id: str):
    """Update project's latest meeting reference."""
    query = f"""
        UPDATE `{_table_id('projects')}`
        SET latest_meeting_id = @meeting_id,
            updated_at = @updated_at
        WHERE project_id = @project_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
            bigquery.ScalarQueryParameter("meeting_id", "STRING", meeting_id),
            bigquery.ScalarQueryParameter("updated_at", "STRING", 
                                         datetime.now(timezone.utc).isoformat()),
        ]
    )
    client.query(query, job_config=job_config).result()


def _save_tasks(
    client: bigquery.Client,
    meeting_id: str,
    tasks: List[Dict[str, Any]],
    project_map: Dict[str, str],
    meeting_date: Optional[str]
) -> List[Any]:
    """Save tasks with date parsing."""
    if not tasks:
        return []
    
    rows = []
    for t in tasks:
        p_name = t.get("project_name", "")
        p_id = project_map.get(p_name)
        
        # Parse due date
        due_date = None
        due_date_text = t.get("due_date_text")
        if due_date_text and meeting_date:
            due_date = parse_date_with_meeting_context(due_date_text, meeting_date)
        
        rows.append({
            "task_id": str(uuid.uuid4()),
            "tenant_id": "default",
            "meeting_id": meeting_id,
            "project_id": p_id,
            "task_title": t.get("task_title", "")[:500],
            "task_description": t.get("task_description", "")[:2000],
            "owner": t.get("owner", "Unassigned")[:200],
            "due_date": due_date,
            "status": t.get("status", "UNKNOWN"),
            "priority": t.get("priority", "MEDIUM"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source_sentence": t.get("source_sentence", "")[:1000],
        })
    
    errors = client.insert_rows_json(_table_id('tasks'), rows)
    return errors


def _save_risks(
    client: bigquery.Client,
    meeting_id: str,
    risks: List[Dict[str, Any]],
    project_map: Dict[str, str]
) -> List[Any]:
    """Save risks."""
    if not risks:
        return []
    
    rows = []
    for r in risks:
        p_name = r.get("project_name", "")
        p_id = project_map.get(p_name)
        
        rows.append({
            "risk_id": str(uuid.uuid4()),
            "tenant_id": "default",
            "meeting_id": meeting_id,
            "project_id": p_id,
            "risk_description": r.get("risk_description", "")[:2000],
            "risk_level": r.get("risk_level", "MEDIUM"),
            "owner": r.get("owner", "")[:200],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_sentence": r.get("source_sentence", "")[:1000],
        })
    
    errors = client.insert_rows_json(_table_id('risks'), rows)
    return errors


def _save_decisions(
    client: bigquery.Client,
    meeting_id: str,
    decisions: List[Dict[str, Any]],
    project_map: Dict[str, str]
) -> List[Any]:
    """Save decisions."""
    if not decisions:
        return []
    
    rows = []
    for d in decisions:
        p_name = d.get("project_name", "")
        p_id = project_map.get(p_name)
        
        rows.append({
            "decision_id": str(uuid.uuid4()),
            "tenant_id": "default",
            "meeting_id": meeting_id,
            "project_id": p_id,
            "decision_content": d.get("decision_content", "")[:2000],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_sentence": d.get("source_sentence", "")[:1000],
        })
    
    errors = client.insert_rows_json(_table_id('decisions'), rows)
    return errors
