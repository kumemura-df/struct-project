"""Authentication middleware and dependencies."""
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt import verify_token

security = HTTPBearer(auto_error=False)


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


def require_auth(func):
    """Decorator to require authentication for a route."""
    async def wrapper(*args, current_user: Dict[str, Any] = Depends(get_current_user), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper
