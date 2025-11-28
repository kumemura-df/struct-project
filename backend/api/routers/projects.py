from fastapi import APIRouter, HTTPException, Depends
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/")
def get_projects(current_user: dict = Depends(get_current_user)):
    try:
        projects = bigquery.list_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
