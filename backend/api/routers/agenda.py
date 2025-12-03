"""API endpoints for meeting agenda generation."""
from fastapi import APIRouter, HTTPException, Depends, Query
from services import bigquery, ai_processor
from auth.middleware import get_current_user
from typing import Optional

router = APIRouter(prefix="/agenda", tags=["agenda"])


@router.get("/generate")
def generate_agenda(
    project_id: str = Query(..., description="Project ID to generate agenda for"),
    current_user: dict = Depends(get_current_user)
):
    """Generate a suggested meeting agenda for a project."""
    try:
        # Get project info
        projects = bigquery.list_projects()
        project = next((p for p in projects if p["project_id"] == project_id), None)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project_name = project.get("project_name", "Unknown Project")

        # Get tasks for the project
        tasks = bigquery.list_tasks(project_id)

        # Get risks for the project
        risks = bigquery.list_risks(project_id=project_id)

        # Get decisions for the project
        decisions = bigquery.list_decisions(project_id=project_id)

        # Get recent meetings
        meetings = bigquery.list_meetings(project_id=project_id)

        # Generate agenda
        agenda = ai_processor.generate_meeting_agenda(
            project_name=project_name,
            tasks=tasks,
            risks=risks,
            decisions=decisions,
            recent_meetings=meetings
        )

        return agenda

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/all")
def generate_portfolio_agenda(
    current_user: dict = Depends(get_current_user)
):
    """Generate a suggested agenda covering all projects (portfolio view)."""
    try:
        # Get all projects
        projects = bigquery.list_projects()

        if not projects:
            return {
                "agenda_items": [],
                "suggested_duration_minutes": 0,
                "key_discussion_points": ["No projects found"],
                "project_name": "Portfolio Overview"
            }

        # Aggregate data from all projects
        all_tasks = bigquery.list_tasks()
        all_risks = bigquery.list_risks()
        all_decisions = bigquery.list_decisions()
        all_meetings = bigquery.list_meetings()

        # Generate portfolio-level agenda
        agenda = ai_processor.generate_meeting_agenda(
            project_name="Portfolio Overview",
            tasks=all_tasks,
            risks=all_risks,
            decisions=all_decisions,
            recent_meetings=all_meetings
        )

        # Add project breakdown
        agenda["projects_count"] = len(projects)

        return agenda

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
