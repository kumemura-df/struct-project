"""Authentication module."""
from .jwt import create_access_token, verify_token
from .oauth import (
    get_authorization_url,
    exchange_code_for_token,
    verify_google_token,
    get_user_info_from_credentials,
    is_oauth_configured,
)
from .middleware import get_current_user, get_current_user_optional, require_auth

__all__ = [
    "create_access_token",
    "verify_token",
    "get_authorization_url",
    "exchange_code_for_token",
    "verify_google_token",
    "get_user_info_from_credentials",
    "is_oauth_configured",
    "get_current_user",
    "get_current_user_optional",
    "require_auth",
]
