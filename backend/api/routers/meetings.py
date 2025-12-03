"""Meeting management endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("/")
def get_meetings(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all meetings with optional filtering by project.

    Returns list of meetings ordered by meeting_date descending.
    """
    try:
        meetings = bigquery.list_meetings(project_id=project_id)
        return meetings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
