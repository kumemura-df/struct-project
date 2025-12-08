from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Optional
from services import bigquery
from auth.middleware import get_current_user
from schemas import ProjectUpdate, SortOrder

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
def get_projects(
    search: Optional[str] = Query(None, description="Search by project name"),
    sort_by: str = Query("updated_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    include_stats: bool = Query(False, description="Include stats for each project"),
    current_user: dict = Depends(get_current_user)
):
    """Get projects with pagination, search, and sorting.
    
    If include_stats=True, includes task/risk counts for each project
    to avoid N+1 API calls from the frontend.
    """
    try:
        result = bigquery.list_projects_paginated(
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
            include_stats=include_stats
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
def get_project(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get a single project by ID."""
    try:
        project = bigquery.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/stats")
def get_project_stats(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get statistics for a specific project."""
    try:
        stats = bigquery.get_project_stats(project_id)
        if not stats:
            raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}")
def update_project(
    project_id: str = Path(..., description="Project ID"),
    updates: ProjectUpdate = None,
    current_user: dict = Depends(get_current_user)
):
    """Update a project."""
    try:
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        update_dict = updates.model_dump(exclude_none=True)
        user_id = current_user.get("email") or current_user.get("sub")
        result = bigquery.update_project(project_id, update_dict, user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return result
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
def delete_project(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user)
):
    """Delete a project (soft delete)."""
    try:
        user_id = current_user.get("email") or current_user.get("sub")
        success = bigquery.delete_project(project_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
