from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Project Progress DB API")

# Trust proxy headers for Cloud Run (HTTPS termination)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# Get frontend URL from environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Allow CORS for frontend with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],  # Include localhost for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with structured response."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request parameters",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions with structured response."""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "code": "INTERNAL_ERROR"
        }
    )

@app.get("/")
def read_root():
    return {"message": "Project Progress DB API is running", "version": "1.0.0"}

# Import and include routers
from routers import upload, projects, tasks, auth, risks, export, meetings, settings, agenda, users

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(risks.router)
app.include_router(export.router)
app.include_router(meetings.router)
app.include_router(settings.router)
app.include_router(agenda.router)
app.include_router(users.router)

