"""Diff detection endpoints for tracking changes between meetings."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/diff", tags=["diff"])


@router.get("/meetings/{meeting_id}")
def get_meeting_diff(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a summary of all changes since the specified meeting.
    Returns new tasks, status changes, and escalated risks.
    """
    try:
        diff = bigquery.get_meeting_diff_summary(meeting_id)
        if not diff:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return diff
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/new")
def get_new_tasks(
    since_meeting_id: Optional[str] = Query(None, description="Meeting ID to compare from"),
    since_date: Optional[str] = Query(None, description="Date to compare from (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get newly created tasks since a meeting or date.
    """
    try:
        if since_meeting_id:
            tasks = bigquery.get_new_tasks_since_meeting(since_meeting_id)
        elif since_date:
            tasks = bigquery.get_new_tasks_since_date(since_date)
        else:
            # Default: tasks from last 7 days
            from datetime import datetime, timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            tasks = bigquery.get_new_tasks_since_date(week_ago)
        
        return {
            "items": tasks[:limit],
            "total": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/changed")
def get_changed_tasks(
    since_meeting_id: Optional[str] = Query(None, description="Meeting ID to compare from"),
    since_date: Optional[str] = Query(None, description="Date to compare from (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get tasks with status changes since a meeting or date.
    """
    try:
        if since_meeting_id:
            changes = bigquery.get_status_changes_since_meeting(since_meeting_id)
        elif since_date:
            changes = bigquery.get_status_changes_since_date(since_date)
        else:
            from datetime import datetime, timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            changes = bigquery.get_status_changes_since_date(week_ago)
        
        return {
            "items": changes[:limit],
            "total": len(changes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risks/escalated")
def get_escalated_risks(
    since_meeting_id: Optional[str] = Query(None, description="Meeting ID to compare from"),
    since_date: Optional[str] = Query(None, description="Date to compare from (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get risks that have escalated (increased in level) since a meeting or date.
    """
    try:
        if since_meeting_id:
            risks = bigquery.get_escalated_risks_since_meeting(since_meeting_id)
        elif since_date:
            risks = bigquery.get_escalated_risks_since_date(since_date)
        else:
            from datetime import datetime, timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            risks = bigquery.get_escalated_risks_since_date(week_ago)
        
        return {
            "items": risks[:limit],
            "total": len(risks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/{task_id}")
def get_task_timeline(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the complete lifecycle/timeline of a task from creation to current state.
    """
    try:
        lifecycle = bigquery.get_task_lifecycle(task_id)
        if not lifecycle or not lifecycle.get("task"):
            raise HTTPException(status_code=404, detail="Task not found")
        return lifecycle
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
def compare_meetings(
    from_meeting_id: str = Query(..., description="Earlier meeting ID"),
    to_meeting_id: Optional[str] = Query(None, description="Later meeting ID (default: now)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Compare two meetings and show all changes between them.
    """
    try:
        # Get from meeting info
        from_meeting = bigquery.get_meeting(from_meeting_id)
        if not from_meeting:
            raise HTTPException(status_code=404, detail="From meeting not found")
        
        to_meeting = None
        if to_meeting_id:
            to_meeting = bigquery.get_meeting(to_meeting_id)
            if not to_meeting:
                raise HTTPException(status_code=404, detail="To meeting not found")
        
        # Get changes since from_meeting
        diff = bigquery.get_meeting_diff_summary(from_meeting_id)
        
        return {
            "from_meeting": {
                "meeting_id": from_meeting_id,
                "title": from_meeting.get("title"),
                "date": from_meeting.get("meeting_date")
            },
            "to_meeting": {
                "meeting_id": to_meeting_id,
                "title": to_meeting.get("title") if to_meeting else "現在",
                "date": to_meeting.get("meeting_date") if to_meeting else None
            } if to_meeting_id else {"title": "現在"},
            "changes": diff
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

