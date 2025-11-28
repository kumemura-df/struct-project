from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class MeetingMetadata(BaseModel):
    title: str
    participants: List[str]
    date: date

class Task(BaseModel):
    task_id: Optional[str] = None
    task_title: str
    task_description: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None
    status: str
    priority: str
    source_sentence: Optional[str] = None

class Risk(BaseModel):
    risk_id: Optional[str] = None
    risk_description: str
    risk_level: str
    owner: Optional[str] = None
    source_sentence: Optional[str] = None

class Decision(BaseModel):
    decision_id: Optional[str] = None
    decision_content: str
    source_sentence: Optional[str] = None

class MeetingExtractionResult(BaseModel):
    tasks: List[Task]
    risks: List[Risk]
    decisions: List[Decision]
    project_name: Optional[str] = None
