"""User management API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from services import local_db
from auth.middleware import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])


class UserRoleUpdate(BaseModel):
    role: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str]
    picture: Optional[str]
    role: str
    created_at: str
    updated_at: str


@router.get("/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user's information including role."""
    return {
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "picture": current_user.get("picture"),
        "role": current_user.get("role", "MEMBER"),
        "user_id": current_user.get("user_id")
    }


@router.get("/", response_model=List[UserResponse])
def list_all_users(current_user: dict = Depends(require_admin)):
    """List all users (Admin only)."""
    try:
        users = local_db.list_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{email}")
def get_user(email: str, current_user: dict = Depends(require_admin)):
    """Get a specific user by email (Admin only)."""
    try:
        user = local_db.get_user_role(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{email}/role")
def update_user_role(
    email: str,
    role_update: UserRoleUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update a user's role (Admin only)."""
    try:
        # Validate role
        if role_update.role not in local_db.VALID_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {local_db.VALID_ROLES}"
            )

        # Prevent demoting the last admin
        if role_update.role != "ADMIN":
            target_user = local_db.get_user_role(email)
            if target_user and target_user.get("role") == "ADMIN":
                admin_count = local_db.count_admins()
                if admin_count <= 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot demote the last admin"
                    )

        # Prevent self-demotion from admin
        if email == current_user.get("email") and role_update.role != "ADMIN":
            raise HTTPException(
                status_code=400,
                detail="Cannot demote yourself from admin"
            )

        updated = local_db.update_user_role(email, role_update.role)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": f"User {email} role updated to {role_update.role}", "user": updated}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{email}")
def delete_user(email: str, current_user: dict = Depends(require_admin)):
    """Delete a user (Admin only)."""
    try:
        # Prevent self-deletion
        if email == current_user.get("email"):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete yourself"
            )

        # Prevent deleting the last admin
        target_user = local_db.get_user_role(email)
        if target_user and target_user.get("role") == "ADMIN":
            admin_count = local_db.count_admins()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete the last admin"
                )

        deleted = local_db.delete_user(email)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": f"User {email} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles/available")
def get_available_roles(current_user: dict = Depends(get_current_user)):
    """Get list of available roles."""
    return {
        "roles": local_db.VALID_ROLES,
        "descriptions": {
            "ADMIN": "Full access - can manage users, settings, and all data",
            "PM": "Project Manager - can manage projects, tasks, and risks",
            "MEMBER": "Member - can view data and upload meeting notes"
        }
    }
