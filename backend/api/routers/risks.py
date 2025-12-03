"""Risk management endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/risks", tags=["risks"])

@router.get("/")
def get_risks(
    project_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    meeting_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all risks with optional filtering."""
    try:
        risks = bigquery.list_risks(
            project_id=project_id,
            risk_level=risk_level,
            meeting_id=meeting_id
        )
        return risks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_risk_statistics(current_user: dict = Depends(get_current_user)):
    """Get risk statistics (count by level and project)."""
    try:
        stats = bigquery.get_risk_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/decisions")
def get_decisions(
    project_id: Optional[str] = Query(None),
    meeting_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all decisions with optional filtering."""
    try:
        decisions = bigquery.list_decisions(
            project_id=project_id,
            meeting_id=meeting_id
        )
        return decisions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/difference")
def get_risks_difference(
    prev_meeting_id: str = Query(..., description="Previous meeting ID"),
    curr_meeting_id: str = Query(..., description="Current meeting ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get risk differences between two meetings.

    Returns:
        - added: New risks in current meeting
        - removed: Risks not in current meeting
        - level_changed: Risks with level changes (escalated/de-escalated)
        - unchanged: Risks with no changes
    """
    try:
        prev_risks = bigquery.list_risks_by_meeting(prev_meeting_id, project_id)
        curr_risks = bigquery.list_risks_by_meeting(curr_meeting_id, project_id)

        diff = bigquery.compare_risks(prev_risks, curr_risks)

        # Add summary counts
        diff["summary"] = {
            "added_count": len(diff["added"]),
            "removed_count": len(diff["removed"]),
            "level_changed_count": len(diff["level_changed"]),
            "unchanged_count": len(diff["unchanged"]),
            "total_changes": (
                len(diff["added"]) +
                len(diff["removed"]) +
                len(diff["level_changed"])
            )
        }

        # Identify escalated risks (level increased)
        level_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        diff["escalated"] = [
            item for item in diff["level_changed"]
            if level_order.get(item["curr_level"], 0) > level_order.get(item["prev_level"], 0)
        ]
        diff["de_escalated"] = [
            item for item in diff["level_changed"]
            if level_order.get(item["curr_level"], 0) < level_order.get(item["prev_level"], 0)
        ]

        return diff
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
