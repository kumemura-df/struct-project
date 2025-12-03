"""Slack notification service."""
import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Default webhook URL from environment
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def send_slack_message(
    message: str,
    webhook_url: Optional[str] = None,
    blocks: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """
    Send a message to Slack via webhook.

    Args:
        message: Plain text message (used as fallback)
        webhook_url: Slack webhook URL (uses env var if not provided)
        blocks: Optional Block Kit blocks for rich formatting

    Returns:
        True if successful, False otherwise
    """
    url = webhook_url or SLACK_WEBHOOK_URL
    if not url:
        logger.warning("No Slack webhook URL configured")
        return False

    payload = {"text": message}
    if blocks:
        payload["blocks"] = blocks

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Slack API returned status {response.status}")
                return False

    except urllib.error.URLError as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {e}")
        return False


def notify_high_risks(
    risks: List[Dict[str, Any]],
    webhook_url: Optional[str] = None
) -> bool:
    """
    Send notification about high-level risks.

    Args:
        risks: List of high-level risks
        webhook_url: Optional webhook URL override
    """
    if not risks:
        return True

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "High Risk Alert",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{len(risks)} high-level risk(s) detected*"
            }
        },
        {"type": "divider"}
    ]

    for risk in risks[:5]:  # Limit to 5 risks
        risk_text = risk.get("risk_description", "No description")[:200]
        owner = risk.get("owner", "Unassigned")
        project = risk.get("project_name", "Unknown Project")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{project}*\n{risk_text}\n_Owner: {owner}_"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "HIGH",
                    "emoji": True
                },
                "style": "danger"
            }
        })

    if len(risks) > 5:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_...and {len(risks) - 5} more risks_"
                }
            ]
        })

    return send_slack_message(
        f"High Risk Alert: {len(risks)} high-level risk(s) detected",
        webhook_url=webhook_url,
        blocks=blocks
    )


def notify_overdue_tasks(
    tasks: List[Dict[str, Any]],
    webhook_url: Optional[str] = None
) -> bool:
    """
    Send notification about overdue tasks.

    Args:
        tasks: List of overdue tasks
        webhook_url: Optional webhook URL override
    """
    if not tasks:
        return True

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Overdue Tasks Alert",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{len(tasks)} overdue task(s)*"
            }
        },
        {"type": "divider"}
    ]

    for task in tasks[:5]:  # Limit to 5 tasks
        task_title = task.get("task_title", "Untitled")[:100]
        owner = task.get("owner", "Unassigned")
        due_date = task.get("due_date", "Unknown")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{task_title}*\n_Owner: {owner} | Due: {due_date}_"
            }
        })

    if len(tasks) > 5:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_...and {len(tasks) - 5} more overdue tasks_"
                }
            ]
        })

    return send_slack_message(
        f"Overdue Tasks Alert: {len(tasks)} task(s) past due date",
        webhook_url=webhook_url,
        blocks=blocks
    )


def notify_meeting_processed(
    meeting_title: str,
    meeting_date: str,
    stats: Dict[str, int],
    webhook_url: Optional[str] = None
) -> bool:
    """
    Send notification when meeting processing is complete.

    Args:
        meeting_title: Title of the meeting
        meeting_date: Date of the meeting
        stats: Dictionary with counts (projects, tasks, risks, decisions)
        webhook_url: Optional webhook URL override
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Meeting Processed",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{meeting_title or 'Untitled Meeting'}*\nDate: {meeting_date}"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Projects:*\n{stats.get('projects', 0)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Tasks:*\n{stats.get('tasks', 0)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Risks:*\n{stats.get('risks', 0)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Decisions:*\n{stats.get('decisions', 0)}"
                }
            ]
        }
    ]

    # Add high risk warning if any
    high_risks = stats.get("high_risks", 0)
    if high_risks > 0:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":warning: *{high_risks} high-level risk(s) identified*"
                }
            ]
        })

    return send_slack_message(
        f"Meeting processed: {meeting_title} - {stats.get('tasks', 0)} tasks, {stats.get('risks', 0)} risks",
        webhook_url=webhook_url,
        blocks=blocks
    )


def notify_escalated_risks(
    escalated: List[Dict[str, Any]],
    webhook_url: Optional[str] = None
) -> bool:
    """
    Send notification about escalated risks (risks that increased in level).

    Args:
        escalated: List of escalated risk changes
        webhook_url: Optional webhook URL override
    """
    if not escalated:
        return True

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Risk Escalation Alert",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{len(escalated)} risk(s) have been escalated*"
            }
        },
        {"type": "divider"}
    ]

    for item in escalated[:5]:
        risk = item.get("risk", {})
        risk_desc = risk.get("risk_description", "No description")[:150]
        prev_level = item.get("prev_level", "?")
        curr_level = item.get("curr_level", "?")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{risk_desc}\n*{prev_level}* → *{curr_level}*"
            }
        })

    return send_slack_message(
        f"Risk Escalation: {len(escalated)} risk(s) escalated",
        webhook_url=webhook_url,
        blocks=blocks
    )
