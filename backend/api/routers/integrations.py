"""External integrations endpoints."""
import os
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from services import bigquery
from auth.middleware import get_current_user

# Import integration clients
try:
    from integrations.google_drive import GoogleDriveClient, is_available as drive_available
    from integrations.google_docs import GoogleDocsClient, is_available as docs_available
    from integrations.google_calendar import GoogleCalendarClient, is_available as calendar_available
    from integrations.slack import SlackNotifier, is_available as slack_available
except ImportError as e:
    print(f"Warning: Some integrations not available: {e}")
    drive_available = lambda: False
    docs_available = lambda: False
    calendar_available = lambda: False
    slack_available = lambda: False

router = APIRouter(prefix="/integrations", tags=["integrations"])


class SlackWebhookConfig(BaseModel):
    webhook_url: str


class SlackNotifyRequest(BaseModel):
    type: str  # 'overdue_tasks', 'high_risks', 'weekly_summary', 'test'
    webhook_url: Optional[str] = None


class GoogleImportRequest(BaseModel):
    file_id: str
    meeting_date: str
    title: Optional[str] = None


@router.get("/status")
def get_integration_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of all integrations.
    Returns availability and configuration status.
    """
    return {
        "google": {
            "drive": {
                "available": drive_available(),
                "configured": bool(os.getenv("OAUTH_CLIENT_ID"))
            },
            "docs": {
                "available": docs_available(),
                "configured": bool(os.getenv("OAUTH_CLIENT_ID"))
            },
            "calendar": {
                "available": calendar_available(),
                "configured": bool(os.getenv("OAUTH_CLIENT_ID"))
            }
        },
        "slack": {
            "available": slack_available(),
            "configured": bool(os.getenv("SLACK_WEBHOOK_URL"))
        }
    }


# ===== GOOGLE DRIVE =====

@router.get("/google/files")
def list_google_drive_files(
    folder_id: Optional[str] = Query(None, description="Folder ID to list files from"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    List files from Google Drive.
    Requires OAuth credentials in session.
    """
    if not drive_available():
        raise HTTPException(status_code=503, detail="Google Drive integration not available")
    
    try:
        # TODO: Get credentials from session/database
        # For now, return mock data for testing UI
        return {
            "files": [],
            "message": "Google Drive連携にはOAuth認証が必要です"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google/import")
def import_from_google_drive(
    request: GoogleImportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Import a file from Google Drive as meeting notes.
    """
    if not drive_available():
        raise HTTPException(status_code=503, detail="Google Drive integration not available")
    
    try:
        # TODO: Implement actual import
        return {
            "success": False,
            "message": "Google Drive連携にはOAuth認証が必要です"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== GOOGLE CALENDAR =====

@router.get("/calendar/events")
def list_calendar_events(
    days_back: int = Query(30, ge=1, le=90),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    List meeting events from Google Calendar.
    """
    if not calendar_available():
        raise HTTPException(status_code=503, detail="Google Calendar integration not available")
    
    try:
        # TODO: Get credentials from session/database
        return {
            "events": [],
            "message": "Google Calendar連携にはOAuth認証が必要です"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== SLACK =====

@router.post("/slack/test")
def test_slack_webhook(
    config: SlackWebhookConfig,
    current_user: dict = Depends(get_current_user)
):
    """
    Test Slack webhook configuration.
    """
    if not slack_available():
        raise HTTPException(status_code=503, detail="Slack integration not available (httpx not installed)")
    
    try:
        notifier = SlackNotifier(webhook_url=config.webhook_url)
        success = notifier.test_connection()
        
        if success:
            return {"success": True, "message": "Slack接続テストに成功しました"}
        else:
            raise HTTPException(status_code=400, detail="Slack接続テストに失敗しました")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/notify")
def send_slack_notification(
    request: SlackNotifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a notification to Slack.
    Types: 'overdue_tasks', 'high_risks', 'weekly_summary', 'test'
    """
    if not slack_available():
        raise HTTPException(status_code=503, detail="Slack integration not available")
    
    webhook_url = request.webhook_url or os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise HTTPException(status_code=400, detail="Slack webhook URL not configured")
    
    try:
        notifier = SlackNotifier(webhook_url=webhook_url)
        
        if request.type == 'test':
            success = notifier.test_connection()
        elif request.type == 'overdue_tasks':
            tasks = bigquery.get_overdue_tasks(limit=10)
            success = notifier.send_overdue_tasks_alert(tasks)
        elif request.type == 'high_risks':
            risks = bigquery.get_high_risks(limit=10)
            success = notifier.send_high_risks_alert(risks)
        elif request.type == 'weekly_summary':
            from datetime import datetime, timedelta
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            summary = bigquery.get_weekly_summary(
                week_start.isoformat(),
                week_end.isoformat()
            )
            summary['week_start'] = week_start.isoformat()
            summary['week_end'] = week_end.isoformat()
            success = notifier.send_weekly_summary(summary)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown notification type: {request.type}")
        
        if success:
            return {"success": True, "message": "通知を送信しました"}
        else:
            raise HTTPException(status_code=500, detail="通知の送信に失敗しました")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slack/status")
def get_slack_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get Slack integration status.
    """
    return {
        "available": slack_available(),
        "configured": bool(os.getenv("SLACK_WEBHOOK_URL")),
        "webhook_configured": bool(os.getenv("SLACK_WEBHOOK_URL"))
    }

