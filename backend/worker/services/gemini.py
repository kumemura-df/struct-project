"""Gemini AI service for meeting notes extraction.

Features:
- Exponential backoff retry for transient failures
- Timeout handling
- Structured response validation
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, DeadlineExceeded

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", "asia-northeast1")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-001")

# Retry configuration
MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
INITIAL_BACKOFF_SECONDS = float(os.getenv("GEMINI_INITIAL_BACKOFF", "1.0"))
MAX_BACKOFF_SECONDS = float(os.getenv("GEMINI_MAX_BACKOFF", "30.0"))
TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT", "120"))

# Initialize Vertex AI
_initialized = False


def _ensure_initialized():
    """Initialize Vertex AI if not already done."""
    global _initialized
    if not _initialized:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        _initialized = True


def is_available() -> bool:
    """Check if Gemini service is available."""
    try:
        _ensure_initialized()
        # Just check if we can create the model instance
        GenerativeModel(MODEL_NAME)
        return True
    except Exception:
        return False


# JSON Schema for structured output
EXTRACTION_SCHEMA = {
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
                    "status": {
                        "type": "string",
                        "enum": ["NOT_STARTED", "IN_PROGRESS", "DONE", "UNKNOWN"]
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH"]
                    },
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
                    "risk_level": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH"]
                    },
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


def _build_prompt(text: str, meeting_date: str) -> str:
    """Build the extraction prompt."""
    return f"""You are a highly skilled Project Management Assistant.
Your goal is to structure the following meeting notes into a database-ready format.

Meeting Date: {meeting_date}

Instructions:
1. **Projects**: Identify which projects are being discussed. Look for project names, code names, or initiatives.

2. **Tasks**: Extract actionable items with the following details:
   - task_title: Clear, concise title
   - task_description: Additional context if available
   - owner: Person responsible (use "Unassigned" if unclear)
   - due_date_text: Deadline as mentioned (e.g., "next Friday", "end of month")
   - status: NOT_STARTED (default), IN_PROGRESS, DONE, or UNKNOWN
   - priority: LOW, MEDIUM (default), or HIGH
   - source_sentence: The original text that mentions this task

3. **Risks**: Extract both explicit risks AND "risk-like" utterances:
   - Explicit: "Risk: X might happen"
   - Implicit: "I'm worried about...", "It might be tight...", "We are not sure if..."
   - Set source_sentence to the exact quote
   - Assign risk_level based on context and language intensity

4. **Decisions**: Extract agreed-upon decisions or conclusions that were made during the meeting.

Meeting Notes:
{text}

Output must be valid JSON following the provided schema. If no items are found for a category, return an empty array."""


def extract_info(text: str, meeting_date: str) -> Dict[str, Any]:
    """Extract structured information from meeting notes.
    
    Args:
        text: Meeting notes text content
        meeting_date: Date of the meeting (YYYY-MM-DD format)
        
    Returns:
        Dict with projects, tasks, risks, and decisions
        
    Raises:
        Exception: On Gemini API errors
    """
    _ensure_initialized()
    
    model = GenerativeModel(MODEL_NAME)
    prompt = _build_prompt(text, meeting_date)
    
    generation_config = GenerationConfig(
        response_mime_type="application/json",
        response_schema=EXTRACTION_SCHEMA,
        temperature=0.1,  # Low temperature for consistent extraction
        max_output_tokens=8192,
    )
    
    response = model.generate_content(
        prompt,
        generation_config=generation_config,
    )
    
    result = json.loads(response.text)
    
    # Validate and sanitize output
    return _validate_and_sanitize(result)


def extract_info_with_retry(text: str, meeting_date: str) -> Dict[str, Any]:
    """Extract info with exponential backoff retry.
    
    Args:
        text: Meeting notes text content
        meeting_date: Date of the meeting
        
    Returns:
        Extracted data dictionary
        
    Raises:
        Exception: After all retries exhausted
    """
    last_exception: Optional[Exception] = None
    backoff = INITIAL_BACKOFF_SECONDS
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            return extract_info(text, meeting_date)
            
        except (ResourceExhausted, ServiceUnavailable, DeadlineExceeded) as e:
            last_exception = e
            
            if attempt < MAX_RETRIES:
                # Log retry attempt
                logger.warning(
                    f"Gemini API error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {backoff:.1f}s..."
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
            else:
                logger.error(f"Gemini API error after {MAX_RETRIES + 1} attempts: {e}")
                
        except json.JSONDecodeError as e:
            # JSON parsing error - might be a model issue, retry with backoff
            last_exception = e
            
            if attempt < MAX_RETRIES:
                logger.warning(
                    f"JSON decode error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {backoff:.1f}s..."
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
            else:
                logger.error(f"JSON decode error after {MAX_RETRIES + 1} attempts: {e}")
                
        except Exception as e:
            # Unexpected errors - don't retry
            logger.error(f"Unexpected Gemini error: {e}")
            raise
    
    # All retries exhausted
    raise last_exception or Exception("Gemini extraction failed after retries")


def _validate_and_sanitize(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize extracted data.
    
    Ensures all required fields exist and have valid values.
    """
    # Ensure all top-level arrays exist
    result = {
        "projects": data.get("projects", []),
        "tasks": data.get("tasks", []),
        "risks": data.get("risks", []),
        "decisions": data.get("decisions", []),
    }
    
    # Sanitize tasks
    for task in result["tasks"]:
        # Ensure required fields
        task["task_title"] = task.get("task_title", "Untitled Task")
        task["owner"] = task.get("owner", "Unassigned")
        task["status"] = task.get("status", "UNKNOWN")
        task["priority"] = task.get("priority", "MEDIUM")
        
        # Validate enum values
        if task["status"] not in ["NOT_STARTED", "IN_PROGRESS", "DONE", "UNKNOWN"]:
            task["status"] = "UNKNOWN"
        if task["priority"] not in ["LOW", "MEDIUM", "HIGH"]:
            task["priority"] = "MEDIUM"
    
    # Sanitize risks
    for risk in result["risks"]:
        risk["risk_description"] = risk.get("risk_description", "")
        risk["risk_level"] = risk.get("risk_level", "MEDIUM")
        risk["source_sentence"] = risk.get("source_sentence", "")
        
        if risk["risk_level"] not in ["LOW", "MEDIUM", "HIGH"]:
            risk["risk_level"] = "MEDIUM"
    
    # Sanitize decisions
    for decision in result["decisions"]:
        decision["decision_content"] = decision.get("decision_content", "")
        decision["source_sentence"] = decision.get("source_sentence", "")
    
    return result
