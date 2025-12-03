"""JWT token management for authentication."""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    import warnings
    warnings.warn("JWT_SECRET_KEY not set! Using insecure default for development only.", UserWarning)
    SECRET_KEY = "dev-secret-key-change-in-production-immediately"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """Extract payload from token without verification (for debugging)."""
    try:
        return jwt.get_unverified_claims(token)
    except JWTError:
        return None
