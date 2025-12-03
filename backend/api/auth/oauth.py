"""Google OAuth integration with enhanced security."""
import os
import sys
import logging
from typing import Optional, Dict, Any

from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow

logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# OAuth configuration
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
REDIRECT_URI_PATH = "/auth/callback"

# Parse allowed domains
_allowed_domains_raw = os.getenv("ALLOWED_OAUTH_DOMAINS", "")
ALLOWED_DOMAINS = [d.strip() for d in _allowed_domains_raw.split(",") if d.strip()]

# Validate configuration in production
if ENVIRONMENT in ("prod", "production"):
    missing_config = []
    if not CLIENT_ID:
        missing_config.append("OAUTH_CLIENT_ID")
    if not CLIENT_SECRET:
        missing_config.append("OAUTH_CLIENT_SECRET")
    if not ALLOWED_DOMAINS:
        missing_config.append("ALLOWED_OAUTH_DOMAINS")
    
    if missing_config:
        logger.critical(f"Missing required OAuth configuration in production: {', '.join(missing_config)}")
        sys.exit(1)
    
    logger.info(f"OAuth configured with allowed domains: {ALLOWED_DOMAINS}")

elif ENVIRONMENT == "staging":
    # Staging: warn but don't fail if domains not set
    if not ALLOWED_DOMAINS:
        logger.warning("⚠️ ALLOWED_OAUTH_DOMAINS not set in staging - any Google account can login")
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.warning("⚠️ OAuth credentials not fully configured in staging")

else:
    # Dev: log warning for missing config
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.warning("⚠️ OAuth credentials not configured - use /auth/dev-login for development")


# Scopes required for OAuth
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def is_oauth_configured() -> bool:
    """Check if OAuth is properly configured."""
    return bool(CLIENT_ID and CLIENT_SECRET)


def create_oauth_flow(redirect_uri: str) -> Flow:
    """Create OAuth flow for Google authentication.
    
    Args:
        redirect_uri: The callback URL after OAuth completion
        
    Returns:
        Configured OAuth Flow object
        
    Raises:
        ValueError: If OAuth is not configured
    """
    if not is_oauth_configured():
        raise ValueError("OAuth is not configured. Set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET.")
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = redirect_uri
    return flow


def get_authorization_url(redirect_uri: str, state: Optional[str] = None) -> str:
    """Get the Google OAuth authorization URL.
    
    Args:
        redirect_uri: Callback URL
        state: Optional state parameter to pass through OAuth flow
        
    Returns:
        Authorization URL to redirect user to
    """
    flow = create_oauth_flow(redirect_uri)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="select_account",  # Always show account selector
    )
    return authorization_url


def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange authorization code for access token.
    
    Args:
        code: Authorization code from OAuth callback
        redirect_uri: Same redirect URI used in authorization
        
    Returns:
        Dict containing access_token, refresh_token, and id_token
    """
    flow = create_oauth_flow(redirect_uri)
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "id_token": credentials.id_token,
    }


def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Google ID token and return user info.
    
    Performs the following validations:
    1. Token signature verification
    2. Audience (aud) matches our CLIENT_ID
    3. Email domain is in ALLOWED_DOMAINS (if configured)
    
    Args:
        token: Google ID token to verify
        
    Returns:
        User info dict if valid, None otherwise
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), CLIENT_ID
        )
        
        # Verify the token is for our app
        if idinfo["aud"] != CLIENT_ID:
            logger.warning(f"Token audience mismatch: {idinfo['aud']} != {CLIENT_ID}")
            return None
        
        email = idinfo.get("email", "")
        email_domain = email.split("@")[1] if "@" in email else ""
        hosted_domain = idinfo.get("hd", "")  # Google Workspace domain
        
        # Check allowed domains if configured
        if ALLOWED_DOMAINS:
            # Check hosted domain first (for Google Workspace accounts)
            if hosted_domain and hosted_domain in ALLOWED_DOMAINS:
                pass  # Allowed
            # Fall back to email domain
            elif email_domain in ALLOWED_DOMAINS:
                pass  # Allowed
            else:
                logger.warning(
                    f"Domain not allowed: email={email}, hd={hosted_domain}, "
                    f"allowed={ALLOWED_DOMAINS}"
                )
                return None
        
        # Log successful authentication
        logger.info(f"User authenticated: {email}")
        
        return {
            "email": email,
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
            "sub": idinfo["sub"],  # Google user ID
            "email_verified": idinfo.get("email_verified", False),
            "hosted_domain": hosted_domain,
        }
        
    except ValueError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def get_user_info_from_credentials(credentials) -> Optional[Dict[str, Any]]:
    """Get user info from OAuth credentials.
    
    Args:
        credentials: Google OAuth credentials object
        
    Returns:
        User info dict or None
    """
    if credentials.id_token:
        return verify_google_token(credentials.id_token)
    return None
