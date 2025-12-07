"""Meetings API endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("/")
def get_meetings(
    status: Optional[str] = Query(None, description="Filter by status (PENDING/DONE/ERROR)"),
    search: Optional[str] = Query(None, description="Search in title or meeting_id"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_user)
):
    """Get meetings with pagination, filtering, and sorting."""
    try:
        result = bigquery.list_meetings_paginated(
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}")
def get_meeting(
    meeting_id: str = Path(..., description="Meeting ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get a single meeting by ID with extraction counts."""
    try:
        meeting = bigquery.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="会議が見つかりません")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

