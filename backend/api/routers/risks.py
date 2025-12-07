"""Risk management endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional, List
from services import bigquery
from auth.middleware import get_current_user
from schemas import RiskUpdate, DecisionUpdate, RiskLevel, SortOrder

router = APIRouter(prefix="/risks", tags=["risks"])


@router.get("/")
def get_risks(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    risk_level: Optional[List[str]] = Query(None, description="Filter by risk level (can specify multiple)"),
    meeting_id: Optional[str] = Query(None, description="Filter by meeting ID"),
    owner: Optional[str] = Query(None, description="Filter by owner (partial match)"),
    search: Optional[str] = Query(None, description="Search in risk description"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_user)
):
    """Get risks with pagination, filtering, and sorting."""
    try:
        result = bigquery.list_risks_paginated(
            project_id=project_id,
            meeting_id=meeting_id,
            risk_level=risk_level,
            owner=owner,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        return result
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
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    meeting_id: Optional[str] = Query(None, description="Filter by meeting ID"),
    search: Optional[str] = Query(None, description="Search in decision description"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_user)
):
    """Get decisions with pagination, filtering, and sorting."""
    try:
        result = bigquery.list_decisions_paginated(
            project_id=project_id,
            meeting_id=meeting_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/{decision_id}")
def get_decision(
    decision_id: str = Path(..., description="Decision ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get a single decision by ID."""
    try:
        decision = bigquery.get_decision(decision_id)
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        return decision
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/decisions/{decision_id}")
def update_decision(
    decision_id: str = Path(..., description="Decision ID"),
    updates: DecisionUpdate = None,
    current_user: dict = Depends(get_current_user)
):
    """Update a decision."""
    try:
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        update_dict = updates.model_dump(exclude_none=True)
        user_id = current_user.get("email") or current_user.get("sub")
        result = bigquery.update_decision(decision_id, update_dict, user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Decision not found")
        return result
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/decisions/{decision_id}")
def delete_decision(
    decision_id: str = Path(..., description="Decision ID"),
    current_user: dict = Depends(get_current_user)
):
    """Delete a decision (soft delete)."""
    try:
        user_id = current_user.get("email") or current_user.get("sub")
        success = bigquery.delete_decision(decision_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Decision not found")
        return {"message": "Decision deleted successfully"}
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{risk_id}")
def get_risk(
    risk_id: str = Path(..., description="Risk ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get a single risk by ID."""
    try:
        risk = bigquery.get_risk(risk_id)
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        return risk
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{risk_id}")
def update_risk(
    risk_id: str = Path(..., description="Risk ID"),
    updates: RiskUpdate = None,
    current_user: dict = Depends(get_current_user)
):
    """Update a risk."""
    try:
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        update_dict = updates.model_dump(exclude_none=True)
        # Convert enums to strings
        for key, value in update_dict.items():
            if hasattr(value, 'value'):
                update_dict[key] = value.value
        
        user_id = current_user.get("email") or current_user.get("sub")
        result = bigquery.update_risk(risk_id, update_dict, user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Risk not found")
        return result
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{risk_id}")
def delete_risk(
    risk_id: str = Path(..., description="Risk ID"),
    current_user: dict = Depends(get_current_user)
):
    """Delete a risk (soft delete)."""
    try:
        user_id = current_user.get("email") or current_user.get("sub")
        success = bigquery.delete_risk(risk_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Risk not found")
        return {"message": "Risk deleted successfully"}
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
