from fastapi import APIRouter, HTTPException, Depends, Query
from services import bigquery
from auth.middleware import get_current_user
from typing import Optional

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
def get_projects(current_user: dict = Depends(get_current_user)):
    try:
        projects = bigquery.list_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def get_all_health_scores(current_user: dict = Depends(get_current_user)):
    """Get health scores for all projects."""
    try:
        return bigquery.get_all_project_health_scores()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/health")
def get_project_health(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get health score for a specific project."""
    try:
        return bigquery.get_project_health_score(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
