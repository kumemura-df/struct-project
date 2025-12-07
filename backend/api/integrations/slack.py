"""Slack integration for sending notifications."""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class SlackNotifier:
    """Client for sending Slack notifications via webhooks."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack Incoming Webhook URL
        """
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
    
    def send_message(
        self,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send a message to Slack.
        
        Args:
            text: Fallback text for notifications
            blocks: Optional Block Kit blocks for rich formatting
            attachments: Optional attachments
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            raise Exception("Slack webhook URL not configured")
        
        if not HTTPX_AVAILABLE:
            raise Exception("httpx library not installed")
        
        payload = {"text": text}
        
        if blocks:
            payload["blocks"] = blocks
        
        if attachments:
            payload["attachments"] = attachments
        
        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Slack notification failed: {e}")
            return False
    
    def send_overdue_tasks_alert(
        self,
        tasks: List[Dict[str, Any]],
        limit: int = 10
    ) -> bool:
        """
        Send an alert about overdue tasks.
        
        Args:
            tasks: List of overdue task dictionaries
            limit: Maximum number of tasks to include
        """
        if not tasks:
            return True
        
        tasks = tasks[:limit]
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 期限超過タスクアラート",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(tasks)}件* のタスクが期限を超過しています"
                }
            },
            {"type": "divider"}
        ]
        
        for task in tasks:
            days = int(task.get('days_overdue', 0))
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{task.get('task_title', 'N/A')}*\n"
                        f"👤 担当: {task.get('owner', '未割当')} | "
                        f"📅 {days}日超過 | "
                        f"📁 {task.get('project_name', 'N/A')}"
                    )
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"送信日時: {datetime.now().strftime('%Y/%m/%d %H:%M')}"
                }
            ]
        })
        
        return self.send_message(
            text=f"🚨 {len(tasks)}件の期限超過タスクがあります",
            blocks=blocks
        )
    
    def send_high_risks_alert(
        self,
        risks: List[Dict[str, Any]],
        limit: int = 10
    ) -> bool:
        """
        Send an alert about high-priority risks.
        
        Args:
            risks: List of high-priority risk dictionaries
            limit: Maximum number of risks to include
        """
        if not risks:
            return True
        
        risks = risks[:limit]
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ 高リスクアラート",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(risks)}件* の高リスク項目があります"
                }
            },
            {"type": "divider"}
        ]
        
        for risk in risks:
            level = risk.get('risk_level', 'UNKNOWN')
            emoji = "🔴" if level == "HIGH" else "🟡" if level == "MEDIUM" else "🟢"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{emoji} *[{level}]* {risk.get('risk_description', 'N/A')[:100]}\n"
                        f"📁 {risk.get('project_name', 'N/A')}"
                    )
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"送信日時: {datetime.now().strftime('%Y/%m/%d %H:%M')}"
                }
            ]
        })
        
        return self.send_message(
            text=f"⚠️ {len(risks)}件の高リスク項目があります",
            blocks=blocks
        )
    
    def send_weekly_summary(
        self,
        summary: Dict[str, Any]
    ) -> bool:
        """
        Send weekly summary notification.
        
        Args:
            summary: Weekly summary dictionary with stats
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 週次サマリー",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*全タスク*\n{summary.get('total_tasks', 0)}件"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*未完了*\n{summary.get('incomplete_tasks', 0)}件"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*期限超過*\n{summary.get('overdue_tasks', 0)}件"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*高リスク*\n{summary.get('high_risks', 0)}件"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"期間: {summary.get('week_start', 'N/A')} 〜 {summary.get('week_end', 'N/A')}"
                    }
                ]
            }
        ]
        
        return self.send_message(
            text="📊 週次サマリーが生成されました",
            blocks=blocks
        )
    
    def test_connection(self) -> bool:
        """Send a test message to verify webhook configuration."""
        return self.send_message(
            text="✅ Project Progress DB からのテストメッセージです",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✅ *接続テスト成功*\nSlack通知が正常に設定されています"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"テスト日時: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        )


def is_available() -> bool:
    """Check if Slack integration is available."""
    return HTTPX_AVAILABLE

