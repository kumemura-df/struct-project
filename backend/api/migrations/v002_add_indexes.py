"""
Migration v002: Add performance indexes

Adds indexes for commonly queried columns.
"""
from services.local_db import _get_connection

description = "Add performance indexes"


def upgrade():
    """Create indexes for better query performance."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    indexes = [
        ("idx_tasks_project", "tasks", "project_id"),
        ("idx_tasks_due_date", "tasks", "due_date"),
        ("idx_tasks_status", "tasks", "status"),
        ("idx_tasks_owner", "tasks", "owner"),
        ("idx_tasks_deleted", "tasks", "deleted_at"),
        ("idx_tasks_priority", "tasks", "priority"),
        
        ("idx_risks_project", "risks", "project_id"),
        ("idx_risks_level", "risks", "risk_level"),
        ("idx_risks_meeting", "risks", "meeting_id"),
        ("idx_risks_deleted", "risks", "deleted_at"),
        
        ("idx_projects_deleted", "projects", "deleted_at"),
        ("idx_projects_name", "projects", "project_name"),
        
        ("idx_decisions_project", "decisions", "project_id"),
        ("idx_decisions_meeting", "decisions", "meeting_id"),
        ("idx_decisions_deleted", "decisions", "deleted_at"),
        
        ("idx_meetings_date", "meetings", "meeting_date"),
        ("idx_meetings_status", "meetings", "status"),
        
        ("idx_audit_entity", "audit_log", "entity_type, entity_id"),
        ("idx_audit_created", "audit_log", "created_at"),
    ]
    
    for idx_name, table, columns in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({columns})")
        except Exception as e:
            print(f"Warning: Could not create index {idx_name}: {e}")
    
    conn.commit()
    conn.close()


def downgrade():
    """Drop the indexes."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    indexes = [
        "idx_tasks_project", "idx_tasks_due_date", "idx_tasks_status",
        "idx_tasks_owner", "idx_tasks_deleted", "idx_tasks_priority",
        "idx_risks_project", "idx_risks_level", "idx_risks_meeting", "idx_risks_deleted",
        "idx_projects_deleted", "idx_projects_name",
        "idx_decisions_project", "idx_decisions_meeting", "idx_decisions_deleted",
        "idx_meetings_date", "idx_meetings_status",
        "idx_audit_entity", "idx_audit_created",
    ]
    
    for idx_name in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
        except Exception as e:
            print(f"Warning: Could not drop index {idx_name}: {e}")
    
    conn.commit()
    conn.close()

