"""Local SQLite database for development mode."""
import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from queue import Queue
from threading import Lock
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "local.db")

# Connection pool settings
POOL_SIZE = 5
_connection_pool: Queue = Queue(maxsize=POOL_SIZE)
_pool_lock = Lock()
_pool_initialized = False

def _init_pool():
    """Initialize the connection pool."""
    global _pool_initialized
    with _pool_lock:
        if _pool_initialized:
            return
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        for _ in range(POOL_SIZE):
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _connection_pool.put(conn)
        _pool_initialized = True


@contextmanager
def get_connection():
    """Get a connection from the pool (context manager)."""
    _init_pool()
    conn = _connection_pool.get()
    try:
        _create_tables(conn)
        yield conn
    finally:
        _connection_pool.put(conn)


def _get_connection():
    """Get SQLite connection and ensure tables exist (legacy support)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
            error_message TEXT,
            deleted_at TEXT
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
            updated_at TEXT,
            deleted_at TEXT
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
            source_sentence TEXT,
            deleted_at TEXT
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
            source_sentence TEXT,
            deleted_at TEXT,
            updated_at TEXT
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
            source_sentence TEXT,
            deleted_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Audit log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            user_id TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Schema migrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT
        )
    """)
    
    # Task history table (for diff detection)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            history_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            meeting_id TEXT,
            field_changed TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            changed_at TEXT NOT NULL,
            changed_by TEXT
        )
    """)
    
    # Risk history table (for diff detection)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_history (
            history_id TEXT PRIMARY KEY,
            risk_id TEXT NOT NULL,
            meeting_id TEXT,
            old_level TEXT,
            new_level TEXT,
            changed_at TEXT NOT NULL,
            changed_by TEXT
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_owner ON tasks(owner)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_deleted ON tasks(deleted_at)")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risks_project ON risks(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risks_level ON risks(risk_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risks_deleted ON risks(deleted_at)")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_deleted ON projects(deleted_at)")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_deleted ON decisions(deleted_at)")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)")
    
    # Indexes for history tables
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_history_task ON task_history(task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_history_meeting ON task_history(meeting_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_history_changed ON task_history(changed_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_history_risk ON risk_history(risk_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_history_meeting ON risk_history(meeting_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_history_changed ON risk_history(changed_at)")
    
    conn.commit()


def _add_column_if_not_exists(conn: sqlite3.Connection, table: str, column: str, column_type: str):
    """Add a column to a table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        conn.commit()


def _ensure_columns(conn: sqlite3.Connection):
    """Ensure all required columns exist (for existing databases)."""
    # Add deleted_at columns
    _add_column_if_not_exists(conn, "meetings", "deleted_at", "TEXT")
    _add_column_if_not_exists(conn, "projects", "deleted_at", "TEXT")
    _add_column_if_not_exists(conn, "tasks", "deleted_at", "TEXT")
    _add_column_if_not_exists(conn, "risks", "deleted_at", "TEXT")
    _add_column_if_not_exists(conn, "risks", "updated_at", "TEXT")
    _add_column_if_not_exists(conn, "decisions", "deleted_at", "TEXT")
    _add_column_if_not_exists(conn, "decisions", "updated_at", "TEXT")

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


# ===== AUDIT LOG =====

def _log_audit(
    conn: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    action: str,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None,
    user_id: Optional[str] = None
):
    """Log an audit entry."""
    import uuid
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log (log_id, entity_type, entity_id, action, old_value, new_value, user_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        entity_type,
        entity_id,
        action,
        json.dumps(old_value) if old_value else None,
        json.dumps(new_value) if new_value else None,
        user_id,
        datetime.utcnow().isoformat()
    ))


def get_audit_log(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get audit log entries."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    where_clauses = []
    params = []
    
    if entity_type:
        where_clauses.append("entity_type = ?")
        params.append(entity_type)
    
    if entity_id:
        where_clauses.append("entity_id = ?")
        params.append(entity_id)
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    query = f"""
        SELECT * FROM audit_log 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        item = dict(row)
        if item.get("old_value"):
            item["old_value"] = json.loads(item["old_value"])
        if item.get("new_value"):
            item["new_value"] = json.loads(item["new_value"])
        result.append(item)
    
    return result


# ===== SINGLE RECORD GET =====

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get a single task by ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_id = ? AND deleted_at IS NULL", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_risk(risk_id: str) -> Optional[Dict[str, Any]]:
    """Get a single risk by ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM risks WHERE risk_id = ? AND deleted_at IS NULL", (risk_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Get a single project by ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE project_id = ? AND deleted_at IS NULL", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_decision(decision_id: str) -> Optional[Dict[str, Any]]:
    """Get a single decision by ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM decisions WHERE decision_id = ? AND deleted_at IS NULL", (decision_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ===== UPDATE FUNCTIONS =====

def update_task(task_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a task."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    # Get current values for audit log
    cursor.execute("SELECT * FROM tasks WHERE task_id = ? AND deleted_at IS NULL", (task_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return None
    
    old_value = dict(old_row)
    
    # Build update query
    update_fields = []
    params = []
    
    allowed_fields = ["task_title", "task_description", "owner", "due_date", "status", "priority"]
    for field in allowed_fields:
        if field in updates and updates[field] is not None:
            update_fields.append(f"{field} = ?")
            params.append(str(updates[field]) if updates[field] else None)
    
    if not update_fields:
        conn.close()
        return old_value
    
    update_fields.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(task_id)
    
    query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?"
    cursor.execute(query, params)
    
    # Log audit
    _log_audit(conn, "task", task_id, "UPDATE", old_value, updates, user_id)
    
    conn.commit()
    
    # Return updated record
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_risk(risk_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a risk."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    # Get current values for audit log
    cursor.execute("SELECT * FROM risks WHERE risk_id = ? AND deleted_at IS NULL", (risk_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return None
    
    old_value = dict(old_row)
    
    # Build update query
    update_fields = []
    params = []
    
    allowed_fields = ["risk_description", "risk_level", "owner"]
    for field in allowed_fields:
        if field in updates and updates[field] is not None:
            update_fields.append(f"{field} = ?")
            params.append(str(updates[field]) if updates[field] else None)
    
    if not update_fields:
        conn.close()
        return old_value
    
    update_fields.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(risk_id)
    
    query = f"UPDATE risks SET {', '.join(update_fields)} WHERE risk_id = ?"
    cursor.execute(query, params)
    
    # Log audit
    _log_audit(conn, "risk", risk_id, "UPDATE", old_value, updates, user_id)
    
    conn.commit()
    
    # Return updated record
    cursor.execute("SELECT * FROM risks WHERE risk_id = ?", (risk_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_project(project_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a project."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    # Get current values for audit log
    cursor.execute("SELECT * FROM projects WHERE project_id = ? AND deleted_at IS NULL", (project_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return None
    
    old_value = dict(old_row)
    
    # Build update query
    update_fields = []
    params = []
    
    allowed_fields = ["project_name"]
    for field in allowed_fields:
        if field in updates and updates[field] is not None:
            update_fields.append(f"{field} = ?")
            params.append(str(updates[field]) if updates[field] else None)
    
    if not update_fields:
        conn.close()
        return old_value
    
    update_fields.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(project_id)
    
    query = f"UPDATE projects SET {', '.join(update_fields)} WHERE project_id = ?"
    cursor.execute(query, params)
    
    # Log audit
    _log_audit(conn, "project", project_id, "UPDATE", old_value, updates, user_id)
    
    conn.commit()
    
    # Return updated record
    cursor.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_decision(decision_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a decision."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    # Get current values for audit log
    cursor.execute("SELECT * FROM decisions WHERE decision_id = ? AND deleted_at IS NULL", (decision_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return None
    
    old_value = dict(old_row)
    
    # Build update query
    update_fields = []
    params = []
    
    allowed_fields = ["decision_description", "decided_by"]
    for field in allowed_fields:
        if field in updates and updates[field] is not None:
            update_fields.append(f"{field} = ?")
            params.append(str(updates[field]) if updates[field] else None)
    
    if not update_fields:
        conn.close()
        return old_value
    
    update_fields.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(decision_id)
    
    query = f"UPDATE decisions SET {', '.join(update_fields)} WHERE decision_id = ?"
    cursor.execute(query, params)
    
    # Log audit
    _log_audit(conn, "decision", decision_id, "UPDATE", old_value, updates, user_id)
    
    conn.commit()
    
    # Return updated record
    cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ===== DELETE FUNCTIONS (Soft Delete) =====

def delete_task(task_id: str, user_id: Optional[str] = None) -> bool:
    """Soft delete a task."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    # Get current values for audit log
    cursor.execute("SELECT * FROM tasks WHERE task_id = ? AND deleted_at IS NULL", (task_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return False
    
    old_value = dict(old_row)
    
    # Soft delete
    cursor.execute(
        "UPDATE tasks SET deleted_at = ? WHERE task_id = ?",
        (datetime.utcnow().isoformat(), task_id)
    )
    
    # Log audit
    _log_audit(conn, "task", task_id, "DELETE", old_value, None, user_id)
    
    conn.commit()
    conn.close()
    return True


def delete_risk(risk_id: str, user_id: Optional[str] = None) -> bool:
    """Soft delete a risk."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    # Get current values for audit log
    cursor.execute("SELECT * FROM risks WHERE risk_id = ? AND deleted_at IS NULL", (risk_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return False
    
    old_value = dict(old_row)
    
    # Soft delete
    cursor.execute(
        "UPDATE risks SET deleted_at = ? WHERE risk_id = ?",
        (datetime.utcnow().isoformat(), risk_id)
    )
    
    # Log audit
    _log_audit(conn, "risk", risk_id, "DELETE", old_value, None, user_id)
    
    conn.commit()
    conn.close()
    return True


def delete_project(project_id: str, user_id: Optional[str] = None) -> bool:
    """Soft delete a project."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    # Get current values for audit log
    cursor.execute("SELECT * FROM projects WHERE project_id = ? AND deleted_at IS NULL", (project_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return False
    
    old_value = dict(old_row)
    
    # Soft delete
    cursor.execute(
        "UPDATE projects SET deleted_at = ? WHERE project_id = ?",
        (datetime.utcnow().isoformat(), project_id)
    )
    
    # Log audit
    _log_audit(conn, "project", project_id, "DELETE", old_value, None, user_id)
    
    conn.commit()
    conn.close()
    return True


def delete_decision(decision_id: str, user_id: Optional[str] = None) -> bool:
    """Soft delete a decision."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    # Get current values for audit log
    cursor.execute("SELECT * FROM decisions WHERE decision_id = ? AND deleted_at IS NULL", (decision_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return False
    
    old_value = dict(old_row)
    
    # Soft delete
    cursor.execute(
        "UPDATE decisions SET deleted_at = ? WHERE decision_id = ?",
        (datetime.utcnow().isoformat(), decision_id)
    )
    
    # Log audit
    _log_audit(conn, "decision", decision_id, "DELETE", old_value, None, user_id)
    
    conn.commit()
    conn.close()
    return True


# ===== RESTORE FUNCTIONS =====

def restore_task(task_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Restore a soft-deleted task."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE task_id = ? AND deleted_at IS NOT NULL", (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    cursor.execute(
        "UPDATE tasks SET deleted_at = NULL, updated_at = ? WHERE task_id = ?",
        (datetime.utcnow().isoformat(), task_id)
    )
    
    _log_audit(conn, "task", task_id, "RESTORE", None, None, user_id)
    
    conn.commit()
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ===== ADVANCED LIST WITH PAGINATION, SEARCH, SORT =====

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
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    where_clauses = ["deleted_at IS NULL"]
    params = []
    
    if project_id:
        where_clauses.append("project_id = ?")
        params.append(project_id)
    
    if status:
        placeholders = ",".join("?" * len(status))
        where_clauses.append(f"status IN ({placeholders})")
        params.extend(status)
    
    if priority:
        placeholders = ",".join("?" * len(priority))
        where_clauses.append(f"priority IN ({placeholders})")
        params.extend(priority)
    
    if owner:
        where_clauses.append("owner LIKE ?")
        params.append(f"%{owner}%")
    
    if due_date_from:
        where_clauses.append("due_date >= ?")
        params.append(due_date_from)
    
    if due_date_to:
        where_clauses.append("due_date <= ?")
        params.append(due_date_to)
    
    if search:
        where_clauses.append("(task_title LIKE ? OR task_description LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}"
    
    # Validate sort_by
    allowed_sort = ["due_date", "created_at", "updated_at", "priority", "status", "task_title"]
    if sort_by not in allowed_sort:
        sort_by = "due_date"
    
    sort_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM tasks {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]
    
    # Get items
    query = f"""
        SELECT * FROM tasks 
        {where_clause}
        ORDER BY {sort_by} {sort_direction}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "items": [dict(row) for row in rows],
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
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    where_clauses = ["deleted_at IS NULL"]
    params = []
    
    if project_id:
        where_clauses.append("project_id = ?")
        params.append(project_id)
    
    if meeting_id:
        where_clauses.append("meeting_id = ?")
        params.append(meeting_id)
    
    if risk_level:
        placeholders = ",".join("?" * len(risk_level))
        where_clauses.append(f"risk_level IN ({placeholders})")
        params.extend(risk_level)
    
    if owner:
        where_clauses.append("owner LIKE ?")
        params.append(f"%{owner}%")
    
    if search:
        where_clauses.append("risk_description LIKE ?")
        params.append(f"%{search}%")
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}"
    
    # Validate sort_by
    allowed_sort = ["created_at", "updated_at", "risk_level"]
    if sort_by not in allowed_sort:
        sort_by = "created_at"
    
    sort_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM risks {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]
    
    # Get items
    query = f"""
        SELECT * FROM risks 
        {where_clause}
        ORDER BY {sort_by} {sort_direction}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "items": [dict(row) for row in rows],
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
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    where_clauses = ["deleted_at IS NULL"]
    params = []
    
    if search:
        where_clauses.append("project_name LIKE ?")
        params.append(f"%{search}%")
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}"
    
    # Validate sort_by
    allowed_sort = ["created_at", "updated_at", "project_name"]
    if sort_by not in allowed_sort:
        sort_by = "updated_at"
    
    sort_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM projects {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]
    
    # Get items
    query = f"""
        SELECT * FROM projects 
        {where_clause}
        ORDER BY {sort_by} {sort_direction}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "items": [dict(row) for row in rows],
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
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    where_clauses = ["deleted_at IS NULL"]
    params = []
    
    if project_id:
        where_clauses.append("project_id = ?")
        params.append(project_id)
    
    if meeting_id:
        where_clauses.append("meeting_id = ?")
        params.append(meeting_id)
    
    if search:
        where_clauses.append("decision_description LIKE ?")
        params.append(f"%{search}%")
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}"
    
    # Validate sort_by
    allowed_sort = ["created_at", "updated_at"]
    if sort_by not in allowed_sort:
        sort_by = "created_at"
    
    sort_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM decisions {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]
    
    # Get items
    query = f"""
        SELECT * FROM decisions 
        {where_clause}
        ORDER BY {sort_by} {sort_direction}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


# ===== SEARCH FUNCTIONS =====

def search_all(
    query: str,
    limit: int = 20
) -> Dict[str, List[Dict[str, Any]]]:
    """Search across all entities."""
    conn = _get_connection()
    _ensure_columns(conn)
    cursor = conn.cursor()
    
    search_term = f"%{query}%"
    
    # Search tasks
    cursor.execute("""
        SELECT 'task' as entity_type, task_id as id, task_title as title, task_description as description
        FROM tasks WHERE deleted_at IS NULL AND (task_title LIKE ? OR task_description LIKE ?)
        LIMIT ?
    """, (search_term, search_term, limit))
    tasks = [dict(row) for row in cursor.fetchall()]
    
    # Search risks
    cursor.execute("""
        SELECT 'risk' as entity_type, risk_id as id, risk_description as title, risk_description as description
        FROM risks WHERE deleted_at IS NULL AND risk_description LIKE ?
        LIMIT ?
    """, (search_term, limit))
    risks = [dict(row) for row in cursor.fetchall()]
    
    # Search projects
    cursor.execute("""
        SELECT 'project' as entity_type, project_id as id, project_name as title, project_name as description
        FROM projects WHERE deleted_at IS NULL AND project_name LIKE ?
        LIMIT ?
    """, (search_term, limit))
    projects = [dict(row) for row in cursor.fetchall()]
    
    # Search decisions
    cursor.execute("""
        SELECT 'decision' as entity_type, decision_id as id, decision_description as title, decision_description as description
        FROM decisions WHERE deleted_at IS NULL AND decision_description LIKE ?
        LIMIT ?
    """, (search_term, limit))
    decisions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "tasks": tasks,
        "risks": risks,
        "projects": projects,
        "decisions": decisions
    }


# ===== MIGRATION HELPERS =====

def get_schema_version() -> int:
    """Get current schema version."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(version) as version FROM schema_migrations")
        row = cursor.fetchone()
        conn.close()
        return row["version"] if row and row["version"] else 0
    except:
        conn.close()
        return 0


def set_schema_version(version: int, description: str = ""):
    """Set schema version."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO schema_migrations (version, applied_at, description)
        VALUES (?, ?, ?)
    """, (version, datetime.utcnow().isoformat(), description))
    conn.commit()
    conn.close()


# ===== MEETINGS LIST =====

def list_meetings_paginated(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """List meetings with pagination, filtering, search, and sorting."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    where_clauses = ["deleted_at IS NULL"]
    params = []
    
    if status:
        where_clauses.append("status = ?")
        params.append(status)
    
    if search:
        where_clauses.append("(title LIKE ? OR meeting_id LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    where_clause = f"WHERE {' AND '.join(where_clauses)}"
    
    # Validate sort_by
    allowed_sort = ["created_at", "meeting_date", "title", "status"]
    if sort_by not in allowed_sort:
        sort_by = "created_at"
    
    sort_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM meetings {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]
    
    # Get items with extraction counts
    query = f"""
        SELECT 
            m.*,
            (SELECT COUNT(*) FROM tasks t WHERE t.meeting_id = m.meeting_id AND t.deleted_at IS NULL) as task_count,
            (SELECT COUNT(*) FROM risks r WHERE r.meeting_id = m.meeting_id AND r.deleted_at IS NULL) as risk_count,
            (SELECT COUNT(*) FROM decisions d WHERE d.meeting_id = m.meeting_id AND d.deleted_at IS NULL) as decision_count
        FROM meetings m
        {where_clause}
        ORDER BY {sort_by} {sort_direction}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


def get_meeting(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Get a single meeting by ID with extraction counts."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            m.*,
            (SELECT COUNT(*) FROM tasks t WHERE t.meeting_id = m.meeting_id AND t.deleted_at IS NULL) as task_count,
            (SELECT COUNT(*) FROM risks r WHERE r.meeting_id = m.meeting_id AND r.deleted_at IS NULL) as risk_count,
            (SELECT COUNT(*) FROM decisions d WHERE d.meeting_id = m.meeting_id AND d.deleted_at IS NULL) as decision_count
        FROM meetings m
        WHERE m.meeting_id = ? AND m.deleted_at IS NULL
    """, (meeting_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ===== PROJECT STATS =====

def get_project_stats(project_id: str) -> Optional[Dict[str, Any]]:
    """Get statistics for a specific project."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Check if project exists
    cursor.execute("SELECT * FROM projects WHERE project_id = ? AND deleted_at IS NULL", (project_id,))
    project = cursor.fetchone()
    if not project:
        conn.close()
        return None
    
    # Total tasks
    cursor.execute("""
        SELECT COUNT(*) as total FROM tasks 
        WHERE project_id = ? AND deleted_at IS NULL
    """, (project_id,))
    total_tasks = cursor.fetchone()["total"]
    
    # Incomplete tasks (not DONE)
    cursor.execute("""
        SELECT COUNT(*) as count FROM tasks 
        WHERE project_id = ? AND deleted_at IS NULL AND status != 'DONE'
    """, (project_id,))
    incomplete_tasks = cursor.fetchone()["count"]
    
    # Overdue tasks
    cursor.execute("""
        SELECT COUNT(*) as count FROM tasks 
        WHERE project_id = ? AND deleted_at IS NULL 
        AND status != 'DONE' 
        AND due_date IS NOT NULL 
        AND due_date < date('now')
    """, (project_id,))
    overdue_tasks = cursor.fetchone()["count"]
    
    # Risk count by level
    cursor.execute("""
        SELECT risk_level, COUNT(*) as count FROM risks 
        WHERE project_id = ? AND deleted_at IS NULL
        GROUP BY risk_level
    """, (project_id,))
    risks_by_level = {row["risk_level"]: row["count"] for row in cursor.fetchall()}
    
    # Total risks
    total_risks = sum(risks_by_level.values())
    
    # Decision count
    cursor.execute("""
        SELECT COUNT(*) as count FROM decisions 
        WHERE project_id = ? AND deleted_at IS NULL
    """, (project_id,))
    total_decisions = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "project_id": project_id,
        "total_tasks": total_tasks,
        "incomplete_tasks": incomplete_tasks,
        "overdue_tasks": overdue_tasks,
        "total_risks": total_risks,
        "risks_by_level": risks_by_level,
        "total_decisions": total_decisions,
    }


# ===== WEEKLY REPORT FUNCTIONS =====

def get_weekly_summary(start_date: str, end_date: str) -> Dict[str, Any]:
    """Get weekly summary statistics."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Task statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status != 'DONE' THEN 1 ELSE 0 END) as incomplete_tasks,
            SUM(CASE WHEN status != 'DONE' AND due_date IS NOT NULL AND due_date < date('now') THEN 1 ELSE 0 END) as overdue_tasks
        FROM tasks WHERE deleted_at IS NULL
    """)
    task_row = cursor.fetchone()
    
    # High risk count
    cursor.execute("""
        SELECT COUNT(*) as high_risks FROM risks 
        WHERE deleted_at IS NULL AND risk_level = 'HIGH'
    """)
    risk_row = cursor.fetchone()
    
    # Decisions this week
    cursor.execute("""
        SELECT COUNT(*) as weekly_decisions FROM decisions 
        WHERE deleted_at IS NULL AND date(created_at) BETWEEN ? AND ?
    """, (start_date, end_date))
    decision_row = cursor.fetchone()
    
    conn.close()
    
    return {
        "total_tasks": task_row["total_tasks"] or 0,
        "incomplete_tasks": task_row["incomplete_tasks"] or 0,
        "overdue_tasks": task_row["overdue_tasks"] or 0,
        "high_risks": risk_row["high_risks"] or 0,
        "weekly_decisions": decision_row["weekly_decisions"] or 0,
    }


def get_overdue_tasks(limit: int = 10, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get overdue tasks sorted by days overdue."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    where_clause = "WHERE t.deleted_at IS NULL AND t.status != 'DONE' AND t.due_date IS NOT NULL AND t.due_date < date('now')"
    params = []
    
    if project_id:
        where_clause += " AND t.project_id = ?"
        params.append(project_id)
    
    query = f"""
        SELECT 
            t.*,
            p.project_name,
            julianday('now') - julianday(t.due_date) as days_overdue
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        {where_clause}
        ORDER BY days_overdue DESC
        LIMIT ?
    """
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_high_risks(limit: int = 10, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get high and medium priority risks."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    where_clause = "WHERE r.deleted_at IS NULL AND r.risk_level IN ('HIGH', 'MEDIUM')"
    params = []
    
    if project_id:
        where_clause += " AND r.project_id = ?"
        params.append(project_id)
    
    query = f"""
        SELECT 
            r.*,
            p.project_name
        FROM risks r
        LEFT JOIN projects p ON r.project_id = p.project_id
        {where_clause}
        ORDER BY 
            CASE r.risk_level WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
            r.created_at DESC
        LIMIT ?
    """
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_recent_decisions(start_date: str, end_date: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent decisions within date range."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            d.*,
            p.project_name
        FROM decisions d
        LEFT JOIN projects p ON d.project_id = p.project_id
        WHERE d.deleted_at IS NULL AND date(d.created_at) BETWEEN ? AND ?
        ORDER BY d.created_at DESC
        LIMIT ?
    """, (start_date, end_date, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# ===== HISTORY TRACKING FOR DIFF DETECTION =====

def record_task_history(
    task_id: str,
    field_changed: str,
    old_value: Optional[str],
    new_value: Optional[str],
    meeting_id: Optional[str] = None,
    changed_by: Optional[str] = None
):
    """Record a task change in history."""
    import uuid
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO task_history (history_id, task_id, meeting_id, field_changed, old_value, new_value, changed_at, changed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        task_id,
        meeting_id,
        field_changed,
        old_value,
        new_value,
        datetime.utcnow().isoformat(),
        changed_by
    ))
    
    conn.commit()
    conn.close()


def record_risk_history(
    risk_id: str,
    old_level: Optional[str],
    new_level: Optional[str],
    meeting_id: Optional[str] = None,
    changed_by: Optional[str] = None
):
    """Record a risk level change in history."""
    import uuid
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO risk_history (history_id, risk_id, meeting_id, old_level, new_level, changed_at, changed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        risk_id,
        meeting_id,
        old_level,
        new_level,
        datetime.utcnow().isoformat(),
        changed_by
    ))
    
    conn.commit()
    conn.close()


def get_task_history(task_id: str) -> List[Dict[str, Any]]:
    """Get history of changes for a task."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM task_history
        WHERE task_id = ?
        ORDER BY changed_at DESC
    """, (task_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_risk_history(risk_id: str) -> List[Dict[str, Any]]:
    """Get history of level changes for a risk."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM risk_history
        WHERE risk_id = ?
        ORDER BY changed_at DESC
    """, (risk_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# ===== DIFF DETECTION FUNCTIONS =====

def get_new_tasks_since_meeting(meeting_id: str) -> List[Dict[str, Any]]:
    """Get tasks created after the given meeting."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Get meeting date
    cursor.execute("SELECT created_at FROM meetings WHERE meeting_id = ?", (meeting_id,))
    meeting_row = cursor.fetchone()
    if not meeting_row:
        conn.close()
        return []
    
    meeting_date = meeting_row["created_at"]
    
    # Get tasks created after this meeting
    cursor.execute("""
        SELECT t.*, p.project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.deleted_at IS NULL AND t.created_at > ?
        ORDER BY t.created_at DESC
    """, (meeting_date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_status_changes_since_meeting(meeting_id: str) -> List[Dict[str, Any]]:
    """Get task status changes since the given meeting."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Get meeting date
    cursor.execute("SELECT created_at FROM meetings WHERE meeting_id = ?", (meeting_id,))
    meeting_row = cursor.fetchone()
    if not meeting_row:
        conn.close()
        return []
    
    meeting_date = meeting_row["created_at"]
    
    # Get status changes from task_history
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
    """, (meeting_date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_escalated_risks_since_meeting(meeting_id: str) -> List[Dict[str, Any]]:
    """Get risks that escalated (LOW->MEDIUM, MEDIUM->HIGH, etc.) since the given meeting."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Get meeting date
    cursor.execute("SELECT created_at FROM meetings WHERE meeting_id = ?", (meeting_id,))
    meeting_row = cursor.fetchone()
    if not meeting_row:
        conn.close()
        return []
    
    meeting_date = meeting_row["created_at"]
    
    # Get risk level changes (escalations only)
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
    """, (meeting_date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_task_lifecycle(task_id: str) -> Dict[str, Any]:
    """Get complete lifecycle of a task from creation to current state."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Get task details
    cursor.execute("""
        SELECT t.*, p.project_name, m.title as meeting_title, m.meeting_date
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        LEFT JOIN meetings m ON t.meeting_id = m.meeting_id
        WHERE t.task_id = ?
    """, (task_id,))
    
    task_row = cursor.fetchone()
    if not task_row:
        conn.close()
        return {}
    
    task = dict(task_row)
    
    # Get all history
    cursor.execute("""
        SELECT * FROM task_history
        WHERE task_id = ?
        ORDER BY changed_at ASC
    """, (task_id,))
    
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Build timeline
    timeline = [
        {
            "event": "created",
            "timestamp": task["created_at"],
            "details": f"タスク「{task['task_title']}」が作成されました",
            "meeting_title": task.get("meeting_title")
        }
    ]
    
    for h in history:
        if h["field_changed"] == "status":
            timeline.append({
                "event": "status_change",
                "timestamp": h["changed_at"],
                "details": f"ステータスが {h['old_value']} から {h['new_value']} に変更",
                "old_value": h["old_value"],
                "new_value": h["new_value"]
            })
        else:
            timeline.append({
                "event": "update",
                "timestamp": h["changed_at"],
                "details": f"{h['field_changed']} が変更されました",
                "field": h["field_changed"],
                "old_value": h["old_value"],
                "new_value": h["new_value"]
            })
    
    return {
        "task": task,
        "timeline": timeline,
        "history_count": len(history)
    }


def get_meeting_diff_summary(meeting_id: str) -> Dict[str, Any]:
    """Get a summary of all changes since a meeting."""
    new_tasks = get_new_tasks_since_meeting(meeting_id)
    status_changes = get_status_changes_since_meeting(meeting_id)
    escalated_risks = get_escalated_risks_since_meeting(meeting_id)
    
    return {
        "meeting_id": meeting_id,
        "new_tasks": {
            "count": len(new_tasks),
            "items": new_tasks[:10]  # Limit to 10
        },
        "status_changes": {
            "count": len(status_changes),
            "items": status_changes[:10]
        },
        "escalated_risks": {
            "count": len(escalated_risks),
            "items": escalated_risks[:10]
        }
    }
