"""Audit log API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import List, Optional
from services import local_db
from auth.middleware import get_current_user, require_admin

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    log_id: str
    timestamp: str
    user_email: Optional[str]
    user_name: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


@router.get("/logs", response_model=AuditLogListResponse)
def list_logs(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user_email: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """List audit logs (Admin only)."""
    try:
        logs = local_db.list_audit_logs(
            limit=limit,
            offset=offset,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date
        )
        total = local_db.count_audit_logs(
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_stats(
    days: int = Query(default=30, le=365),
    current_user: dict = Depends(require_admin)
):
    """Get audit log statistics (Admin only)."""
    try:
        return local_db.get_audit_stats(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions")
def get_available_actions(current_user: dict = Depends(require_admin)):
    """Get list of available audit actions."""
    return {
        "actions": local_db.AUDIT_ACTIONS,
        "descriptions": {
            "LOGIN": "User login",
            "LOGOUT": "User logout",
            "UPLOAD_MEETING": "Meeting notes uploaded",
            "VIEW_PROJECT": "Project viewed",
            "VIEW_TASK": "Task viewed",
            "VIEW_RISK": "Risk viewed",
            "EXPORT_DATA": "Data exported",
            "UPDATE_SETTINGS": "Settings updated",
            "UPDATE_USER_ROLE": "User role updated",
            "DELETE_USER": "User deleted",
            "GENERATE_AGENDA": "Agenda generated",
            "VIEW_DIFF": "Diff view accessed",
        }
    }


def log_user_action(
    request: Request,
    action: str,
    current_user: dict,
    resource_type: str = None,
    resource_id: str = None,
    details: str = None
):
    """Helper function to log user actions."""
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        local_db.log_audit(
            action=action,
            user_email=current_user.get("email"),
            user_name=current_user.get("name"),
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Failed to log audit action: {e}")
