"""Email generation endpoints for weekly reports."""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import Optional
from services import local_db
from auth.middleware import get_current_user

router = APIRouter(prefix="/email", tags=["email"])


def _generate_weekly_report_email(
    overdue_tasks: list,
    high_risks: list,
    project_health: list,
    include_health: bool = True
) -> dict:
    """Generate weekly report email content."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Build subject line
    overdue_count = len(overdue_tasks)
    risk_count = len(high_risks)
    subject = f"Weekly Report: {overdue_count} Overdue Tasks, {risk_count} High Risks ({today})"

    # Build email body
    lines = []
    lines.append("=" * 60)
    lines.append("WEEKLY PROJECT STATUS REPORT")
    lines.append(f"Generated: {today}")
    lines.append("=" * 60)
    lines.append("")

    # Top 10 Overdue Tasks
    lines.append("-" * 40)
    lines.append("TOP 10 OVERDUE TASKS")
    lines.append("-" * 40)

    if overdue_tasks:
        for i, task in enumerate(overdue_tasks[:10], 1):
            project_name = task.get("project_name", "Unknown Project")
            task_title = task.get("task_title", "No title")
            owner = task.get("owner", "Unassigned")
            due_date = task.get("due_date", "No date")
            days_overdue = ""
            if due_date and due_date != "No date":
                try:
                    due = datetime.strptime(due_date, "%Y-%m-%d")
                    delta = (datetime.now() - due).days
                    days_overdue = f" ({delta} days overdue)"
                except ValueError:
                    pass

            lines.append(f"{i}. [{project_name}] {task_title}")
            lines.append(f"   Owner: {owner} | Due: {due_date}{days_overdue}")
            lines.append("")
    else:
        lines.append("No overdue tasks.")
        lines.append("")

    # Top 10 High Risks
    lines.append("-" * 40)
    lines.append("TOP 10 HIGH RISKS")
    lines.append("-" * 40)

    if high_risks:
        for i, risk in enumerate(high_risks[:10], 1):
            project_name = risk.get("project_name", "Unknown Project")
            description = risk.get("risk_description", "No description")
            owner = risk.get("owner", "Unassigned")

            lines.append(f"{i}. [{project_name}] {description[:80]}{'...' if len(description) > 80 else ''}")
            lines.append(f"   Owner: {owner}")
            lines.append("")
    else:
        lines.append("No high risks.")
        lines.append("")

    # Project Health Summary
    if include_health and project_health:
        lines.append("-" * 40)
        lines.append("PROJECT HEALTH SUMMARY")
        lines.append("-" * 40)

        # Sort by score (lowest first = most critical)
        sorted_health = sorted(project_health, key=lambda x: x.get("score", 100))

        for ph in sorted_health[:10]:
            project_name = ph.get("project_name", "Unknown")
            score = ph.get("score", 0)
            status = ph.get("status", "UNKNOWN")

            status_icon = {
                "HEALTHY": "[OK]",
                "AT_RISK": "[!]",
                "WARNING": "[!!]",
                "CRITICAL": "[!!!]"
            }.get(status, "[?]")

            lines.append(f"{status_icon} {project_name}: {score}/100 ({status})")

        lines.append("")

    # Footer
    lines.append("=" * 60)
    lines.append("This report was automatically generated.")
    lines.append("Please review and take necessary actions.")
    lines.append("=" * 60)

    body = "\n".join(lines)

    return {
        "subject": subject,
        "body": body,
        "summary": {
            "overdue_tasks_count": overdue_count,
            "high_risks_count": risk_count,
            "projects_analyzed": len(project_health) if project_health else 0
        },
        "generated_at": datetime.now().isoformat()
    }


@router.get("/weekly-report")
def generate_weekly_report(
    include_health: bool = Query(default=True, description="Include project health summary"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate weekly report email draft with:
    - Top 10 overdue tasks
    - Top 10 high risks
    - Project health summary (optional)
    """
    # Get overdue tasks
    overdue_tasks = local_db.get_overdue_tasks()

    # Get high risks
    high_risks = local_db.get_high_risks()

    # Get project health scores
    project_health = []
    if include_health:
        try:
            project_health = local_db.get_all_project_health_scores()
        except Exception:
            pass  # Continue without health scores if error

    return _generate_weekly_report_email(
        overdue_tasks=overdue_tasks,
        high_risks=high_risks,
        project_health=project_health,
        include_health=include_health
    )


@router.get("/weekly-report/html")
def generate_weekly_report_html(
    include_health: bool = Query(default=True, description="Include project health summary"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate weekly report email draft in HTML format.
    """
    # Get data
    overdue_tasks = local_db.get_overdue_tasks()
    high_risks = local_db.get_high_risks()
    project_health = []
    if include_health:
        try:
            project_health = local_db.get_all_project_health_scores()
        except Exception:
            pass

    today = datetime.now().strftime("%Y-%m-%d")
    overdue_count = len(overdue_tasks)
    risk_count = len(high_risks)

    subject = f"Weekly Report: {overdue_count} Overdue Tasks, {risk_count} High Risks ({today})"

    # Build HTML body
    html_parts = []
    html_parts.append("""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0;">Weekly Project Status Report</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">Generated: """ + today + """</p>
        </div>
    """)

    # Overdue Tasks Section
    html_parts.append("""
        <div style="background: #fff; padding: 20px; border: 1px solid #e0e0e0;">
            <h2 style="color: #e53e3e; margin-top: 0;">Top 10 Overdue Tasks</h2>
    """)

    if overdue_tasks:
        html_parts.append('<table style="width: 100%; border-collapse: collapse;">')
        html_parts.append('<tr style="background: #f7fafc;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">#</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">Task</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">Owner</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">Due Date</th></tr>')

        for i, task in enumerate(overdue_tasks[:10], 1):
            project_name = task.get("project_name", "Unknown")
            task_title = task.get("task_title", "No title")
            owner = task.get("owner", "Unassigned")
            due_date = task.get("due_date", "-")

            html_parts.append(f'<tr><td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{i}</td><td style="padding: 10px; border-bottom: 1px solid #e0e0e0;"><strong>[{project_name}]</strong><br/>{task_title}</td><td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{owner}</td><td style="padding: 10px; border-bottom: 1px solid #e0e0e0; color: #e53e3e;">{due_date}</td></tr>')

        html_parts.append('</table>')
    else:
        html_parts.append('<p style="color: #38a169;">No overdue tasks.</p>')

    html_parts.append('</div>')

    # High Risks Section
    html_parts.append("""
        <div style="background: #fff; padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
            <h2 style="color: #dd6b20; margin-top: 0;">Top 10 High Risks</h2>
    """)

    if high_risks:
        html_parts.append('<table style="width: 100%; border-collapse: collapse;">')
        html_parts.append('<tr style="background: #f7fafc;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">#</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">Risk</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">Owner</th></tr>')

        for i, risk in enumerate(high_risks[:10], 1):
            project_name = risk.get("project_name", "Unknown")
            description = risk.get("risk_description", "No description")
            if len(description) > 100:
                description = description[:100] + "..."
            owner = risk.get("owner", "Unassigned")

            html_parts.append(f'<tr><td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{i}</td><td style="padding: 10px; border-bottom: 1px solid #e0e0e0;"><strong>[{project_name}]</strong><br/>{description}</td><td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{owner}</td></tr>')

        html_parts.append('</table>')
    else:
        html_parts.append('<p style="color: #38a169;">No high risks.</p>')

    html_parts.append('</div>')

    # Project Health Section
    if include_health and project_health:
        html_parts.append("""
            <div style="background: #fff; padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
                <h2 style="color: #3182ce; margin-top: 0;">Project Health Summary</h2>
        """)

        sorted_health = sorted(project_health, key=lambda x: x.get("score", 100))

        for ph in sorted_health[:10]:
            project_name = ph.get("project_name", "Unknown")
            score = ph.get("score", 0)
            status = ph.get("status", "UNKNOWN")

            color = {
                "HEALTHY": "#38a169",
                "AT_RISK": "#d69e2e",
                "WARNING": "#dd6b20",
                "CRITICAL": "#e53e3e"
            }.get(status, "#718096")

            bar_width = score

            html_parts.append(f'''
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="font-weight: bold;">{project_name}</span>
                        <span style="color: {color}; font-weight: bold;">{score}/100 ({status})</span>
                    </div>
                    <div style="background: #e0e0e0; border-radius: 4px; height: 8px;">
                        <div style="background: {color}; width: {bar_width}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
            ''')

        html_parts.append('</div>')

    # Footer
    html_parts.append("""
        <div style="background: #f7fafc; padding: 15px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px; text-align: center; color: #718096;">
            <p style="margin: 0;">This report was automatically generated. Please review and take necessary actions.</p>
        </div>
    </div>
    """)

    html_body = "".join(html_parts)

    return {
        "subject": subject,
        "body_html": html_body,
        "summary": {
            "overdue_tasks_count": overdue_count,
            "high_risks_count": risk_count,
            "projects_analyzed": len(project_health) if project_health else 0
        },
        "generated_at": datetime.now().isoformat()
    }
