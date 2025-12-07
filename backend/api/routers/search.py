"""Search and audit endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
def search_all(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results per entity type"),
    current_user: dict = Depends(get_current_user)
):
    """
    Search across all entities (tasks, risks, projects, decisions).
    Returns results grouped by entity type.
    """
    try:
        results = bigquery.search_all(q, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit")
def get_audit_log(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (task, risk, project, decision)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit log entries.
    Shows history of changes made to entities.
    """
    try:
        entries = bigquery.get_audit_log(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset
        )
        return {"entries": entries, "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

