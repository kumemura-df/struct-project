"""Error models for API responses."""
from pydantic import BaseModel
from typing import Optional, Any, Dict


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    code: Optional[str] = None


class ValidationErrorDetail(BaseModel):
    """Validation error details."""
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "Validation Error"
    message: str
    details: list[ValidationErrorDetail]
