from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional, List
from services import bigquery
from auth.middleware import get_current_user
from schemas import TaskUpdate, TaskStatus, Priority, SortOrder

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/")
def get_tasks(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[List[str]] = Query(None, description="Filter by status (can specify multiple)"),
    priority: Optional[List[str]] = Query(None, description="Filter by priority (can specify multiple)"),
    owner: Optional[str] = Query(None, description="Filter by owner (partial match)"),
    due_date_from: Optional[str] = Query(None, description="Filter by due date (from)"),
    due_date_to: Optional[str] = Query(None, description="Filter by due date (to)"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    sort_by: str = Query("due_date", description="Sort by field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_user)
):
    """Get tasks with pagination, filtering, and sorting."""
    try:
        result = bigquery.list_tasks_paginated(
            project_id=project_id,
            status=status,
            priority=priority,
            owner=owner,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
def get_task(
    task_id: str = Path(..., description="Task ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get a single task by ID."""
    try:
        task = bigquery.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}")
def update_task(
    task_id: str = Path(..., description="Task ID"),
    updates: TaskUpdate = None,
    current_user: dict = Depends(get_current_user)
):
    """Update a task."""
    try:
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        update_dict = updates.model_dump(exclude_none=True)
        # Convert enums to strings
        for key, value in update_dict.items():
            if hasattr(value, 'value'):
                update_dict[key] = value.value
        
        user_id = current_user.get("email") or current_user.get("sub")
        result = bigquery.update_task(task_id, update_dict, user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        return result
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
def delete_task(
    task_id: str = Path(..., description="Task ID"),
    current_user: dict = Depends(get_current_user)
):
    """Delete a task (soft delete)."""
    try:
        user_id = current_user.get("email") or current_user.get("sub")
        success = bigquery.delete_task(task_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
