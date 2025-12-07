"""Migration runner for SQLite database."""
import os
import importlib
from datetime import datetime
from typing import List, Dict, Any
from services.local_db import _get_connection, get_schema_version, set_schema_version

MIGRATIONS_DIR = os.path.dirname(__file__)


def get_available_migrations() -> List[Dict[str, Any]]:
    """Get list of available migration files."""
    migrations = []
    for filename in sorted(os.listdir(MIGRATIONS_DIR)):
        if filename.startswith("v") and filename.endswith(".py"):
            # Extract version number from filename like v001_add_deleted_at.py
            version_str = filename.split("_")[0][1:]  # Remove 'v' prefix
            try:
                version = int(version_str)
                module_name = filename[:-3]  # Remove .py
                migrations.append({
                    "version": version,
                    "filename": filename,
                    "module_name": module_name
                })
            except ValueError:
                continue
    return migrations


def run_migrations(target_version: int = None):
    """
    Run pending migrations up to target_version.
    If target_version is None, run all pending migrations.
    """
    current_version = get_schema_version()
    available = get_available_migrations()
    
    if not available:
        print("No migrations found.")
        return
    
    max_version = max(m["version"] for m in available)
    
    if target_version is None:
        target_version = max_version
    
    if current_version >= target_version:
        print(f"Database is already at version {current_version}.")
        return
    
    pending = [m for m in available if current_version < m["version"] <= target_version]
    
    if not pending:
        print("No pending migrations.")
        return
    
    print(f"Running {len(pending)} migration(s) from v{current_version} to v{target_version}...")
    
    for migration in sorted(pending, key=lambda m: m["version"]):
        print(f"  Applying migration v{migration['version']}: {migration['filename']}")
        
        try:
            module = importlib.import_module(f"migrations.{migration['module_name']}")
            
            if hasattr(module, "upgrade"):
                module.upgrade()
                set_schema_version(migration["version"], getattr(module, "description", ""))
                print(f"    ✓ Migration v{migration['version']} applied successfully")
            else:
                print(f"    ✗ Migration v{migration['version']} has no upgrade() function")
                break
                
        except Exception as e:
            print(f"    ✗ Migration v{migration['version']} failed: {e}")
            raise
    
    print(f"Migrations complete. Current version: {get_schema_version()}")


def rollback(target_version: int):
    """Roll back migrations to target_version."""
    current_version = get_schema_version()
    available = get_available_migrations()
    
    if current_version <= target_version:
        print(f"Cannot rollback: current version {current_version} <= target {target_version}")
        return
    
    to_rollback = [m for m in available if target_version < m["version"] <= current_version]
    
    if not to_rollback:
        print("No migrations to rollback.")
        return
    
    print(f"Rolling back {len(to_rollback)} migration(s) from v{current_version} to v{target_version}...")
    
    for migration in sorted(to_rollback, key=lambda m: m["version"], reverse=True):
        print(f"  Rolling back migration v{migration['version']}: {migration['filename']}")
        
        try:
            module = importlib.import_module(f"migrations.{migration['module_name']}")
            
            if hasattr(module, "downgrade"):
                module.downgrade()
                new_version = migration["version"] - 1
                set_schema_version(new_version, f"Rolled back from v{migration['version']}")
                print(f"    ✓ Rollback of v{migration['version']} successful")
            else:
                print(f"    ✗ Migration v{migration['version']} has no downgrade() function")
                break
                
        except Exception as e:
            print(f"    ✗ Rollback of v{migration['version']} failed: {e}")
            raise
    
    print(f"Rollback complete. Current version: {get_schema_version()}")


def show_status():
    """Show current migration status."""
    current_version = get_schema_version()
    available = get_available_migrations()
    
    print(f"Current schema version: {current_version}")
    print(f"Available migrations:")
    
    for m in sorted(available, key=lambda x: x["version"]):
        status = "✓ applied" if m["version"] <= current_version else "○ pending"
        print(f"  v{m['version']:03d}: {m['filename']} [{status}]")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        show_status()
    elif sys.argv[1] == "upgrade":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else None
        run_migrations(target)
    elif sys.argv[1] == "rollback":
        if len(sys.argv) < 3:
            print("Usage: python runner.py rollback <target_version>")
        else:
            rollback(int(sys.argv[2]))
    elif sys.argv[1] == "status":
        show_status()
    else:
        print("Usage: python runner.py [upgrade [version] | rollback <version> | status]")

