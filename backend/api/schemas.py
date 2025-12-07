from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from enum import Enum


# Enums for validation
class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    UNKNOWN = "UNKNOWN"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


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


# ===== UPDATE Schemas =====

class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    task_title: Optional[str] = None
    task_description: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None


class RiskUpdate(BaseModel):
    """Schema for updating a risk."""
    risk_description: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    owner: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    project_name: Optional[str] = None


class DecisionUpdate(BaseModel):
    """Schema for updating a decision."""
    decision_description: Optional[str] = None
    decided_by: Optional[str] = None


# ===== Pagination Response Schemas =====

class PaginatedResponse(BaseModel):
    """Base paginated response."""
    items: List
    total: int
    limit: int
    offset: int
    has_more: bool


class TaskListResponse(PaginatedResponse):
    """Paginated task list response."""
    items: List[dict]


class RiskListResponse(PaginatedResponse):
    """Paginated risk list response."""
    items: List[dict]


class ProjectListResponse(PaginatedResponse):
    """Paginated project list response."""
    items: List[dict]


class DecisionListResponse(PaginatedResponse):
    """Paginated decision list response."""
    items: List[dict]


# ===== Filter Schemas =====

class TaskFilter(BaseModel):
    """Filter options for tasks."""
    project_id: Optional[str] = None
    status: Optional[List[TaskStatus]] = None
    priority: Optional[List[Priority]] = None
    owner: Optional[str] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    search: Optional[str] = None
    sort_by: Optional[str] = "due_date"
    sort_order: Optional[SortOrder] = SortOrder.ASC
    limit: int = 20
    offset: int = 0


class RiskFilter(BaseModel):
    """Filter options for risks."""
    project_id: Optional[str] = None
    meeting_id: Optional[str] = None
    risk_level: Optional[List[RiskLevel]] = None
    owner: Optional[str] = None
    search: Optional[str] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[SortOrder] = SortOrder.DESC
    limit: int = 20
    offset: int = 0
