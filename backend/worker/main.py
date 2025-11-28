"""Worker service for processing uploaded meeting notes."""
import os
import base64
import json
from flask import Flask, request, jsonify
from google.cloud import storage
from services import gemini, bigquery

app = Flask(__name__)

PROJECT_ID = os.getenv("PROJECT_ID")


@app.route("/", methods=["POST"])
def pubsub_push_handler():
    """Handle Pub/Sub push messages from Cloud Run."""
    try:
        # Validate request is from Pub/Sub
        envelope = request.get_json()
        if not envelope:
            return ("Bad Request: no Pub/Sub message received", 400)

        if not isinstance(envelope, dict) or "message" not in envelope:
            return ("Bad Request: invalid Pub/Sub message format", 400)

        # Extract and decode message data
        pubsub_message = envelope["message"]
        
        if "data" not in pubsub_message:
            return ("Bad Request: missing data field", 400)
        
        message_data_encoded = pubsub_message["data"]
        message_data_json = base64.b64decode(message_data_encoded).decode("utf-8")
        message_data = json.loads(message_data_json)
        
        meeting_id = message_data.get("meeting_id")
        gcs_uri = message_data.get("gcs_uri")
        
        if not meeting_id or not gcs_uri:
            return ("Bad Request: missing meeting_id or gcs_uri", 400)
        
        print(f"Processing meeting_id: {meeting_id}, gcs_uri: {gcs_uri}")
        
        # Process the upload
        process_upload(meeting_id, gcs_uri)
        
        return ("", 204)  # Success, no content
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return (f"Bad Request: invalid JSON: {e}", 400)
    except Exception as e:
        print(f"Error processing message: {e}")
        # Return 500 so Pub/Sub will retry
        return (f"Internal Server Error: {e}", 500)


def process_upload(meeting_id: str, gcs_uri: str):
    """Process an uploaded meeting file."""
    try:
        # 1. Get meeting metadata (date)
        meeting_meta = bigquery.get_meeting_metadata(meeting_id)
        if not meeting_meta:
            print(f"Meeting metadata not found for {meeting_id}")
            bigquery.update_meeting_status(meeting_id, "ERROR", "Meeting metadata not found")
            return
        
        meeting_date = str(meeting_meta.get("meeting_date", "2024-01-01"))  # Default if missing
        
        # 2. Read file from GCS
        # gcs_uri is like gs://bucket/path
        bucket_name = gcs_uri.split("/")[2]
        blob_name = "/".join(gcs_uri.split("/")[3:])
        
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        text_content = blob.download_as_text()
        
        print(f"Downloaded file: {len(text_content)} characters")
        
        # 3. Call Gemini
        extracted_data = gemini.extract_info(text_content, meeting_date)
        print(f"Extracted data: {json.dumps(extracted_data, default=str)[:500]}...")
        
        # 4. Save to BigQuery
        bigquery.save_extracted_data(meeting_id, extracted_data)
        
        # 5. Update status
        bigquery.update_meeting_status(meeting_id, "DONE")
        print(f"Successfully processed meeting {meeting_id}")
        
    except Exception as e:
        print(f"Error processing upload: {e}")
        bigquery.update_meeting_status(meeting_id, "ERROR", str(e))
        raise e


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "worker"}), 200


if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

