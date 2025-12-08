import os
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from google.cloud import pubsub_v1
from services import storage, bigquery
from services.transcript_parser import parse_transcript, get_supported_formats, TranscriptFormat
from services.speech_to_text import (
    transcribe_audio, 
    transcribe_audio_gcs,
    is_audio_file, 
    get_audio_mime_type,
    get_supported_audio_formats,
    SUPPORTED_AUDIO_FORMATS
)
from auth.middleware import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/upload", tags=["upload"])

# Supported file extensions for transcript uploads
SUPPORTED_EXTENSIONS = {'.txt', '.md', '.vtt', '.srt'}

# Supported audio extensions
SUPPORTED_AUDIO_EXTENSIONS = set(SUPPORTED_AUDIO_FORMATS.keys())

# All supported extensions
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS

# Maximum file size for direct transcription (10MB)
MAX_AUDIO_SIZE_DIRECT = 10 * 1024 * 1024  # 10MB

# Get limiter from app state (will be set in main.py)
def get_limiter(request: Request) -> Limiter:
    return request.app.state.limiter

PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_ID = os.getenv("PUBSUB_TOPIC")
USE_LOCAL_MODE = os.getenv("USE_LOCAL_DB", "false").lower() == "true"

@router.get("/formats")
async def get_upload_formats():
    """Get list of supported file formats (transcript and audio)."""
    return {
        "transcript_formats": get_supported_formats(),
        "audio_formats": get_supported_audio_formats(),
        "supported_extensions": {
            "transcript": list(SUPPORTED_EXTENSIONS),
            "audio": list(SUPPORTED_AUDIO_EXTENSIONS),
            "all": list(ALL_SUPPORTED_EXTENSIONS)
        }
    }


@router.post("/")
async def upload_meeting_notes(
    request: Request,
    file: UploadFile = File(...),
    meeting_date: str = Form(...), # YYYY-MM-DD
    title: str = Form(None),
    source_type: str = Form("auto"),  # auto, otter, tldv, zoom, vtt, srt, plain
    current_user: dict = Depends(get_current_user)
):
    """
    Upload meeting notes file with automatic format detection.
    
    Supported formats:
    - .txt, .md: Plain text or Otter.ai/tl;dv/Zoom exports
    - .vtt: WebVTT (Zoom, YouTube, Google Meet)
    - .srt: SubRip subtitle format
    
    Rate limited to 10 requests per minute.
    """
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        if file_ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        content = await file.read()
        meeting_id = str(uuid.uuid4())
        filename = f"{meeting_id}/{file.filename}"
        
        # Decode content for parsing
        try:
            content_text = content.decode('utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            try:
                content_text = content.decode('shift-jis')
            except UnicodeDecodeError:
                content_text = content.decode('utf-8', errors='ignore')
        
        # Parse transcript to extract clean text
        parsed = parse_transcript(content_text, file.filename or "")
        processed_text = parsed.raw_text
        
        # Upload original file to GCS
        gcs_uri = storage.upload_file(content, filename, file.content_type)
        
        # Insert metadata to BigQuery with transcript info
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
        
        # Log transcript parsing info
        print(f"Parsed transcript: format={parsed.format.value}, segments={len(parsed.segments)}")
        if parsed.metadata.get("speakers"):
            print(f"Detected speakers: {parsed.metadata['speakers']}")
        
        # In local mode, skip Pub/Sub and return success immediately
        # In production mode, publish to Pub/Sub for async processing
        if USE_LOCAL_MODE:
            # In local mode, process the file immediately with AI
            try:
                # Use parsed transcript text (cleaner than raw file content)
                # This ensures VTT/SRT timestamps are stripped and text is properly formatted
                
                # Process with AI
                from ..services import ai_processor, local_db
                
                print(f"Starting AI processing for meeting {meeting_id} (format: {parsed.format.value})...")
                extracted_data = ai_processor.process_meeting_notes(
                    meeting_id=meeting_id,
                    text_content=processed_text,  # Use parsed text instead of raw content
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
                    "transcript_format": parsed.format.value,
                    "transcript_segments": len(parsed.segments),
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
                    "message": f"File uploaded but AI processing failed: {str(ai_error)}",
                    "transcript_format": parsed.format.value
                }
        else:
            # Publish to Pub/Sub for async processing
            # Include parsed text in the message for worker to use
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
            message_json = json.dumps({
                "meeting_id": meeting_id, 
                "gcs_uri": gcs_uri,
                "transcript_format": parsed.format.value,
                "processed_text": processed_text  # Include parsed text
            })
            future = publisher.publish(topic_path, message_json.encode("utf-8"))
            message_id = future.result()
            
            return {
                "meeting_id": meeting_id, 
                "status": "PENDING", 
                "message_id": message_id,
                "transcript_format": parsed.format.value,
                "transcript_segments": len(parsed.segments)
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text")
async def upload_meeting_text(
    request: Request,
    text: str = Form(...),
    meeting_date: str = Form(...),  # YYYY-MM-DD
    title: str = Form(None),
    source_type: str = Form("auto"),  # auto, otter, tldv, zoom, plain
    current_user: dict = Depends(get_current_user)
):
    """
    Upload meeting notes as direct text input.
    
    Supports pasted transcript formats from:
    - Otter.ai
    - tl;dv
    - Zoom transcript
    - Plain text
    
    Rate limited to 10 requests per minute.
    """
    try:
        meeting_id = str(uuid.uuid4())
        
        # Parse the pasted text to extract clean content
        parsed = parse_transcript(text, "")
        processed_text = parsed.raw_text
        
        content = text.encode('utf-8')
        filename = f"{meeting_id}/meeting_notes.txt"
        
        # Upload original text content to GCS as a file
        gcs_uri = storage.upload_file(content, filename, "text/plain")
        
        # Insert metadata to BigQuery
        meeting_data = {
            "meeting_id": meeting_id,
            "tenant_id": "default",  # MVP
            "meeting_date": meeting_date,
            "title": title or "会議メモ",
            "source_file_uri": gcs_uri,
            "language": "ja",  # Default to Japanese for MVP
            "created_at": datetime.utcnow().isoformat(),
            "status": "PENDING"
        }
        bigquery.insert_meeting_metadata(meeting_data)
        
        # Log transcript parsing info
        print(f"Parsed text: format={parsed.format.value}, segments={len(parsed.segments)}")
        
        # In local mode, skip Pub/Sub and process immediately
        # In production mode, publish to Pub/Sub for async processing
        if USE_LOCAL_MODE:
            try:
                # Process with AI using parsed text
                from ..services import ai_processor, local_db
                
                print(f"Starting AI processing for meeting {meeting_id} (format: {parsed.format.value})...")
                extracted_data = ai_processor.process_meeting_notes(
                    meeting_id=meeting_id,
                    text_content=processed_text,  # Use parsed text
                    meeting_date=meeting_date
                )
                
                # Save extracted data
                local_db.save_extracted_data(meeting_id, extracted_data)
                
                # Update status to DONE
                local_db.update_meeting_status(meeting_id, "DONE")
                
                return {
                    "meeting_id": meeting_id,
                    "status": "DONE",
                    "message": "Text uploaded and processed successfully",
                    "transcript_format": parsed.format.value,
                    "transcript_segments": len(parsed.segments),
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
                    "message": f"Text uploaded but AI processing failed: {str(ai_error)}",
                    "transcript_format": parsed.format.value
                }
        else:
            # Publish to Pub/Sub for async processing
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
            message_json = json.dumps({
                "meeting_id": meeting_id, 
                "gcs_uri": gcs_uri,
                "transcript_format": parsed.format.value,
                "processed_text": processed_text
            })
            future = publisher.publish(topic_path, message_json.encode("utf-8"))
            message_id = future.result()
            
            return {
                "meeting_id": meeting_id, 
                "status": "PENDING", 
                "message_id": message_id,
                "transcript_format": parsed.format.value,
                "transcript_segments": len(parsed.segments)
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio")
async def upload_audio_file(
    request: Request,
    file: UploadFile = File(...),
    meeting_date: str = Form(...),  # YYYY-MM-DD
    title: str = Form(None),
    language: str = Form("ja-JP"),  # BCP-47 language code
    enable_diarization: bool = Form(True),  # Speaker identification
    min_speakers: int = Form(2),
    max_speakers: int = Form(6),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload audio file for transcription and AI processing.
    
    Supported formats:
    - .mp3, .m4a: Common audio formats
    - .wav, .flac: High quality audio
    - .webm, .ogg, .opus: Web audio formats
    
    Process:
    1. Upload audio to GCS
    2. Transcribe using Google Cloud Speech-to-Text
    3. Process transcript with Gemini AI to extract projects/tasks/risks
    
    Rate limited to 5 requests per minute (audio processing is expensive).
    """
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        if file_ext not in SUPPORTED_AUDIO_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported audio format. Supported: {', '.join(SUPPORTED_AUDIO_EXTENSIONS)}"
            )
        
        content = await file.read()
        file_size = len(content)
        meeting_id = str(uuid.uuid4())
        filename = f"{meeting_id}/{file.filename}"
        
        print(f"Processing audio file: {file.filename} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Upload audio to GCS first
        mime_type = get_audio_mime_type(file.filename or "") or "audio/mpeg"
        gcs_uri = storage.upload_file(content, filename, mime_type)
        
        # Insert metadata to BigQuery
        meeting_data = {
            "meeting_id": meeting_id,
            "tenant_id": "default",
            "meeting_date": meeting_date,
            "title": title or file.filename,
            "source_file_uri": gcs_uri,
            "language": language.split("-")[0],  # Extract language code (ja from ja-JP)
            "created_at": datetime.utcnow().isoformat(),
            "status": "TRANSCRIBING"  # New status for audio processing
        }
        bigquery.insert_meeting_metadata(meeting_data)
        
        # Transcribe audio
        print(f"Starting transcription for meeting {meeting_id}...")
        
        try:
            if file_size <= MAX_AUDIO_SIZE_DIRECT:
                # Direct transcription for smaller files
                transcription = transcribe_audio(
                    audio_content=content,
                    filename=file.filename or "",
                    language_code=language,
                    enable_diarization=enable_diarization,
                    min_speakers=min_speakers,
                    max_speakers=max_speakers
                )
            else:
                # Use GCS-based batch transcription for larger files
                transcription = transcribe_audio_gcs(
                    gcs_uri=gcs_uri,
                    language_code=language,
                    enable_diarization=enable_diarization,
                    min_speakers=min_speakers,
                    max_speakers=max_speakers
                )
            
            print(f"Transcription complete: {len(transcription.segments)} segments, "
                  f"{len(transcription.speakers)} speakers, "
                  f"{transcription.duration_seconds:.1f}s duration")
            
        except Exception as transcription_error:
            print(f"Transcription failed: {transcription_error}")
            # Update status to error
            if USE_LOCAL_MODE:
                from ..services import local_db
                local_db.update_meeting_status(meeting_id, "ERROR", f"Transcription failed: {str(transcription_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio transcription failed: {str(transcription_error)}"
            )
        
        # Process transcription with AI
        if USE_LOCAL_MODE:
            try:
                from ..services import ai_processor, local_db
                
                print(f"Starting AI processing for meeting {meeting_id}...")
                extracted_data = ai_processor.process_meeting_notes(
                    meeting_id=meeting_id,
                    text_content=transcription.full_text,
                    meeting_date=meeting_date
                )
                
                # Save extracted data
                local_db.save_extracted_data(meeting_id, extracted_data)
                
                # Update status to DONE
                local_db.update_meeting_status(meeting_id, "DONE")
                
                return {
                    "meeting_id": meeting_id,
                    "status": "DONE",
                    "message": "Audio transcribed and processed successfully",
                    "transcription": {
                        "duration_seconds": transcription.duration_seconds,
                        "speakers": transcription.speakers,
                        "segment_count": len(transcription.segments)
                    },
                    "extracted": {
                        "projects": len(extracted_data.get("projects", [])),
                        "tasks": len(extracted_data.get("tasks", [])),
                        "risks": len(extracted_data.get("risks", [])),
                        "decisions": len(extracted_data.get("decisions", []))
                    }
                }
            except Exception as ai_error:
                print(f"AI processing failed: {ai_error}")
                local_db.update_meeting_status(meeting_id, "ERROR", str(ai_error))
                return {
                    "meeting_id": meeting_id,
                    "status": "ERROR",
                    "message": f"Audio transcribed but AI processing failed: {str(ai_error)}",
                    "transcription": {
                        "duration_seconds": transcription.duration_seconds,
                        "speakers": transcription.speakers,
                        "segment_count": len(transcription.segments)
                    }
                }
        else:
            # Publish to Pub/Sub for async processing
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
            message_json = json.dumps({
                "meeting_id": meeting_id, 
                "gcs_uri": gcs_uri,
                "transcript_format": "audio",
                "processed_text": transcription.full_text,
                "transcription_metadata": {
                    "duration_seconds": transcription.duration_seconds,
                    "speakers": transcription.speakers,
                    "segment_count": len(transcription.segments)
                }
            })
            future = publisher.publish(topic_path, message_json.encode("utf-8"))
            message_id = future.result()
            
            return {
                "meeting_id": meeting_id, 
                "status": "PENDING", 
                "message_id": message_id,
                "transcription": {
                    "duration_seconds": transcription.duration_seconds,
                    "speakers": transcription.speakers,
                    "segment_count": len(transcription.segments)
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
