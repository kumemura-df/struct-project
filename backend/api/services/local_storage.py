"""Local file storage for development mode."""
import os
from pathlib import Path

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")

def upload_file(file_content: bytes, destination_blob_name: str, content_type: str = "text/plain") -> str:
    """Save file to local filesystem."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Create full path
    file_path = os.path.join(UPLOAD_DIR, destination_blob_name)
    
    # Create parent directories if needed
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Return file:// URI instead of gs://
    return f"file://{os.path.abspath(file_path)}"
