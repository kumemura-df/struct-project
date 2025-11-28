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
