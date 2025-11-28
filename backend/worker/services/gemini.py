import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", "asia-northeast1")

vertexai.init(project=PROJECT_ID, location=LOCATION)

def extract_info(text: str, meeting_date: str) -> dict:
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
