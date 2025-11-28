"""Export service for generating CSV files."""
import csv
import io
from typing import List, Dict, Any
from datetime import datetime


def generate_csv(data: List[Dict[str, Any]], headers: List[str]) -> str:
    """Generate CSV content from data."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
    
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()


def generate_projects_csv(projects: List[Dict[str, Any]]) -> str:
    """Generate CSV export for projects."""
    headers = [
        'project_id',
        'project_name',
        'tenant_id',
        'latest_meeting_id',
        'created_at',
        'updated_at'
    ]
    return generate_csv(projects, headers)


def generate_tasks_csv(tasks: List[Dict[str, Any]]) -> str:
    """Generate CSV export for tasks."""
    headers = [
        'task_id',
        'meeting_id',
        'project_id',
        'task_title',
        'task_description',
        'owner',
        'owner_email',
        'due_date',
        'status',
        'priority',
        'created_at',
        'updated_at',
        'source_sentence'
    ]
    return generate_csv(tasks, headers)


def generate_risks_csv(risks: List[Dict[str, Any]]) -> str:
    """Generate CSV export for risks."""
    headers = [
        'risk_id',
        'meeting_id',
        'project_id',
        'risk_description',
        'risk_level',
        'likelihood',
        'impact',
        'owner',
        'created_at',
        'source_sentence'
    ]
    return generate_csv(risks, headers)


def generate_decisions_csv(decisions: List[Dict[str, Any]]) -> str:
    """Generate CSV export for decisions."""
    headers = [
        'decision_id',
        'meeting_id',
        'project_id',
        'decision_content',
        'created_at',
        'source_sentence'
    ]
    return generate_csv(decisions, headers)


def get_export_filename(entity_type: str) -> str:
    """Generate filename for export with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"project_progress_{entity_type}_{timestamp}.csv"
