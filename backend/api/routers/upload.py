import os
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from google.cloud import pubsub_v1
from services import storage, bigquery
from auth.middleware import get_current_user
from routers.audit import log_user_action

router = APIRouter(prefix="/upload", tags=["upload"])

PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_ID = os.getenv("PUBSUB_TOPIC")
USE_LOCAL_MODE = os.getenv("USE_LOCAL_DB", "false").lower() == "true"

@router.post("/")
async def upload_meeting_notes(
    request: Request,
    file: UploadFile = File(...),
    meeting_date: str = Form(...), # YYYY-MM-DD
    title: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        content = await file.read()
        meeting_id = str(uuid.uuid4())
        filename = f"{meeting_id}/{file.filename}"

        # Upload to GCS
        gcs_uri = storage.upload_file(content, filename, file.content_type)

        # Log audit
        log_user_action(
            request=request,
            action="UPLOAD_MEETING",
            current_user=current_user,
            resource_type="meeting",
            resource_id=meeting_id,
            details=f"Uploaded file: {file.filename}, date: {meeting_date}"
        )
        
        # Insert metadata to BigQuery
        meeting_data = {
            "meeting_id": meeting_id,
            "tenant_id": "default", # MVP
            "meeting_date": meeting_date,
            "title": title or file.filename,
            "source_file_uri": gcs_uri,
            "language": "ja", # Default to Japanese for MVP or detect later
            "created_at": datetime.utcnow().isoformat(),
            "status": "PENDING"
        }
        bigquery.insert_meeting_metadata(meeting_data)
        
        # In local mode, skip Pub/Sub and return success immediately
        # In production mode, publish to Pub/Sub for async processing
        if USE_LOCAL_MODE:
            # In local mode, process the file immediately with AI
            try:
                # Read the uploaded file content
                file_content_text = content.decode('utf-8')
                
                # Process with AI
                from ..services import ai_processor, local_db
                
                print(f"Starting AI processing for meeting {meeting_id}...")
                extracted_data = ai_processor.process_meeting_notes(
                    meeting_id=meeting_id,
                    text_content=file_content_text,
                    meeting_date=meeting_date
                )
                
                # Save extracted data
                local_db.save_extracted_data(meeting_id, extracted_data)
                
                # Update status to DONE
                local_db.update_meeting_status(meeting_id, "DONE")
                
                return {
                    "meeting_id": meeting_id,
                    "status": "DONE",
                    "message": "File uploaded and processed successfully",
                    "extracted": {
                        "projects": len(extracted_data.get("projects", [])),
                        "tasks": len(extracted_data.get("tasks", [])),
                        "risks": len(extracted_data.get("risks", [])),
                        "decisions": len(extracted_data.get("decisions", []))
                    }
                }
            except Exception as ai_error:
                # If AI processing fails, update status but don't fail the upload
                print(f"AI processing failed: {ai_error}")
                local_db.update_meeting_status(meeting_id, "ERROR", str(ai_error))
                return {
                    "meeting_id": meeting_id,
                    "status": "ERROR",
                    "message": f"File uploaded but AI processing failed: {str(ai_error)}"
                }
        else:
            # Publish to Pub/Sub for async processing
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
            message_json = json.dumps({"meeting_id": meeting_id, "gcs_uri": gcs_uri})
            future = publisher.publish(topic_path, message_json.encode("utf-8"))
            message_id = future.result()
            
            return {"meeting_id": meeting_id, "status": "PENDING", "message_id": message_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
