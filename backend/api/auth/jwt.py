"""JWT token management for authentication."""
import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Validate secret key
if not _SECRET_KEY:
    if ENVIRONMENT in ("prod", "production", "staging"):
        logger.critical("JWT_SECRET_KEY is required in production/staging environments")
        sys.exit(1)
    else:
        # Allow default only in dev
        _SECRET_KEY = "dev-secret-key-NOT-FOR-PRODUCTION"
        logger.warning("⚠️ Using insecure default JWT secret - DO NOT use in production!")

SECRET_KEY = _SECRET_KEY
ALGORITHM = "HS256"

# Token expiration settings per environment
TOKEN_EXPIRE_MINUTES = {
    "dev": 60 * 24 * 7,    # 7 days for development
    "staging": 60 * 24,     # 24 hours for staging
    "prod": 60 * 8,         # 8 hours for production
    "production": 60 * 8,
}

ACCESS_TOKEN_EXPIRE_MINUTES = TOKEN_EXPIRE_MINUTES.get(ENVIRONMENT, 60 * 24)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "env": ENVIRONMENT,  # Include environment for audit
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Additional validation for production
        if ENVIRONMENT in ("prod", "production"):
            # Verify token was created for this environment
            token_env = payload.get("env")
            if token_env and token_env not in ("prod", "production"):
                logger.warning(f"Token from non-production environment rejected: {token_env}")
                return None
        
        return payload
    except JWTError as e:
        logger.debug(f"Token verification failed: {e}")
        return None


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """Extract payload from token without verification (for debugging only).
    
    WARNING: This should only be used for debugging/logging purposes.
    Never trust unverified token claims for authorization decisions.
    
    Args:
        token: JWT token string
        
    Returns:
        Unverified payload, or None if parsing fails
    """
    try:
        return jwt.get_unverified_claims(token)
    except JWTError:
        return None


def is_token_expiring_soon(token: str, minutes: int = 30) -> bool:
    """Check if a token is expiring within the specified minutes.
    
    Args:
        token: JWT token string
        minutes: Number of minutes to check
        
    Returns:
        True if token expires within the specified time
    """
    payload = verify_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
    threshold = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    
    return exp_time <= threshold
