"""Worker service for processing uploaded meeting notes.

Features:
- Idempotent message processing (deduplication via message ID)
- Structured logging for observability
- Graceful error handling with proper status updates
"""
import os
import base64
import json
import logging
import time
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify
from google.cloud import storage

from services import gemini, bigquery

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
)
logger = logging.getLogger(__name__)


def log_structured(severity: str, message: str, **kwargs):
    """Log in Cloud Logging structured format."""
    entry = {
        "severity": severity,
        "message": message,
        "service": "worker",
        **kwargs,
    }
    print(json.dumps(entry))


app = Flask(__name__)

PROJECT_ID = os.getenv("PROJECT_ID")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@app.route("/", methods=["POST"])
def pubsub_push_handler():
    """Handle Pub/Sub push messages from Cloud Run.
    
    Implements idempotent processing using Pub/Sub message ID.
    Returns:
        - 204: Success (or already processed)
        - 400: Bad request (won't retry)
        - 500: Server error (will retry)
    """
    request_start = time.time()
    message_id: Optional[str] = None
    meeting_id: Optional[str] = None
    
    try:
        # Parse envelope
        envelope = request.get_json()
        if not envelope or not isinstance(envelope, dict):
            log_structured("WARNING", "Invalid request: no envelope", 
                          request_body=str(request.data)[:200])
            return ("Bad Request: no Pub/Sub message received", 400)

        if "message" not in envelope:
            log_structured("WARNING", "Invalid request: no message field")
            return ("Bad Request: invalid Pub/Sub message format", 400)

        pubsub_message = envelope["message"]
        message_id = pubsub_message.get("messageId") or pubsub_message.get("message_id")
        
        if not message_id:
            log_structured("WARNING", "Missing message ID")
            return ("Bad Request: missing message ID", 400)

        # Check idempotency - skip if already processed
        if bigquery.is_message_processed(message_id):
            log_structured("INFO", "Message already processed (idempotent skip)",
                          message_id=message_id)
            return ("", 204)

        # Decode message data
        if "data" not in pubsub_message:
            log_structured("WARNING", "Missing data field", message_id=message_id)
            return ("Bad Request: missing data field", 400)
        
        message_data_encoded = pubsub_message["data"]
        message_data_json = base64.b64decode(message_data_encoded).decode("utf-8")
        message_data = json.loads(message_data_json)
        
        meeting_id = message_data.get("meeting_id")
        gcs_uri = message_data.get("gcs_uri")
        
        if not meeting_id or not gcs_uri:
            log_structured("WARNING", "Missing required fields",
                          message_id=message_id,
                          has_meeting_id=bool(meeting_id),
                          has_gcs_uri=bool(gcs_uri))
            return ("Bad Request: missing meeting_id or gcs_uri", 400)
        
        log_structured("INFO", "Processing meeting",
                      message_id=message_id,
                      meeting_id=meeting_id,
                      gcs_uri=gcs_uri)
        
        # Process the upload
        process_upload(meeting_id, gcs_uri, message_id)
        
        # Mark message as processed for idempotency
        bigquery.mark_message_processed(message_id, meeting_id)
        
        duration_ms = int((time.time() - request_start) * 1000)
        log_structured("INFO", "Processing completed",
                      message_id=message_id,
                      meeting_id=meeting_id,
                      duration_ms=duration_ms)
        
        return ("", 204)
        
    except json.JSONDecodeError as e:
        log_structured("ERROR", f"JSON decode error: {e}",
                      message_id=message_id)
        return (f"Bad Request: invalid JSON: {e}", 400)
    
    except bigquery.ProcessingError as e:
        # Known processing errors - don't retry
        log_structured("ERROR", f"Processing error (no retry): {e}",
                      message_id=message_id,
                      meeting_id=meeting_id,
                      error_type="ProcessingError")
        if meeting_id:
            bigquery.update_meeting_status(meeting_id, "ERROR", str(e))
        return ("", 204)  # Return 204 to prevent retry
    
    except Exception as e:
        duration_ms = int((time.time() - request_start) * 1000)
        log_structured("ERROR", f"Unexpected error: {e}",
                      message_id=message_id,
                      meeting_id=meeting_id,
                      duration_ms=duration_ms,
                      error_type=type(e).__name__)
        
        if meeting_id:
            try:
                bigquery.update_meeting_status(meeting_id, "ERROR", str(e)[:500])
            except Exception as status_error:
                log_structured("ERROR", f"Failed to update status: {status_error}")
        
        # Return 500 so Pub/Sub will retry
        return (f"Internal Server Error", 500)


def process_upload(meeting_id: str, gcs_uri: str, message_id: str):
    """Process an uploaded meeting file.
    
    Args:
        meeting_id: The meeting record ID
        gcs_uri: GCS URI of the uploaded file
        message_id: Pub/Sub message ID for logging
        
    Raises:
        bigquery.ProcessingError: For recoverable errors
        Exception: For unexpected errors (will trigger retry)
    """
    # 1. Get meeting metadata
    meeting_meta = bigquery.get_meeting_metadata(meeting_id)
    if not meeting_meta:
        raise bigquery.ProcessingError(f"Meeting metadata not found: {meeting_id}")
    
    # Check if already processed (additional idempotency check)
    current_status = meeting_meta.get("status")
    if current_status == "DONE":
        log_structured("INFO", "Meeting already processed",
                      meeting_id=meeting_id, message_id=message_id)
        return
    
    meeting_date = str(meeting_meta.get("meeting_date", "2024-01-01"))
    
    # 2. Update status to PROCESSING
    bigquery.update_meeting_status(meeting_id, "PROCESSING")
    
    # 3. Read file from GCS with size check
    bucket_name = gcs_uri.split("/")[2]
    blob_name = "/".join(gcs_uri.split("/")[3:])
    
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    # Check file size before downloading
    blob.reload()
    if blob.size and blob.size > MAX_FILE_SIZE_BYTES:
        raise bigquery.ProcessingError(
            f"File too large: {blob.size / 1024 / 1024:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)"
        )
    
    text_content = blob.download_as_text()
    
    log_structured("INFO", "File downloaded",
                  meeting_id=meeting_id,
                  file_size_chars=len(text_content),
                  file_size_kb=len(text_content.encode('utf-8')) / 1024)
    
    # 4. Validate content
    if not text_content.strip():
        raise bigquery.ProcessingError("File is empty")
    
    if len(text_content) < 50:
        raise bigquery.ProcessingError("File content too short (min 50 characters)")
    
    # 5. Call Gemini with retry
    extracted_data = gemini.extract_info_with_retry(text_content, meeting_date)
    
    # Log extraction summary
    log_structured("INFO", "Data extracted",
                  meeting_id=meeting_id,
                  projects_count=len(extracted_data.get("projects", [])),
                  tasks_count=len(extracted_data.get("tasks", [])),
                  risks_count=len(extracted_data.get("risks", [])),
                  decisions_count=len(extracted_data.get("decisions", [])))
    
    # 6. Save to BigQuery with partial failure handling
    bigquery.save_extracted_data(meeting_id, extracted_data)
    
    # 7. Update status to DONE
    bigquery.update_meeting_status(meeting_id, "DONE")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "worker",
        "environment": ENVIRONMENT,
    }), 200


@app.route("/ready", methods=["GET"])
def ready():
    """Readiness check - verifies dependencies are available."""
    checks = {
        "bigquery": False,
        "gemini": False,
    }
    
    try:
        # Check BigQuery connectivity
        bigquery.get_client()
        checks["bigquery"] = True
    except Exception as e:
        log_structured("WARNING", f"BigQuery readiness check failed: {e}")
    
    try:
        # Check Gemini availability (light check)
        checks["gemini"] = gemini.is_available()
    except Exception as e:
        log_structured("WARNING", f"Gemini readiness check failed: {e}")
    
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return jsonify({
        "ready": all_ready,
        "checks": checks,
    }), status_code


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    log_structured("INFO", f"Starting worker service on port {port}",
                  environment=ENVIRONMENT)
    app.run(host="0.0.0.0", port=port, debug=False)
