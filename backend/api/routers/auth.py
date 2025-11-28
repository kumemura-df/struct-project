"""Authentication endpoints."""
import os
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional

from auth import (
    get_authorization_url,
    exchange_code_for_token,
    verify_google_token,
    create_access_token,
    get_current_user_optional,
)
from fastapi import Depends

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/login")
async def login(request: Request, redirect_to: Optional[str] = None):
    """Initiate Google OAuth flow."""
    # Build redirect URI
    # Force HTTPS on Cloud Run to avoid redirect_uri_mismatch
    host = str(request.url.netloc)
    if "run.app" in host:
        scheme = "https"
    else:
        scheme = request.url.scheme
    redirect_uri = f"{scheme}://{host}/auth/callback"
    
    # Get authorization URL
    auth_url = get_authorization_url(
        redirect_uri=redirect_uri,
        state=redirect_to or FRONTEND_URL,
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(request: Request, code: str, state: Optional[str] = None):
    """Handle OAuth callback from Google."""
    try:
        # Build redirect URI
        # Force HTTPS on Cloud Run to avoid redirect_uri_mismatch
        host = str(request.url.netloc)
        if "run.app" in host:
            scheme = "https"
        else:
            scheme = request.url.scheme
        redirect_uri = f"{scheme}://{host}/auth/callback"
        
        # Exchange code for tokens
        tokens = exchange_code_for_token(code, redirect_uri)
        
        # Verify ID token and get user info
        user_info = verify_google_token(tokens["id_token"])
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or unauthorized domain"
            )
        
        # Create JWT access token
        access_token = create_access_token(data={
            "sub": user_info["sub"],
            "email": user_info["email"],
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        })
        
        # Redirect to frontend with token
        redirect_url = state or FRONTEND_URL
        # Add token as query parameter for frontend to store
        response = RedirectResponse(
            url=f"{redirect_url}?token={access_token}",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
        # Also set as HTTP-only cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            max_age=60 * 60 * 24,  # 24 hours
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout")
async def logout():
    """Logout user by clearing cookie."""
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key="access_token")
    return response


@router.get("/me")
async def get_me(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get current user information."""
    if not current_user:
        return {"authenticated": False, "user": None}
    
    return {
        "authenticated": True,
        "user": {
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "picture": current_user.get("picture"),
        }
    }


@router.get("/dev-login")
async def dev_login(request: Request):
    """Development only login to bypass Google Auth."""
    # Check if we are in a production environment
    environment = os.getenv("ENVIRONMENT", "dev")
    if environment == "production":
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login not available in production"
        )
    
    # Create a mock user token
    user_info = {
        "sub": "dev-user-123",
        "email": "dev@example.com",
        "name": "Dev User",
        "picture": "https://via.placeholder.com/150"
    }
    
    access_token = create_access_token(data=user_info)
    
    # Redirect to frontend with token
    redirect_url = FRONTEND_URL
    response = RedirectResponse(
        url=f"{redirect_url}?token={access_token}",
        status_code=status.HTTP_303_SEE_OTHER
    )
    
    # Also set as HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False, # Not secure for dev
        samesite="lax",
        max_age=60 * 60 * 24,  # 24 hours
    )
    
    return response
