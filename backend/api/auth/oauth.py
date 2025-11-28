"""Google OAuth integration."""
import os
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow

# OAuth configuration
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
REDIRECT_URI_PATH = "/auth/callback"
ALLOWED_DOMAINS = os.getenv("ALLOWED_OAUTH_DOMAINS", "").split(",") if os.getenv("ALLOWED_OAUTH_DOMAINS") else []

# Scopes required for OAuth
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def create_oauth_flow(redirect_uri: str) -> Flow:
    """Create OAuth flow for Google authentication."""
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
    """Get the Google OAuth authorization URL."""
    flow = create_oauth_flow(redirect_uri)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
    )
    return authorization_url


def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange authorization code for access token."""
    flow = create_oauth_flow(redirect_uri)
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "id_token": credentials.id_token,
    }


def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Google ID token and return user info."""
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), CLIENT_ID
        )
        
        # Verify the token is for our app
        if idinfo["aud"] != CLIENT_ID:
            return None
        
        # Check allowed domains if configured
        if ALLOWED_DOMAINS and idinfo.get("hd") not in ALLOWED_DOMAINS:
            email = idinfo.get("email", "")
            email_domain = email.split("@")[1] if "@" in email else ""
            if email_domain not in ALLOWED_DOMAINS:
                return None
        
        return {
            "email": idinfo["email"],
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
            "sub": idinfo["sub"],  # Google user ID
            "email_verified": idinfo.get("email_verified", False),
        }
    except ValueError:
        return None


def get_user_info_from_credentials(credentials) -> Dict[str, Any]:
    """Get user info from OAuth credentials."""
    if credentials.id_token:
        return verify_google_token(credentials.id_token)
    return None
