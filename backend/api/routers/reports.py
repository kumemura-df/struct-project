"""Weekly reports endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timedelta
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


def get_week_range(week_offset: int = 0):
    """Get start and end dates for a week.
    
    week_offset: 0 = current week, -1 = last week, etc.
    """
    today = datetime.now().date()
    # Start of current week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    # Apply offset
    start_of_week = start_of_week + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week


@router.get("/weekly/summary")
def get_weekly_summary(
    week_offset: int = Query(0, description="Week offset (0=current, -1=last week)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get weekly summary with key metrics.
    Returns overdue tasks, high risks, and recent decisions.
    """
    try:
        start_date, end_date = get_week_range(week_offset)
        summary = bigquery.get_weekly_summary(
            start_date.isoformat(),
            end_date.isoformat()
        )
        return {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "week_offset": week_offset,
            **summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly/overdue-tasks")
def get_overdue_tasks(
    limit: int = Query(10, ge=1, le=50, description="Number of tasks to return"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get top overdue tasks sorted by days overdue.
    """
    try:
        tasks = bigquery.get_overdue_tasks(limit=limit, project_id=project_id)
        return {"items": tasks, "total": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly/high-risks")
def get_high_risks(
    limit: int = Query(10, ge=1, le=50, description="Number of risks to return"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get high and medium priority risks.
    """
    try:
        risks = bigquery.get_high_risks(limit=limit, project_id=project_id)
        return {"items": risks, "total": len(risks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email-draft")
def generate_email_draft(
    week_offset: int = Query(0, description="Week offset (0=current, -1=last week)"),
    include_overdue: bool = Query(True, description="Include overdue tasks section"),
    include_risks: bool = Query(True, description="Include risks section"),
    include_decisions: bool = Query(True, description="Include decisions section"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a copy-paste ready email draft for weekly status report.
    """
    try:
        start_date, end_date = get_week_range(week_offset)
        
        # Gather data
        summary = bigquery.get_weekly_summary(
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        overdue_tasks = []
        high_risks = []
        recent_decisions = []
        
        if include_overdue:
            overdue_tasks = bigquery.get_overdue_tasks(limit=10)
        if include_risks:
            high_risks = bigquery.get_high_risks(limit=10)
        if include_decisions:
            recent_decisions = bigquery.get_recent_decisions(
                start_date.isoformat(),
                end_date.isoformat(),
                limit=10
            )
        
        # Generate email text
        email_lines = [
            f"【週次プロジェクト状況レポート】",
            f"期間: {start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%Y/%m/%d')}",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "■ サマリー",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"・全タスク数: {summary.get('total_tasks', 0)}件",
            f"・未完了タスク: {summary.get('incomplete_tasks', 0)}件",
            f"・期限超過タスク: {summary.get('overdue_tasks', 0)}件 ⚠️",
            f"・高リスク: {summary.get('high_risks', 0)}件",
            f"・今週の決定事項: {summary.get('weekly_decisions', 0)}件",
            "",
        ]
        
        if include_overdue and overdue_tasks:
            email_lines.extend([
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "■ 期限超過タスク TOP10",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ])
            for i, task in enumerate(overdue_tasks, 1):
                days = task.get('days_overdue', 0)
                owner = task.get('owner', '未割り当て')
                title = task.get('task_title', 'N/A')
                project = task.get('project_name', 'N/A')
                email_lines.append(
                    f"{i}. [{days}日超過] {title}"
                )
                email_lines.append(
                    f"   担当: {owner} / プロジェクト: {project}"
                )
            email_lines.append("")
        
        if include_risks and high_risks:
            email_lines.extend([
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "■ 高リスク項目",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ])
            for i, risk in enumerate(high_risks, 1):
                level = risk.get('risk_level', 'N/A')
                desc = risk.get('risk_description', 'N/A')
                project = risk.get('project_name', 'N/A')
                level_icon = "🔴" if level == "HIGH" else "🟡"
                email_lines.append(
                    f"{i}. [{level_icon} {level}] {desc[:50]}..."
                )
                email_lines.append(
                    f"   プロジェクト: {project}"
                )
            email_lines.append("")
        
        if include_decisions and recent_decisions:
            email_lines.extend([
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "■ 今週の決定事項",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ])
            for i, decision in enumerate(recent_decisions, 1):
                desc = decision.get('decision_content', decision.get('decision_description', 'N/A'))
                project = decision.get('project_name', 'N/A')
                email_lines.append(f"{i}. {desc[:60]}...")
                email_lines.append(f"   プロジェクト: {project}")
            email_lines.append("")
        
        email_lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "以上",
            "",
            "※ 本レポートはProject Progress DBより自動生成されました。",
        ])
        
        email_text = "\n".join(email_lines)
        
        return {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "email_text": email_text,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/summary")
def get_project_summary(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed summary for a specific project.
    """
    try:
        stats = bigquery.get_project_stats(project_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Project not found")
        
        overdue = bigquery.get_overdue_tasks(limit=5, project_id=project_id)
        risks = bigquery.get_high_risks(limit=5, project_id=project_id)
        
        return {
            "project_id": project_id,
            "stats": stats,
            "top_overdue_tasks": overdue,
            "top_risks": risks
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

