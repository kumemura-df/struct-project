"""Project Progress DB API - Main Application.

Features:
- Structured logging for Cloud Logging
- CORS configuration for frontend
- Request tracing middleware
- Comprehensive error handling
"""
import json
import os
import sys
import time
import uuid
import logging
from contextvars import ContextVar
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
VERSION = "1.0.0"

# Request context for tracing
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class StructuredLogFormatter(logging.Formatter):
    """Format logs as JSON for Cloud Logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "timestamp": self.formatTime(record),
            "service": "api",
            "environment": ENVIRONMENT,
        }
        
        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)


def setup_logging():
    """Configure structured logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add structured handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Use structured format in non-dev environments
    if ENVIRONMENT in ("prod", "production", "staging"):
        handler.setFormatter(StructuredLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    
    root_logger.addHandler(handler)


# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title="Project Progress DB API",
    description="AI-powered meeting notes analysis and project progress tracking",
    version=VERSION,
    docs_url="/docs" if ENVIRONMENT != "prod" else None,
    redoc_url="/redoc" if ENVIRONMENT != "prod" else None,
)

# Trust proxy headers for Cloud Run (HTTPS termination)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])


# Request tracing middleware
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next: Callable):
    """Add request tracing and logging."""
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
    request_id_var.set(request_id)
    
    start_time = time.time()
    
    # Process request
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log request completion
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
        }
        
        # Log level based on status
        if response.status_code >= 500:
            logger.error(f"Request completed: {json.dumps(log_data)}")
        elif response.status_code >= 400:
            logger.warning(f"Request completed: {json.dumps(log_data)}")
        else:
            logger.info(f"Request completed: {json.dumps(log_data)}")
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.exception(f"Request failed: {request.method} {request.url.path} ({duration_ms}ms)")
        raise


# CORS configuration
allowed_origins = [FRONTEND_URL]
if ENVIRONMENT == "dev":
    allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with structured response."""
    request_id = request_id_var.get()
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={"extra_fields": {"request_id": request_id, "errors": str(exc.errors())}}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request parameters",
            "details": exc.errors(),
            "request_id": request_id,
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions with structured response."""
    request_id = request_id_var.get()
    logger.exception(f"Unhandled exception: {exc}")
    
    # Don't expose internal details in production
    if ENVIRONMENT in ("prod", "production"):
        message = "An unexpected error occurred. Please try again later."
    else:
        message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": message,
            "code": "INTERNAL_ERROR",
            "request_id": request_id,
        }
    )


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "message": "Project Progress DB API is running",
        "version": VERSION,
        "environment": ENVIRONMENT,
    }


@app.get("/health")
def health_check():
    """Detailed health check for load balancers."""
    return {
        "status": "healthy",
        "version": VERSION,
        "environment": ENVIRONMENT,
    }


# Import and include routers
from routers import upload, projects, tasks, auth, risks, export

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(risks.router)
app.include_router(export.router)

logger.info(f"API initialized: version={VERSION}, environment={ENVIRONMENT}")
