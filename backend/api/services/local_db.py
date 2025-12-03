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

    # User roles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            picture TEXT,
            role TEXT DEFAULT 'MEMBER',
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # Audit logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            user_email TEXT,
            user_name TEXT,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT
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


def get_project_health_score(project_id: str) -> Dict[str, Any]:
    """Calculate health score for a project (0-100).

    Score breakdown:
    - Task completion rate: 30 points (done / total)
    - No overdue tasks: 25 points (inverted ratio of overdue)
    - Risk level: 25 points (lower = better)
    - Recent activity: 20 points (meetings in last 30 days)
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # Get tasks for project
    cursor.execute("""
        SELECT status, due_date FROM tasks WHERE project_id = ?
    """, (project_id,))
    tasks = cursor.fetchall()

    # Get risks for project
    cursor.execute("""
        SELECT risk_level FROM risks WHERE project_id = ?
    """, (project_id,))
    risks = cursor.fetchall()

    # Get recent meetings (last 30 days)
    cursor.execute("""
        SELECT COUNT(*) as count FROM meetings m
        WHERE m.meeting_date >= date('now', '-30 days')
        AND EXISTS (
            SELECT 1 FROM tasks t WHERE t.meeting_id = m.meeting_id AND t.project_id = ?
            UNION
            SELECT 1 FROM risks r WHERE r.meeting_id = m.meeting_id AND r.project_id = ?
        )
    """, (project_id, project_id))
    recent_meetings = cursor.fetchone()["count"]

    conn.close()

    # Calculate scores
    total_tasks = len(tasks)
    done_tasks = sum(1 for t in tasks if t["status"] == "DONE")
    overdue_tasks = sum(1 for t in tasks if t["due_date"] and t["due_date"] < datetime.now().strftime("%Y-%m-%d") and t["status"] != "DONE")
    incomplete_tasks = total_tasks - done_tasks

    # Task completion score (30 points)
    task_score = (done_tasks / total_tasks * 30) if total_tasks > 0 else 30

    # Overdue score (25 points)
    if incomplete_tasks > 0:
        overdue_ratio = overdue_tasks / incomplete_tasks
        overdue_score = (1 - overdue_ratio) * 25
    else:
        overdue_score = 25

    # Risk score (25 points)
    total_risks = len(risks)
    high_risks = sum(1 for r in risks if r["risk_level"] == "HIGH")
    medium_risks = sum(1 for r in risks if r["risk_level"] == "MEDIUM")

    if total_risks > 0:
        # HIGH = 0 points, MEDIUM = 0.5 points, LOW = 1 point per risk
        risk_points = (total_risks - high_risks - medium_risks * 0.5) / total_risks
        risk_score = risk_points * 25
    else:
        risk_score = 25

    # Activity score (20 points)
    activity_score = min(recent_meetings * 5, 20)  # Max 4 meetings for full score

    total_score = round(task_score + overdue_score + risk_score + activity_score)

    # Determine health status
    if total_score >= 80:
        status = "HEALTHY"
    elif total_score >= 60:
        status = "AT_RISK"
    elif total_score >= 40:
        status = "WARNING"
    else:
        status = "CRITICAL"

    return {
        "project_id": project_id,
        "score": total_score,
        "status": status,
        "breakdown": {
            "task_completion": round(task_score, 1),
            "overdue": round(overdue_score, 1),
            "risk_level": round(risk_score, 1),
            "activity": round(activity_score, 1)
        },
        "details": {
            "total_tasks": total_tasks,
            "done_tasks": done_tasks,
            "overdue_tasks": overdue_tasks,
            "total_risks": total_risks,
            "high_risks": high_risks,
            "recent_meetings": recent_meetings
        }
    }


def get_all_project_health_scores() -> List[Dict[str, Any]]:
    """Get health scores for all projects."""
    projects = list_projects()
    return [
        {**get_project_health_score(p["project_id"]), "project_name": p["project_name"]}
        for p in projects
    ]


# User roles functions
VALID_ROLES = ["ADMIN", "PM", "MEMBER"]


def get_user_role(email: str) -> Optional[Dict[str, Any]]:
    """Get user role by email."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_roles WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_or_create_user(email: str, name: str = None, picture: str = None) -> Dict[str, Any]:
    """Get existing user or create new one with default MEMBER role."""
    import uuid

    existing = get_user_role(email)
    if existing:
        return existing

    conn = _get_connection()
    cursor = conn.cursor()

    user_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    # First user becomes ADMIN
    cursor.execute("SELECT COUNT(*) as count FROM user_roles")
    is_first_user = cursor.fetchone()["count"] == 0
    default_role = "ADMIN" if is_first_user else "MEMBER"

    cursor.execute("""
        INSERT INTO user_roles (user_id, email, name, picture, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, email, name, picture, default_role, now, now))

    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "picture": picture,
        "role": default_role,
        "created_at": now,
        "updated_at": now
    }


def update_user_role(email: str, role: str) -> Optional[Dict[str, Any]]:
    """Update user's role."""
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}. Must be one of {VALID_ROLES}")

    conn = _get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE user_roles SET role = ?, updated_at = ? WHERE email = ?
    """, (role, now, email))

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return None

    cursor.execute("SELECT * FROM user_roles WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def list_users() -> List[Dict[str, Any]]:
    """List all users."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_roles ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_user(email: str) -> bool:
    """Delete a user by email."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_roles WHERE email = ?", (email,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def count_admins() -> int:
    """Count number of admin users."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM user_roles WHERE role = 'ADMIN'")
    count = cursor.fetchone()["count"]
    conn.close()
    return count


# Audit log functions
AUDIT_ACTIONS = [
    "LOGIN",
    "LOGOUT",
    "UPLOAD_MEETING",
    "VIEW_PROJECT",
    "VIEW_TASK",
    "VIEW_RISK",
    "EXPORT_DATA",
    "UPDATE_SETTINGS",
    "UPDATE_USER_ROLE",
    "DELETE_USER",
    "GENERATE_AGENDA",
    "VIEW_DIFF",
]


def log_audit(
    action: str,
    user_email: str = None,
    user_name: str = None,
    resource_type: str = None,
    resource_id: str = None,
    details: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> str:
    """Record an audit log entry."""
    import uuid

    conn = _get_connection()
    cursor = conn.cursor()

    log_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO audit_logs (
            log_id, timestamp, user_email, user_name, action,
            resource_type, resource_id, details, ip_address, user_agent
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        log_id, timestamp, user_email, user_name, action,
        resource_type, resource_id, details, ip_address, user_agent
    ))

    conn.commit()
    conn.close()

    return log_id


def list_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_email: str = None,
    action: str = None,
    resource_type: str = None,
    start_date: str = None,
    end_date: str = None
) -> List[Dict[str, Any]]:
    """List audit logs with optional filtering."""
    conn = _get_connection()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if user_email:
        where_clauses.append("user_email = ?")
        params.append(user_email)

    if action:
        where_clauses.append("action = ?")
        params.append(action)

    if resource_type:
        where_clauses.append("resource_type = ?")
        params.append(resource_type)

    if start_date:
        where_clauses.append("timestamp >= ?")
        params.append(start_date)

    if end_date:
        where_clauses.append("timestamp <= ?")
        params.append(end_date)

    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
        SELECT * FROM audit_logs
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def count_audit_logs(
    user_email: str = None,
    action: str = None,
    resource_type: str = None,
    start_date: str = None,
    end_date: str = None
) -> int:
    """Count audit logs with optional filtering."""
    conn = _get_connection()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if user_email:
        where_clauses.append("user_email = ?")
        params.append(user_email)

    if action:
        where_clauses.append("action = ?")
        params.append(action)

    if resource_type:
        where_clauses.append("resource_type = ?")
        params.append(resource_type)

    if start_date:
        where_clauses.append("timestamp >= ?")
        params.append(start_date)

    if end_date:
        where_clauses.append("timestamp <= ?")
        params.append(end_date)

    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"SELECT COUNT(*) as count FROM audit_logs {where_clause}"
    cursor.execute(query, params)
    count = cursor.fetchone()["count"]
    conn.close()

    return count


def get_audit_stats(days: int = 30) -> Dict[str, Any]:
    """Get audit log statistics for the last N days."""
    conn = _get_connection()
    cursor = conn.cursor()

    start_date = (datetime.now() - __import__("datetime").timedelta(days=days)).isoformat()

    # Actions by type
    cursor.execute("""
        SELECT action, COUNT(*) as count
        FROM audit_logs
        WHERE timestamp >= ?
        GROUP BY action
        ORDER BY count DESC
    """, (start_date,))
    by_action = {row["action"]: row["count"] for row in cursor.fetchall()}

    # Actions by user
    cursor.execute("""
        SELECT user_email, COUNT(*) as count
        FROM audit_logs
        WHERE timestamp >= ? AND user_email IS NOT NULL
        GROUP BY user_email
        ORDER BY count DESC
        LIMIT 10
    """, (start_date,))
    by_user = [{"email": row["user_email"], "count": row["count"]} for row in cursor.fetchall()]

    # Daily activity
    cursor.execute("""
        SELECT date(timestamp) as date, COUNT(*) as count
        FROM audit_logs
        WHERE timestamp >= ?
        GROUP BY date(timestamp)
        ORDER BY date DESC
    """, (start_date,))
    daily = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]

    # Total count
    cursor.execute("""
        SELECT COUNT(*) as total FROM audit_logs WHERE timestamp >= ?
    """, (start_date,))
    total = cursor.fetchone()["total"]

    conn.close()

    return {
        "period_days": days,
        "total": total,
        "by_action": by_action,
        "by_user": by_user,
        "daily": daily
    }
