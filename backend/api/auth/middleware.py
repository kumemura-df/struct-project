"""Authentication middleware and dependencies."""
from typing import Optional, Dict, Any, List
from functools import wraps
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt import verify_token

security = HTTPBearer(auto_error=False)

# Role hierarchy: ADMIN > PM > MEMBER
ROLE_HIERARCHY = {"ADMIN": 3, "PM": 2, "MEMBER": 1}


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token (optional, returns None if not authenticated)."""
    # Try to get token from Authorization header
    token = None
    if credentials:
        token = credentials.credentials

    # Try to get token from cookie as fallback
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        return None

    # Verify token
    payload = verify_token(token)
    if not payload:
        return None

    # Add role from database
    from services import local_db
    email = payload.get("email")
    if email:
        user_data = local_db.get_or_create_user(
            email=email,
            name=payload.get("name"),
            picture=payload.get("picture")
        )
        payload["role"] = user_data.get("role", "MEMBER")
        payload["user_id"] = user_data.get("user_id")

    return payload


async def get_current_user(
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get current user from JWT token (required, raises exception if not authenticated)."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: List[str]):
    """Dependency to require specific roles."""
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", "MEMBER")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_roles}, your role: {user_role}"
            )
        return current_user
    return role_checker


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require ADMIN role."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_pm_or_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require PM or ADMIN role."""
    if current_user.get("role") not in ["ADMIN", "PM"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PM or Admin access required"
        )
    return current_user


def has_role_or_higher(user_role: str, required_role: str) -> bool:
    """Check if user has the required role or higher in the hierarchy."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def require_auth(func):
    """Decorator to require authentication for a route."""
    async def wrapper(*args, current_user: Dict[str, Any] = Depends(get_current_user), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper
