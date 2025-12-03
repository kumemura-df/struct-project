"""AI-powered meeting notes processor using Vertex AI Gemini."""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import dateparser
from dateutil import parser as dateutil_parser

# Check if Vertex AI is available
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    print("Warning: Vertex AI not available. AI processing will be disabled.")

PROJECT_ID = os.getenv("PROJECT_ID", "local-dev")
REGION = os.getenv("REGION", "asia-northeast1")

# Initialize Vertex AI if available
if VERTEX_AI_AVAILABLE and PROJECT_ID != "local-dev":
    try:
        vertexai.init(project=PROJECT_ID, location=REGION)
    except Exception as e:
        print(f"Warning: Failed to initialize Vertex AI: {e}")
        VERTEX_AI_AVAILABLE = False


def parse_date_with_meeting_context(
    date_text: str,
    meeting_date: str
) -> Optional[str]:
    """
    Parse a natural language date string to absolute date.
    
    Args:
        date_text: Natural language date (e.g., "next Friday", "12月2日")
        meeting_date: Reference date in ISO format "YYYY-MM-DD"
    
    Returns:
        ISO format date string "YYYY-MM-DD" or None
    """
    if not date_text:
        return None
    
    # Parse reference date
    ref_dt = None
    if meeting_date:
        try:
            ref_dt = datetime.fromisoformat(meeting_date)
        except (ValueError, TypeError):
            ref_dt = None
    
    # Try dateparser (handles natural language)
    settings = {
        'PREFER_DATES_FROM': 'future',
        'RETURN_AS_TIMEZONE_AWARE': False,
    }
    
    if ref_dt:
        settings['RELATIVE_BASE'] = ref_dt
    
    parsed = dateparser.parse(date_text, settings=settings)
    
    # Fallback to dateutil for strict ISO dates
    if not parsed:
        try:
            parsed = dateutil_parser.parse(date_text)
        except (ValueError, TypeError):
            return None
    
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    
    return None


def extract_info(text: str, meeting_date: str) -> Dict[str, Any]:
    """
    Extract structured information from meeting notes using Gemini.
    
    Args:
        text: Meeting notes text
        meeting_date: Meeting date in ISO format "YYYY-MM-DD"
    
    Returns:
        Dictionary with projects, tasks, risks, and decisions
    """
    if not VERTEX_AI_AVAILABLE:
        raise Exception("Vertex AI is not available. Please install google-cloud-aiplatform and configure credentials.")
    
    model = GenerativeModel("gemini-1.5-flash-001")
    
    schema = {
        "type": "object",
        "properties": {
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"}
                    },
                    "required": ["project_name"]
                }
            },
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "task_title": {"type": "string"},
                        "task_description": {"type": "string"},
                        "owner": {"type": "string"},
                        "due_date_text": {"type": "string"},
                        "status": {"type": "string", "enum": ["NOT_STARTED", "IN_PROGRESS", "DONE", "UNKNOWN"]},
                        "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                        "source_sentence": {"type": "string"}
                    },
                    "required": ["project_name", "task_title", "owner"]
                }
            },
            "risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "risk_description": {"type": "string"},
                        "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                        "owner": {"type": "string"},
                        "source_sentence": {"type": "string"}
                    },
                    "required": ["risk_description", "source_sentence"]
                }
            },
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "decision_content": {"type": "string"},
                        "source_sentence": {"type": "string"}
                    },
                    "required": ["decision_content", "source_sentence"]
                }
            }
        },
        "required": ["projects", "tasks", "risks", "decisions"]
    }

    prompt = f"""
    You are a highly skilled Project Management Assistant.
    Your goal is to structure the following meeting notes into a database-ready format.
    
    Meeting Date: {meeting_date}
    
    Instructions:
    1. **Projects**: Identify which projects are being discussed.
    2. **Tasks**: Extract actionable items. Infer status and priority if not explicit.
    3. **Risks**: Extract explicit risks AND "risk-like" utterances (e.g., "I'm worried about...", "It might be tight...", "We are not sure if...").
       - For "risk-like" utterances, set the `source_sentence` to the exact quote.
       - Assign a Risk Level (LOW, MEDIUM, HIGH) based on the context.
    4. **Decisions**: Extract agreed-upon decisions or conclusions.
    
    Meeting Notes:
    {text}
    
    Output must be valid JSON following the schema.
    """

    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": schema
    }

    response = model.generate_content(
        prompt,
        generation_config=generation_config,
    )

    return json.loads(response.text)


def process_meeting_notes(
    meeting_id: str,
    text_content: str,
    meeting_date: str
) -> Dict[str, Any]:
    """
    Process meeting notes: extract info and return structured data.

    Args:
        meeting_id: Meeting ID
        text_content: Full text content of meeting notes
        meeting_date: Meeting date in ISO format "YYYY-MM-DD"

    Returns:
        Extracted data dictionary
    """
    print(f"Processing meeting {meeting_id} with Gemini...")

    # Extract info using Gemini
    extracted_data = extract_info(text_content, meeting_date)

    print(f"Extracted: {len(extracted_data.get('projects', []))} projects, "
          f"{len(extracted_data.get('tasks', []))} tasks, "
          f"{len(extracted_data.get('risks', []))} risks, "
          f"{len(extracted_data.get('decisions', []))} decisions")

    return extracted_data


def generate_meeting_agenda(
    project_name: str,
    tasks: list,
    risks: list,
    decisions: list,
    recent_meetings: list
) -> Dict[str, Any]:
    """
    Generate suggested agenda for the next meeting using AI.

    Args:
        project_name: Name of the project
        tasks: List of tasks (including overdue, in-progress)
        risks: List of active risks
        decisions: List of recent decisions
        recent_meetings: List of recent meeting titles and dates

    Returns:
        Dictionary with agenda items and suggestions
    """
    if not VERTEX_AI_AVAILABLE:
        return _generate_agenda_fallback(project_name, tasks, risks, decisions)

    model = GenerativeModel("gemini-1.5-flash-001")

    # Prepare context
    overdue_tasks = [t for t in tasks if t.get("due_date") and t["due_date"] < datetime.now().strftime("%Y-%m-%d") and t.get("status") != "DONE"]
    in_progress_tasks = [t for t in tasks if t.get("status") == "IN_PROGRESS"]
    high_risks = [r for r in risks if r.get("risk_level") == "HIGH"]

    context = f"""
Project: {project_name}

Overdue Tasks ({len(overdue_tasks)}):
{_format_tasks_for_prompt(overdue_tasks)}

In-Progress Tasks ({len(in_progress_tasks)}):
{_format_tasks_for_prompt(in_progress_tasks)}

High Risks ({len(high_risks)}):
{_format_risks_for_prompt(high_risks)}

Recent Decisions ({len(decisions)}):
{_format_decisions_for_prompt(decisions[:5])}

Recent Meetings:
{_format_meetings_for_prompt(recent_meetings[:3])}
"""

    schema = {
        "type": "object",
        "properties": {
            "agenda_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                        "estimated_minutes": {"type": "integer"},
                        "related_tasks": {"type": "array", "items": {"type": "string"}},
                        "related_risks": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["title", "description", "priority", "estimated_minutes"]
                }
            },
            "suggested_duration_minutes": {"type": "integer"},
            "key_discussion_points": {"type": "array", "items": {"type": "string"}},
            "recommended_attendees": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["agenda_items", "suggested_duration_minutes", "key_discussion_points"]
    }

    prompt = f"""
You are a Project Management Assistant helping to plan the next meeting.

Based on the project context below, generate a suggested meeting agenda that:
1. Prioritizes overdue tasks and high risks
2. Reviews in-progress work status
3. Follows up on recent decisions
4. Keeps the meeting focused and time-efficient

{context}

Generate a practical, actionable meeting agenda with estimated time for each item.
Focus on items that need discussion or decisions, not just status updates.
"""

    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": schema
    }

    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
        result = json.loads(response.text)
        result["generated_at"] = datetime.now().isoformat()
        result["project_name"] = project_name
        return result
    except Exception as e:
        print(f"AI agenda generation failed: {e}")
        return _generate_agenda_fallback(project_name, tasks, risks, decisions)


def _generate_agenda_fallback(
    project_name: str,
    tasks: list,
    risks: list,
    decisions: list
) -> Dict[str, Any]:
    """Generate a basic agenda without AI."""
    agenda_items = []

    # Overdue tasks review
    overdue = [t for t in tasks if t.get("due_date") and t["due_date"] < datetime.now().strftime("%Y-%m-%d") and t.get("status") != "DONE"]
    if overdue:
        agenda_items.append({
            "title": "Overdue Tasks Review",
            "description": f"Review {len(overdue)} overdue task(s) and discuss blockers",
            "priority": "HIGH",
            "estimated_minutes": min(len(overdue) * 5, 20),
            "related_tasks": [t.get("task_title", "") for t in overdue[:5]]
        })

    # High risks
    high_risks = [r for r in risks if r.get("risk_level") == "HIGH"]
    if high_risks:
        agenda_items.append({
            "title": "High Risk Discussion",
            "description": f"Address {len(high_risks)} high-level risk(s)",
            "priority": "HIGH",
            "estimated_minutes": min(len(high_risks) * 5, 15),
            "related_risks": [r.get("risk_description", "")[:50] for r in high_risks[:3]]
        })

    # In-progress tasks
    in_progress = [t for t in tasks if t.get("status") == "IN_PROGRESS"]
    if in_progress:
        agenda_items.append({
            "title": "Progress Update",
            "description": f"Status update on {len(in_progress)} in-progress task(s)",
            "priority": "MEDIUM",
            "estimated_minutes": min(len(in_progress) * 3, 15),
            "related_tasks": [t.get("task_title", "") for t in in_progress[:5]]
        })

    # Next steps
    agenda_items.append({
        "title": "Next Steps & Action Items",
        "description": "Define action items and assignments for the coming week",
        "priority": "MEDIUM",
        "estimated_minutes": 10
    })

    total_minutes = sum(item.get("estimated_minutes", 10) for item in agenda_items)

    return {
        "agenda_items": agenda_items,
        "suggested_duration_minutes": total_minutes,
        "key_discussion_points": [
            f"{len(overdue)} overdue tasks need attention" if overdue else None,
            f"{len(high_risks)} high risks require discussion" if high_risks else None,
        ],
        "generated_at": datetime.now().isoformat(),
        "project_name": project_name,
        "ai_generated": False
    }


def _format_tasks_for_prompt(tasks: list) -> str:
    if not tasks:
        return "None"
    return "\n".join([
        f"- {t.get('task_title', 'Untitled')} (Owner: {t.get('owner', 'Unknown')}, Due: {t.get('due_date', 'N/A')})"
        for t in tasks[:10]
    ])


def _format_risks_for_prompt(risks: list) -> str:
    if not risks:
        return "None"
    return "\n".join([
        f"- [{r.get('risk_level', 'UNKNOWN')}] {r.get('risk_description', 'No description')[:100]}"
        for r in risks[:5]
    ])


def _format_decisions_for_prompt(decisions: list) -> str:
    if not decisions:
        return "None"
    return "\n".join([
        f"- {d.get('decision_content', d.get('decision_description', 'No content'))[:100]}"
        for d in decisions[:5]
    ])


def _format_meetings_for_prompt(meetings: list) -> str:
    if not meetings:
        return "None"
    return "\n".join([
        f"- {m.get('title', 'Untitled')} ({m.get('meeting_date', 'Unknown date')})"
        for m in meetings[:3]
    ])
