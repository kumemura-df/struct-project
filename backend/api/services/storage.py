import os
from google.cloud import storage

PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET")
USE_LOCAL_STORAGE = os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"

# Import local_storage if in local mode
if USE_LOCAL_STORAGE:
    from . import local_storage

def upload_file(file_content: bytes, destination_blob_name: str, content_type: str = "text/plain") -> str:
    """Uploads a file to the bucket or local storage."""
    if USE_LOCAL_STORAGE:
        return local_storage.upload_file(file_content, destination_blob_name, content_type)
    
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(file_content, content_type=content_type)

    return f"gs://{BUCKET_NAME}/{destination_blob_name}"
