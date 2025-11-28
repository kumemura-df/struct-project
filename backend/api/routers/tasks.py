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
