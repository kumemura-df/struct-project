"""Slack notification service for Worker."""
import requests
from typing import Dict, Any, List, Optional


def send_slack_message(
    message: str,
    webhook_url: str,
    blocks: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """Send a message to Slack via webhook."""
    try:
        payload = {"text": message}
        if blocks:
            payload["blocks"] = blocks

        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Slack notification error: {e}")
        return False


def notify_meeting_processed(
    meeting_title: str,
    meeting_date: str,
    stats: Dict[str, int],
    webhook_url: str
) -> bool:
    """Send notification when meeting processing is complete."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📋 Meeting Processed",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Meeting:*\n{meeting_title}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Date:*\n{meeting_date}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Extracted Items:*\n• Projects: {stats.get('projects_count', 0)}\n• Tasks: {stats.get('tasks_count', 0)}\n• Risks: {stats.get('risks_count', 0)}\n• Decisions: {stats.get('decisions_count', 0)}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Processed by Project Progress DB_"
                }
            ]
        }
    ]

    return send_slack_message(
        message=f"Meeting '{meeting_title}' has been processed.",
        webhook_url=webhook_url,
        blocks=blocks
    )


def notify_high_risks(
    risks: List[Dict[str, Any]],
    webhook_url: str
) -> bool:
    """Send notification about HIGH level risks."""
    if not risks:
        return True

    risk_list = "\n".join([
        f"• {r.get('risk_description', 'N/A')[:100]} ({r.get('project_name', 'Unknown')})"
        for r in risks[:5]
    ])

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚠️ High Risk Alert",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{len(risks)} HIGH level risk(s) detected:*\n{risk_list}"
            }
        }
    ]

    if len(risks) > 5:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_...and {len(risks) - 5} more_"
                }
            ]
        })

    return send_slack_message(
        message=f"High Risk Alert: {len(risks)} HIGH level risk(s) detected",
        webhook_url=webhook_url,
        blocks=blocks
    )
