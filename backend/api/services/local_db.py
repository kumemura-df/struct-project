"""Local SQLite database for development mode."""
import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "local.db")

def _get_connection():
    """Get SQLite connection and ensure tables exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    return conn

def _create_tables(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    cursor = conn.cursor()
    
    # Meetings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            meeting_id TEXT PRIMARY KEY,
            tenant_id TEXT,
            meeting_date TEXT,
            title TEXT,
            source_file_uri TEXT,
            language TEXT,
            created_at TEXT,
            status TEXT,
            error_message TEXT
        )
    """)
    
    # Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            tenant_id TEXT,
            project_name TEXT,
            latest_meeting_id TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            tenant_id TEXT,
            meeting_id TEXT,
            project_id TEXT,
            task_title TEXT,
            task_description TEXT,
            owner TEXT,
            owner_email TEXT,
            due_date TEXT,
            status TEXT,
            priority TEXT,
            created_at TEXT,
            updated_at TEXT,
            source_sentence TEXT
        )
    """)
    
    # Risks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risks (
            risk_id TEXT PRIMARY KEY,
            tenant_id TEXT,
            meeting_id TEXT,
            project_id TEXT,
            risk_description TEXT,
            risk_level TEXT,
            likelihood TEXT,
            impact TEXT,
            owner TEXT,
            created_at TEXT,
            source_sentence TEXT
        )
    """)
    
    # Decisions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id TEXT PRIMARY KEY,
            tenant_id TEXT,
            meeting_id TEXT,
            project_id TEXT,
            decision_description TEXT,
            decided_by TEXT,
            created_at TEXT,
            source_sentence TEXT
        )
    """)

    # Settings table (for Slack webhook, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    """)

    conn.commit()

def insert_meeting_metadata(meeting_data: Dict[str, Any]):
    """Insert meeting metadata."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO meetings (meeting_id, tenant_id, meeting_date, title, source_file_uri, 
                             language, created_at, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meeting_data["meeting_id"],
        meeting_data["tenant_id"],
        meeting_data["meeting_date"],
        meeting_data["title"],
        meeting_data["source_file_uri"],
        meeting_data["language"],
        meeting_data["created_at"],
        meeting_data["status"],
        meeting_data.get("error_message")
    ))
    
    conn.commit()
    conn.close()

def list_projects() -> List[Dict[str, Any]]:
    """List all projects."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def list_tasks(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List tasks, optionally filtered by project_id."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    if project_id:
        cursor.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY due_date ASC", (project_id,))
    else:
        cursor.execute("SELECT * FROM tasks ORDER BY due_date ASC")
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def list_risks(
    project_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    meeting_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List risks with optional filtering."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    where_clauses = []
    params = []
    
    if project_id:
        where_clauses.append("project_id = ?")
        params.append(project_id)
    
    if risk_level:
        where_clauses.append("risk_level = ?")
        params.append(risk_level)
    
    if meeting_id:
        where_clauses.append("meeting_id = ?")
        params.append(meeting_id)
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    query = f"SELECT * FROM risks {where_clause} ORDER BY created_at DESC"
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def list_decisions(
    project_id: Optional[str] = None,
    meeting_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List decisions with optional filtering."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    where_clauses = []
    params = []
    
    if project_id:
        where_clauses.append("project_id = ?")
        params.append(project_id)
    
    if meeting_id:
        where_clauses.append("meeting_id = ?")
        params.append(meeting_id)
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    query = f"SELECT * FROM decisions {where_clause} ORDER BY created_at DESC"
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def list_meetings(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List meetings, optionally filtered by project_id."""
    conn = _get_connection()
    cursor = conn.cursor()

    if project_id:
        # Get meetings that have tasks/risks for this project
        cursor.execute("""
            SELECT DISTINCT m.* FROM meetings m
            LEFT JOIN tasks t ON m.meeting_id = t.meeting_id
            LEFT JOIN risks r ON m.meeting_id = r.meeting_id
            WHERE t.project_id = ? OR r.project_id = ?
            ORDER BY m.meeting_date DESC
        """, (project_id, project_id))
    else:
        cursor.execute("SELECT * FROM meetings ORDER BY meeting_date DESC")

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_tasks_by_meeting(
    meeting_id: str,
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List tasks for a specific meeting."""
    conn = _get_connection()
    cursor = conn.cursor()

    if project_id:
        cursor.execute(
            "SELECT * FROM tasks WHERE meeting_id = ? AND project_id = ? ORDER BY due_date ASC",
            (meeting_id, project_id)
        )
    else:
        cursor.execute(
            "SELECT * FROM tasks WHERE meeting_id = ? ORDER BY due_date ASC",
            (meeting_id,)
        )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_risks_by_meeting(
    meeting_id: str,
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List risks for a specific meeting."""
    conn = _get_connection()
    cursor = conn.cursor()

    if project_id:
        cursor.execute(
            "SELECT * FROM risks WHERE meeting_id = ? AND project_id = ? ORDER BY created_at DESC",
            (meeting_id, project_id)
        )
    else:
        cursor.execute(
            "SELECT * FROM risks WHERE meeting_id = ? ORDER BY created_at DESC",
            (meeting_id,)
        )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_risk_stats() -> Dict[str, Any]:
    """Get risk statistics."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Count by risk level
    cursor.execute("SELECT risk_level, COUNT(*) as count FROM risks GROUP BY risk_level")
    by_level = {row["risk_level"]: row["count"] for row in cursor.fetchall()}
    
    # Count by project
    cursor.execute("""
        SELECT r.project_id, p.project_name, COUNT(*) as count
        FROM risks r
        LEFT JOIN projects p ON r.project_id = p.project_id
        WHERE r.project_id IS NOT NULL
        GROUP BY r.project_id, p.project_name
        ORDER BY count DESC
        LIMIT 10
    """)
    by_project = [
        {"project_id": row["project_id"], "project_name": row["project_name"], "count": row["count"]}
        for row in cursor.fetchall()
    ]
    
    # Total count
    cursor.execute("SELECT COUNT(*) as total FROM risks")
    total = cursor.fetchone()["total"]
    
    conn.close()
    
    return {
        "total": total,
        "by_level": by_level,
        "by_project": by_project
    }

def get_meeting_metadata(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Get meeting metadata by ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings WHERE meeting_id = ?", (meeting_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def update_meeting_status(meeting_id: str, status: str, error_message: str = None):
    """Update meeting status."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE meetings SET status = ?, error_message = ? WHERE meeting_id = ?",
        (status, error_message or "", meeting_id)
    )
    conn.commit()
    conn.close()

def save_extracted_data(meeting_id: str, extracted_data: dict):
    """
    Save extracted data to SQLite with duplicate checking and date parsing.
    
    Args:
        meeting_id: Meeting ID
        extracted_data: Dictionary with projects, tasks, risks, decisions
    """
    from . import ai_processor
    import uuid
    from datetime import datetime
    
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Get meeting metadata for date context
    meeting_meta = get_meeting_metadata(meeting_id)
    meeting_date = str(meeting_meta.get("meeting_date")) if meeting_meta else None
    
    # 1. Projects - check for duplicates
    project_map = {}  # project_name -> project_id
    
    for p in extracted_data.get("projects", []):
        p_name = p["project_name"]
        
        # Check if project exists
        cursor.execute("SELECT project_id FROM projects WHERE project_name = ? LIMIT 1", (p_name,))
        existing = cursor.fetchone()
        
        if existing:
            p_id = existing["project_id"]
        else:
            p_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO projects (project_id, tenant_id, project_name, latest_meeting_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                p_id,
                "default",
                p_name,
                meeting_id,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
        
        project_map[p_name] = p_id
    
    # 2. Tasks with date parsing
    for t in extracted_data.get("tasks", []):
        p_name = t.get("project_name")
        p_id = project_map.get(p_name)
        
        # Parse due date
        due_date = None
        due_date_text = t.get("due_date_text")
        if due_date_text and meeting_date:
            due_date = ai_processor.parse_date_with_meeting_context(due_date_text, meeting_date)
        
        cursor.execute("""
            INSERT INTO tasks (
                task_id, tenant_id, meeting_id, project_id, task_title, task_description,
                owner, owner_email, due_date, status, priority, created_at, updated_at, source_sentence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "default",
            meeting_id,
            p_id,
            t.get("task_title"),
            t.get("task_description"),
            t.get("owner"),
            None,  # owner_email not extracted yet
            due_date,
            t.get("status", "UNKNOWN"),
            t.get("priority", "MEDIUM"),
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            t.get("source_sentence")
        ))
    
    # 3. Risks
    for r in extracted_data.get("risks", []):
        p_name = r.get("project_name")
        p_id = project_map.get(p_name)
        
        cursor.execute("""
            INSERT INTO risks (
                risk_id, tenant_id, meeting_id, project_id, risk_description,
                risk_level, owner, created_at, source_sentence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "default",
            meeting_id,
            p_id,
            r.get("risk_description"),
            r.get("risk_level", "MEDIUM"),
            r.get("owner"),
            datetime.utcnow().isoformat(),
            r.get("source_sentence")
        ))
    
    # 4. Decisions
    for d in extracted_data.get("decisions", []):
        p_name = d.get("project_name")
        p_id = project_map.get(p_name)
        
        cursor.execute("""
            INSERT INTO decisions (
                decision_id, tenant_id, meeting_id, project_id, decision_description,
                created_at, source_sentence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "default",
            meeting_id,
            p_id,
            d.get("decision_content"),
            datetime.utcnow().isoformat(),
            d.get("source_sentence")
        ))
    
    conn.commit()
    conn.close()

    print(f"Successfully saved: {len(extracted_data.get('projects', []))} projects, "
          f"{len(extracted_data.get('tasks', []))} tasks, "
          f"{len(extracted_data.get('risks', []))} risks, "
          f"{len(extracted_data.get('decisions', []))} decisions")


# Settings functions
def get_setting(key: str) -> Optional[str]:
    """Get a setting value by key."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else None


def set_setting(key: str, value: str) -> None:
    """Set a setting value."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
    """, (key, value, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_all_settings() -> Dict[str, str]:
    """Get all settings as a dictionary."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


def delete_setting(key: str) -> None:
    """Delete a setting."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
    conn.commit()
    conn.close()


def get_overdue_tasks() -> List[Dict[str, Any]]:
    """Get tasks that are past their due date."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, p.project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.due_date < date('now')
          AND t.status != 'DONE'
        ORDER BY t.due_date ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_high_risks() -> List[Dict[str, Any]]:
    """Get all HIGH level risks."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.project_name
        FROM risks r
        LEFT JOIN projects p ON r.project_id = p.project_id
        WHERE r.risk_level = 'HIGH'
        ORDER BY r.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
