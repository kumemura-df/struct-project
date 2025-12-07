"""
Migration v001: Add soft delete support

Adds deleted_at column to all entity tables for soft delete functionality.
"""
from services.local_db import _get_connection, _add_column_if_not_exists

description = "Add soft delete support (deleted_at columns)"


def upgrade():
    """Add deleted_at columns to all tables."""
    conn = _get_connection()
    
    tables = ["meetings", "projects", "tasks", "risks", "decisions"]
    
    for table in tables:
        _add_column_if_not_exists(conn, table, "deleted_at", "TEXT")
    
    # Also add updated_at to risks and decisions if missing
    _add_column_if_not_exists(conn, "risks", "updated_at", "TEXT")
    _add_column_if_not_exists(conn, "decisions", "updated_at", "TEXT")
    
    conn.close()


def downgrade():
    """
    Note: SQLite doesn't support DROP COLUMN easily.
    For downgrade, we would need to recreate tables.
    This is a no-op for safety.
    """
    print("Warning: SQLite doesn't support DROP COLUMN. Manual intervention required.")
    pass

