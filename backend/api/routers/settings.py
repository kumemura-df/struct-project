"""Settings management endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from services import local_db, slack
from auth.middleware import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


class SlackSettings(BaseModel):
    webhook_url: str
    notify_on_high_risk: bool = True
    notify_on_overdue: bool = True
    notify_on_meeting_processed: bool = True


class SlackTestMessage(BaseModel):
    webhook_url: Optional[str] = None
    message: str = "Test notification from Project Progress DB"


@router.get("/slack")
def get_slack_settings(current_user: dict = Depends(get_current_user)):
    """Get current Slack notification settings."""
    try:
        settings = {
            "webhook_url": local_db.get_setting("slack_webhook_url") or "",
            "notify_on_high_risk": local_db.get_setting("slack_notify_high_risk") != "false",
            "notify_on_overdue": local_db.get_setting("slack_notify_overdue") != "false",
            "notify_on_meeting_processed": local_db.get_setting("slack_notify_meeting") != "false",
        }
        # Mask webhook URL for security
        if settings["webhook_url"]:
            settings["webhook_url_masked"] = settings["webhook_url"][:30] + "..." if len(settings["webhook_url"]) > 30 else settings["webhook_url"]
        else:
            settings["webhook_url_masked"] = ""

        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack")
def update_slack_settings(
    settings: SlackSettings,
    current_user: dict = Depends(get_current_user)
):
    """Update Slack notification settings."""
    try:
        local_db.set_setting("slack_webhook_url", settings.webhook_url)
        local_db.set_setting("slack_notify_high_risk", str(settings.notify_on_high_risk).lower())
        local_db.set_setting("slack_notify_overdue", str(settings.notify_on_overdue).lower())
        local_db.set_setting("slack_notify_meeting", str(settings.notify_on_meeting_processed).lower())

        return {"message": "Slack settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/slack")
def delete_slack_settings(current_user: dict = Depends(get_current_user)):
    """Delete Slack webhook configuration."""
    try:
        local_db.delete_setting("slack_webhook_url")
        return {"message": "Slack webhook deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/test")
def test_slack_notification(
    data: SlackTestMessage,
    current_user: dict = Depends(get_current_user)
):
    """Send a test notification to Slack."""
    try:
        webhook_url = data.webhook_url or local_db.get_setting("slack_webhook_url")

        if not webhook_url:
            raise HTTPException(
                status_code=400,
                detail="No webhook URL configured. Please set up Slack integration first."
            )

        success = slack.send_slack_message(
            message=data.message,
            webhook_url=webhook_url,
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Test Notification",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Message:* {data.message}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "_Sent from Project Progress DB_"
                        }
                    ]
                }
            ]
        )

        if success:
            return {"message": "Test notification sent successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send notification. Please check webhook URL."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/notify-now")
def send_immediate_notifications(current_user: dict = Depends(get_current_user)):
    """
    Send immediate notifications for current high risks and overdue tasks.

    Useful for manual trigger or scheduled jobs.
    """
    try:
        webhook_url = local_db.get_setting("slack_webhook_url")
        if not webhook_url:
            raise HTTPException(
                status_code=400,
                detail="Slack webhook not configured"
            )

        results = {
            "high_risks_notified": False,
            "overdue_tasks_notified": False,
            "high_risks_count": 0,
            "overdue_tasks_count": 0
        }

        # Check settings
        notify_risks = local_db.get_setting("slack_notify_high_risk") != "false"
        notify_overdue = local_db.get_setting("slack_notify_overdue") != "false"

        # Send high risk notifications
        if notify_risks:
            high_risks = local_db.get_high_risks()
            results["high_risks_count"] = len(high_risks)
            if high_risks:
                results["high_risks_notified"] = slack.notify_high_risks(
                    high_risks, webhook_url
                )

        # Send overdue task notifications
        if notify_overdue:
            overdue_tasks = local_db.get_overdue_tasks()
            results["overdue_tasks_count"] = len(overdue_tasks)
            if overdue_tasks:
                results["overdue_tasks_notified"] = slack.notify_overdue_tasks(
                    overdue_tasks, webhook_url
                )

        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
