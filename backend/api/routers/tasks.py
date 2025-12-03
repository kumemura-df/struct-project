from fastapi import APIRouter, HTTPException, Query, Depends
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/")
def get_tasks(project_id: str = Query(None), current_user: dict = Depends(get_current_user)):
    try:
        tasks = bigquery.list_tasks(project_id)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/difference")
def get_tasks_difference(
    prev_meeting_id: str = Query(..., description="Previous meeting ID"),
    curr_meeting_id: str = Query(..., description="Current meeting ID"),
    project_id: str = Query(None, description="Filter by project ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get task differences between two meetings.

    Returns:
        - added: New tasks in current meeting
        - removed: Tasks not in current meeting
        - status_changed: Tasks with status changes
        - priority_changed: Tasks with priority changes
        - unchanged: Tasks with no changes
    """
    try:
        prev_tasks = bigquery.list_tasks_by_meeting(prev_meeting_id, project_id)
        curr_tasks = bigquery.list_tasks_by_meeting(curr_meeting_id, project_id)

        diff = bigquery.compare_tasks(prev_tasks, curr_tasks)

        # Add summary counts
        diff["summary"] = {
            "added_count": len(diff["added"]),
            "removed_count": len(diff["removed"]),
            "status_changed_count": len(diff["status_changed"]),
            "priority_changed_count": len(diff["priority_changed"]),
            "unchanged_count": len(diff["unchanged"]),
            "total_changes": (
                len(diff["added"]) +
                len(diff["removed"]) +
                len(diff["status_changed"]) +
                len(diff["priority_changed"])
            )
        }

        return diff
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
