"""Health score endpoints for project health monitoring."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from services import bigquery
from auth.middleware import get_current_user

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/projects")
def get_all_project_scores(
    current_user: dict = Depends(get_current_user)
):
    """
    Get health scores for all projects.
    Returns projects sorted by score (lowest first = most attention needed).
    """
    try:
        scores = bigquery.get_all_projects_health_scores()
        
        # Calculate overall health
        if scores:
            avg_score = sum(s["score"] for s in scores) / len(scores)
            critical_count = sum(1 for s in scores if s["score"] < 50)
            warning_count = sum(1 for s in scores if 50 <= s["score"] < 70)
            healthy_count = sum(1 for s in scores if s["score"] >= 70)
        else:
            avg_score = 0
            critical_count = warning_count = healthy_count = 0
        
        return {
            "projects": scores,
            "summary": {
                "total_projects": len(scores),
                "average_score": round(avg_score, 1),
                "critical_count": critical_count,
                "warning_count": warning_count,
                "healthy_count": healthy_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}")
def get_project_health(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed health score for a specific project.
    """
    try:
        # Get current score
        score = bigquery.calculate_project_health_score(project_id)
        
        # Get project info
        project = bigquery.get_project(project_id)
        if project:
            score["project_name"] = project.get("project_name", "Unknown")
        
        # Determine health status
        if score["score"] >= 80:
            score["status"] = "healthy"
            score["status_label"] = "良好"
            score["status_color"] = "green"
        elif score["score"] >= 60:
            score["status"] = "warning"
            score["status_label"] = "注意"
            score["status_color"] = "yellow"
        elif score["score"] >= 40:
            score["status"] = "at_risk"
            score["status_label"] = "リスクあり"
            score["status_color"] = "orange"
        else:
            score["status"] = "critical"
            score["status_label"] = "危険"
            score["status_color"] = "red"
        
        # Generate recommendations
        recommendations = []
        if score["overdue_penalty"] > 10:
            recommendations.append({
                "type": "overdue",
                "priority": "high",
                "message": f"期限超過タスクが {score['details']['overdue_tasks']} 件あります。優先的に対応してください。"
            })
        if score["risk_penalty"] > 10:
            recommendations.append({
                "type": "risk",
                "priority": "high",
                "message": f"高リスク項目が {score['details']['high_risks']} 件あります。リスク軽減策を検討してください。"
            })
        if score["uncompleted_penalty"] > 5:
            recommendations.append({
                "type": "progress",
                "priority": "medium",
                "message": f"完了率が {score['details']['completion_rate']}% です。タスク消化を加速してください。"
            })
        if score["stale_penalty"] > 5:
            recommendations.append({
                "type": "stale",
                "priority": "medium",
                "message": "最近の更新がありません。プロジェクト状況を確認してください。"
            })
        
        score["recommendations"] = recommendations
        
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/history")
def get_project_health_history(
    project_id: str,
    limit: int = Query(30, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get health score history for trend analysis.
    """
    try:
        history = bigquery.get_health_score_history(project_id, limit=limit)
        
        # Calculate trend
        trend = "stable"
        if len(history) >= 2:
            recent_avg = sum(h["score"] for h in history[:5]) / min(5, len(history))
            older_avg = sum(h["score"] for h in history[5:10]) / max(1, min(5, len(history) - 5)) if len(history) > 5 else recent_avg
            
            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
        
        return {
            "project_id": project_id,
            "history": history,
            "trend": trend,
            "trend_label": {
                "improving": "改善傾向",
                "declining": "悪化傾向",
                "stable": "安定"
            }.get(trend, "安定")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/snapshot")
def save_project_health_snapshot(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Save current health score as a snapshot (for trend tracking).
    """
    try:
        score = bigquery.calculate_project_health_score(project_id)
        snapshot_id = bigquery.save_health_score_snapshot(project_id, score)
        
        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "score": score["score"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
def compare_projects(
    project_ids: str = Query(..., description="Comma-separated project IDs"),
    current_user: dict = Depends(get_current_user)
):
    """
    Compare health scores of multiple projects.
    """
    try:
        ids = [p.strip() for p in project_ids.split(",") if p.strip()]
        
        if len(ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 project IDs required")
        if len(ids) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 projects can be compared")
        
        comparisons = []
        for pid in ids:
            score = bigquery.calculate_project_health_score(pid)
            project = bigquery.get_project(pid)
            score["project_name"] = project.get("project_name", "Unknown") if project else "Unknown"
            comparisons.append(score)
        
        # Sort by score
        comparisons.sort(key=lambda x: x["score"], reverse=True)
        
        # Calculate rankings
        for i, comp in enumerate(comparisons):
            comp["rank"] = i + 1
        
        return {
            "comparisons": comparisons,
            "best": comparisons[0]["project_name"] if comparisons else None,
            "worst": comparisons[-1]["project_name"] if comparisons else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
def get_health_alerts(
    threshold: int = Query(60, ge=0, le=100, description="Score threshold for alerts"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get projects that need attention based on health score threshold.
    """
    try:
        all_scores = bigquery.get_all_projects_health_scores()
        
        alerts = []
        for score in all_scores:
            if score["score"] < threshold:
                alert_level = "critical" if score["score"] < 40 else "warning"
                alerts.append({
                    "project_id": score["project_id"],
                    "project_name": score.get("project_name", "Unknown"),
                    "score": score["score"],
                    "alert_level": alert_level,
                    "issues": []
                })
                
                # Add specific issues
                if score["overdue_penalty"] > 10:
                    alerts[-1]["issues"].append(f"期限超過: {score['details']['overdue_tasks']}件")
                if score["risk_penalty"] > 10:
                    alerts[-1]["issues"].append(f"高リスク: {score['details']['high_risks']}件")
                if score["details"]["completion_rate"] < 30:
                    alerts[-1]["issues"].append(f"進捗遅延: {score['details']['completion_rate']}%完了")
        
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "critical_count": sum(1 for a in alerts if a["alert_level"] == "critical"),
            "warning_count": sum(1 for a in alerts if a["alert_level"] == "warning")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

