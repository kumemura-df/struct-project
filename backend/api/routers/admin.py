"""Admin management endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    role: str = 'member'  # 'admin', 'pm', 'member'


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


def require_admin(current_user: dict):
    """Check if user is admin."""
    user = bigquery.get_user_by_email(current_user.get("email", ""))
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ===== USER MANAGEMENT =====

@router.get("/users")
def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List all users (admin only)."""
    require_admin(current_user)
    return bigquery.list_users(limit=limit, offset=offset)


@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific user."""
    require_admin(current_user)
    user = bigquery.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users")
def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new user (admin only)."""
    require_admin(current_user)
    
    # Check if user already exists
    existing = bigquery.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    if user_data.role not in ['admin', 'pm', 'member']:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = bigquery.create_user(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role
    )
    
    # Log the action
    bigquery.create_audit_log(
        entity_type="user",
        entity_id=user["user_id"],
        action="create",
        user_id=current_user.get("email"),
        new_value={"email": user_data.email, "role": user_data.role}
    )
    
    return user


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    updates: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a user (admin only)."""
    require_admin(current_user)
    
    existing = bigquery.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    if updates.name is not None:
        update_data["name"] = updates.name
    if updates.role is not None:
        if updates.role not in ['admin', 'pm', 'member']:
            raise HTTPException(status_code=400, detail="Invalid role")
        update_data["role"] = updates.role
    if updates.is_active is not None:
        update_data["is_active"] = 1 if updates.is_active else 0
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    user = bigquery.update_user(user_id, update_data)
    
    # Log the action
    bigquery.create_audit_log(
        entity_type="user",
        entity_id=user_id,
        action="update",
        user_id=current_user.get("email"),
        old_value={"role": existing.get("role")},
        new_value=update_data
    )
    
    return user


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a user (admin only)."""
    require_admin(current_user)
    
    existing = bigquery.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deactivation
    if existing.get("email") == current_user.get("email"):
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    bigquery.update_user(user_id, {"is_active": 0})
    
    # Log the action
    bigquery.create_audit_log(
        entity_type="user",
        entity_id=user_id,
        action="deactivate",
        user_id=current_user.get("email")
    )
    
    return {"success": True, "message": "User deactivated"}


# ===== AUDIT LOGS =====

@router.get("/audit-logs")
def get_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get audit logs (admin only)."""
    require_admin(current_user)
    
    return bigquery.get_audit_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        limit=limit,
        offset=offset
    )


# ===== ROLE INFO =====

@router.get("/roles")
def get_roles(
    current_user: dict = Depends(get_current_user)
):
    """Get available roles and their permissions."""
    return {
        "roles": [
            {
                "id": "admin",
                "name": "管理者",
                "description": "全機能へのアクセス権限",
                "permissions": ["*"]
            },
            {
                "id": "pm",
                "name": "プロジェクトマネージャー",
                "description": "プロジェクト管理、レポート作成",
                "permissions": ["projects.*", "tasks.*", "risks.*", "reports.*", "meetings.*"]
            },
            {
                "id": "member",
                "name": "メンバー",
                "description": "閲覧と基本的な編集",
                "permissions": ["projects.read", "tasks.read", "tasks.update", "risks.read", "meetings.read"]
            }
        ]
    }


# ===== CURRENT USER ROLE =====

@router.get("/me/role")
def get_my_role(
    current_user: dict = Depends(get_current_user)
):
    """Get current user's role and permissions."""
    user = bigquery.get_user_by_email(current_user.get("email", ""))
    
    if not user:
        # Auto-create user on first access
        user = bigquery.create_user(
            email=current_user.get("email", ""),
            name=current_user.get("name", ""),
            role="member"
        )
    
    role = user.get("role", "member")
    
    permissions = []
    if role == "admin":
        permissions = ["*"]
    elif role == "pm":
        permissions = ["projects.*", "tasks.*", "risks.*", "reports.*", "meetings.*"]
    else:
        permissions = ["projects.read", "tasks.read", "tasks.update", "risks.read", "meetings.read"]
    
    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": role,
        "permissions": permissions,
        "is_admin": role == "admin"
    }

