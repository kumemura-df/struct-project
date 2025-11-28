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
