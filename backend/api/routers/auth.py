"""Authentication endpoints with security hardening."""
import os
import logging
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional

from auth import (
    get_authorization_url,
    exchange_code_for_token,
    verify_google_token,
    create_access_token,
    get_current_user_optional,
    is_oauth_configured,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Feature flags
DEV_LOGIN_ENABLED = os.getenv("DEV_LOGIN_ENABLED", "").lower() == "true" or ENVIRONMENT == "dev"


def _get_secure_cookie_settings(request: Request) -> dict:
    """Get secure cookie settings based on request context."""
    is_secure = request.url.scheme == "https" or "run.app" in str(request.url.netloc)
    
    return {
        "httponly": True,
        "secure": is_secure,
        "samesite": "lax",
        "max_age": 60 * 60 * 24,  # 24 hours
        "path": "/",
    }


def _build_redirect_uri(request: Request) -> str:
    """Build the OAuth redirect URI from request context."""
    host = str(request.url.netloc)
    # Force HTTPS on Cloud Run
    if "run.app" in host:
        scheme = "https"
    else:
        scheme = request.url.scheme
    return f"{scheme}://{host}/auth/callback"


@router.get("/login")
async def login(request: Request, redirect_to: Optional[str] = None):
    """Initiate Google OAuth flow.
    
    Args:
        redirect_to: Optional URL to redirect after successful login
    """
    if not is_oauth_configured():
        if DEV_LOGIN_ENABLED:
            return RedirectResponse(url="/auth/dev-login", status_code=status.HTTP_302_FOUND)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth is not configured"
        )
    
    redirect_uri = _build_redirect_uri(request)
    
    # Validate redirect_to to prevent open redirect attacks
    state = redirect_to or FRONTEND_URL
    if not state.startswith(FRONTEND_URL) and not state.startswith("/"):
        logger.warning(f"Invalid redirect_to blocked: {state}")
        state = FRONTEND_URL
    
    auth_url = get_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
    )
    
    logger.info(f"OAuth login initiated, redirect_to: {state}")
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(request: Request, code: str, state: Optional[str] = None, error: Optional[str] = None):
    """Handle OAuth callback from Google.
    
    Sets HttpOnly cookie with JWT token - does NOT expose token in URL.
    """
    # Handle OAuth errors
    if error:
        logger.error(f"OAuth error: {error}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error={error}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    try:
        redirect_uri = _build_redirect_uri(request)
        
        # Exchange code for tokens
        tokens = exchange_code_for_token(code, redirect_uri)
        
        # Verify ID token and get user info
        user_info = verify_google_token(tokens["id_token"])
        if not user_info:
            logger.warning("Token verification failed or domain not allowed")
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
            "auth_method": "google_oauth",
        })
        
        # Validate redirect URL
        redirect_url = state or FRONTEND_URL
        if not redirect_url.startswith(FRONTEND_URL) and not redirect_url.startswith("/"):
            redirect_url = FRONTEND_URL
        
        # Create response with ONLY HttpOnly cookie (no token in URL)
        response = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_303_SEE_OTHER
        )
        
        # Set secure HttpOnly cookie
        cookie_settings = _get_secure_cookie_settings(request)
        response.set_cookie(
            key="access_token",
            value=access_token,
            **cookie_settings
        )
        
        logger.info(f"User logged in: {user_info['email']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication failed"
        )


@router.post("/logout")
async def logout(request: Request):
    """Logout user by clearing cookie."""
    response = JSONResponse(content={"message": "Logged out successfully"})
    
    # Clear cookie with same settings used to set it
    cookie_settings = _get_secure_cookie_settings(request)
    response.delete_cookie(
        key="access_token",
        path=cookie_settings["path"],
        secure=cookie_settings["secure"],
        samesite=cookie_settings["samesite"],
    )
    
    logger.info("User logged out")
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
    """Development-only login to bypass Google OAuth.
    
    SECURITY: This endpoint is ONLY available when:
    1. ENVIRONMENT is "dev" (default for local development)
    2. DEV_LOGIN_ENABLED is explicitly set to "true"
    
    This endpoint is automatically disabled in staging/production.
    """
    # Strict environment check
    if ENVIRONMENT in ("prod", "production", "staging"):
        logger.warning(f"Dev login attempt blocked in {ENVIRONMENT} environment")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development login is disabled in this environment"
        )
    
    if not DEV_LOGIN_ENABLED:
        logger.warning("Dev login attempt blocked - DEV_LOGIN_ENABLED is false")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development login is disabled"
        )
    
    # Create a mock user token
    user_info = {
        "sub": "dev-user-123",
        "email": "dev@localhost",
        "name": "Development User",
        "picture": None,
        "auth_method": "dev_login",
    }
    
    access_token = create_access_token(data=user_info)
    
    # Redirect to frontend
    response = RedirectResponse(
        url=FRONTEND_URL,
        status_code=status.HTTP_303_SEE_OTHER
    )
    
    # Set cookie (not secure for local dev)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days for dev
        path="/",
    )
    
    logger.info("Dev user logged in")
    return response


@router.get("/status")
async def auth_status():
    """Get authentication system status (for debugging)."""
    return {
        "oauth_configured": is_oauth_configured(),
        "dev_login_enabled": DEV_LOGIN_ENABLED,
        "environment": ENVIRONMENT,
    }
