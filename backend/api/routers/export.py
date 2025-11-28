"""Export endpoints for downloading data as CSV."""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from typing import Optional
from services import bigquery, export
from auth.middleware import get_current_user

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/projects")
def export_projects(current_user: dict = Depends(get_current_user)):
    """Export all projects as CSV."""
    try:
        projects = bigquery.list_projects()
        csv_content = export.generate_projects_csv(projects)
        filename = export.get_export_filename("projects")
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
def export_tasks(
    project_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Export tasks as CSV, optionally filtered by project."""
    try:
        tasks = bigquery.list_tasks(project_id=project_id)
        csv_content = export.generate_tasks_csv(tasks)
        filename = export.get_export_filename("tasks")
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risks")
def export_risks(
    project_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    meeting_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Export risks as CSV, optionally filtered."""
    try:
        risks = bigquery.list_risks(
            project_id=project_id,
            risk_level=risk_level,
            meeting_id=meeting_id
        )
        csv_content = export.generate_risks_csv(risks)
        filename = export.get_export_filename("risks")
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions")
def export_decisions(
    project_id: Optional[str] = Query(None),
    meeting_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Export decisions as CSV, optionally filtered."""
    try:
        decisions = bigquery.list_decisions(
            project_id=project_id,
            meeting_id=meeting_id
        )
        csv_content = export.generate_decisions_csv(decisions)
        filename = export.get_export_filename("decisions")
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
