"""AI-powered query and chat endpoints."""
import os
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from services import bigquery
from auth.middleware import get_current_user

# Check if Vertex AI is available
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

PROJECT_ID = os.getenv("PROJECT_ID", "local-dev")
REGION = os.getenv("REGION", "asia-northeast1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Initialize Vertex AI
if VERTEX_AI_AVAILABLE and PROJECT_ID != "local-dev":
    try:
        vertexai.init(project=PROJECT_ID, location=REGION)
    except Exception as e:
        print(f"Warning: Failed to initialize Vertex AI: {e}")
        VERTEX_AI_AVAILABLE = False

router = APIRouter(prefix="/ai", tags=["ai"])


class QueryRequest(BaseModel):
    query: str
    context: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None


class AgendaRequest(BaseModel):
    project_id: Optional[str] = None


def get_system_context() -> str:
    """Get current system context for AI."""
    try:
        # Get summary statistics
        tasks_data = bigquery.list_tasks_paginated(limit=100)
        risks_data = bigquery.list_risks_paginated(limit=50)
        projects_data = bigquery.list_projects_paginated(limit=20)
        
        today = datetime.now().date()
        
        # Calculate statistics
        total_tasks = tasks_data.get("total", 0)
        incomplete_tasks = len([t for t in tasks_data.get("items", []) if t.get("status") != "DONE"])
        overdue_tasks = len([
            t for t in tasks_data.get("items", [])
            if t.get("status") != "DONE" and t.get("due_date") and t.get("due_date") < str(today)
        ])
        
        high_risks = len([r for r in risks_data.get("items", []) if r.get("risk_level") == "HIGH"])
        
        # Get project names
        project_names = [p.get("project_name", "") for p in projects_data.get("items", [])]
        
        # Get sample tasks for context
        sample_tasks = tasks_data.get("items", [])[:10]
        task_info = "\n".join([
            f"- {t.get('task_title')} (担当: {t.get('owner', '未割当')}, 期限: {t.get('due_date', 'なし')}, 状態: {t.get('status')})"
            for t in sample_tasks
        ])
        
        context = f"""
現在のプロジェクト状況:
- プロジェクト数: {len(project_names)}件 ({', '.join(project_names[:5])}...)
- 全タスク数: {total_tasks}件
- 未完了タスク: {incomplete_tasks}件
- 期限超過タスク: {overdue_tasks}件
- 高リスク項目: {high_risks}件

最近のタスク:
{task_info}
"""
        return context
    except Exception as e:
        return f"システム情報取得エラー: {str(e)}"


def process_natural_language_query(query: str) -> Dict[str, Any]:
    """Process natural language query and return filtered results."""
    query_lower = query.lower()
    
    filters = {}
    result_type = "tasks"  # default
    
    # Detect result type
    if "リスク" in query or "risk" in query_lower:
        result_type = "risks"
    elif "決定" in query or "decision" in query_lower:
        result_type = "decisions"
    elif "プロジェクト" in query or "project" in query_lower:
        result_type = "projects"
    
    # Detect time filters
    today = datetime.now().date()
    if "今週" in query or "this week" in query_lower:
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        filters["due_date_from"] = week_start.isoformat()
        filters["due_date_to"] = week_end.isoformat()
    elif "今月" in query or "this month" in query_lower:
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        filters["due_date_from"] = month_start.isoformat()
        filters["due_date_to"] = month_end.isoformat()
    elif "期限超過" in query or "遅延" in query or "overdue" in query_lower:
        filters["due_date_to"] = (today - timedelta(days=1)).isoformat()
    
    # Detect status filters
    if "未完了" in query or "incomplete" in query_lower:
        filters["status"] = ["NOT_STARTED", "IN_PROGRESS"]
    elif "完了" in query or "done" in query_lower or "completed" in query_lower:
        filters["status"] = ["DONE"]
    elif "進行中" in query or "in progress" in query_lower:
        filters["status"] = ["IN_PROGRESS"]
    
    # Detect priority filters
    if "高優先" in query or "high priority" in query_lower or "優先度高" in query:
        filters["priority"] = ["HIGH"]
    
    # Detect risk level filters
    if "高リスク" in query or "high risk" in query_lower:
        filters["risk_level"] = ["HIGH"]
    elif "中リスク" in query or "medium risk" in query_lower:
        filters["risk_level"] = ["MEDIUM"]
    
    # Execute query based on type
    try:
        if result_type == "tasks":
            data = bigquery.list_tasks_paginated(**filters, limit=20)
        elif result_type == "risks":
            data = bigquery.list_risks_paginated(**filters, limit=20)
        elif result_type == "decisions":
            data = bigquery.list_decisions_paginated(**filters, limit=20)
        else:
            data = bigquery.list_projects_paginated(limit=20)
        
        return {
            "type": result_type,
            "filters_applied": filters,
            "results": data.get("items", []),
            "total": data.get("total", 0)
        }
    except Exception as e:
        return {
            "type": result_type,
            "error": str(e),
            "results": [],
            "total": 0
        }


@router.post("/query")
def natural_language_query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process natural language query and return structured results.
    Examples:
    - "今週期限のタスクを見せて"
    - "高リスクの項目は？"
    - "Project Aの未完了タスク"
    """
    try:
        result = process_natural_language_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
def chat_with_ai(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat with AI about project status.
    AI has context about current tasks, risks, and projects.
    """
    if not VERTEX_AI_AVAILABLE:
        # Fallback response when Vertex AI is not available
        return {
            "response": "AI機能は現在利用できません。Vertex AIの設定を確認してください。",
            "context_used": False
        }
    
    try:
        model = GenerativeModel(GEMINI_MODEL)
        
        # Build system context
        system_context = get_system_context()
        
        # Build conversation history
        history_text = ""
        if request.history:
            for msg in request.history[-5:]:  # Last 5 messages
                role = "ユーザー" if msg.get("role") == "user" else "アシスタント"
                history_text += f"{role}: {msg.get('content', '')}\n"
        
        prompt = f"""あなたはプロジェクト管理アシスタントです。
以下のプロジェクト情報を参考に、ユーザーの質問に日本語で簡潔に回答してください。

{system_context}

会話履歴:
{history_text}

ユーザーの質問: {request.message}

回答（日本語で、簡潔に）:"""

        response = model.generate_content(prompt)
        
        return {
            "response": response.text,
            "context_used": True
        }
    except Exception as e:
        # Return error message but don't fail
        return {
            "response": f"申し訳ありません、エラーが発生しました: {str(e)}",
            "context_used": False
        }


@router.post("/agenda/generate")
def generate_agenda(
    request: AgendaRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate next meeting agenda based on unresolved items.
    """
    if not VERTEX_AI_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="AI機能は現在利用できません"
        )
    
    try:
        # Get unresolved items
        overdue_tasks = bigquery.get_overdue_tasks(limit=10, project_id=request.project_id)
        high_risks = bigquery.get_high_risks(limit=10, project_id=request.project_id)
        
        # Get recent decisions for context
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        recent_decisions = bigquery.get_recent_decisions(
            week_ago.isoformat(),
            today.isoformat(),
            limit=5
        )
        
        model = GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""以下の情報を元に、次回会議のアジェンダを作成してください。

## 期限超過タスク
{json.dumps([{"title": t.get("task_title"), "owner": t.get("owner"), "days_overdue": t.get("days_overdue")} for t in overdue_tasks], ensure_ascii=False, indent=2)}

## 高リスク項目
{json.dumps([{"description": r.get("risk_description"), "level": r.get("risk_level")} for r in high_risks], ensure_ascii=False, indent=2)}

## 先週の決定事項（フォローアップ用）
{json.dumps([d.get("decision_description", d.get("decision_content", "")) for d in recent_decisions], ensure_ascii=False, indent=2)}

アジェンダを以下の形式で作成してください：
1. 開会・前回決定事項の確認 (5分)
2. [議題1] - [想定時間]
3. [議題2] - [想定時間]
...
n. 次回予定・閉会 (5分)

各議題には簡単な説明も付けてください。"""

        response = model.generate_content(prompt)
        
        return {
            "agenda": response.text,
            "based_on": {
                "overdue_tasks_count": len(overdue_tasks),
                "high_risks_count": len(high_risks),
                "recent_decisions_count": len(recent_decisions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/bottleneck")
def analyze_bottlenecks(
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze project bottlenecks using AI.
    """
    if not VERTEX_AI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="AI機能は現在利用できません"
        )
    
    try:
        # Get data for analysis
        if project_id:
            tasks = bigquery.list_tasks_paginated(project_id=project_id, limit=50)
            risks = bigquery.list_risks_paginated(project_id=project_id, limit=20)
            stats = bigquery.get_project_stats(project_id)
        else:
            tasks = bigquery.list_tasks_paginated(limit=100)
            risks = bigquery.list_risks_paginated(limit=50)
            stats = None
        
        model = GenerativeModel(GEMINI_MODEL)
        
        # Prepare task summary
        task_summary = []
        for t in tasks.get("items", []):
            task_summary.append({
                "title": t.get("task_title"),
                "owner": t.get("owner"),
                "status": t.get("status"),
                "due_date": t.get("due_date"),
                "priority": t.get("priority")
            })
        
        risk_summary = []
        for r in risks.get("items", []):
            risk_summary.append({
                "description": r.get("risk_description"),
                "level": r.get("risk_level")
            })
        
        prompt = f"""以下のプロジェクトデータを分析し、ボトルネックと改善提案を日本語で提供してください。

## タスク一覧
{json.dumps(task_summary[:20], ensure_ascii=False, indent=2)}

## リスク一覧
{json.dumps(risk_summary[:10], ensure_ascii=False, indent=2)}

## 統計
{json.dumps(stats, ensure_ascii=False, indent=2) if stats else "全体分析"}

以下の観点で分析してください：
1. **ボトルネック**: 進捗を妨げている主な要因
2. **リスク評価**: 最も注意すべきリスク
3. **改善提案**: 具体的なアクション（3つ程度）
4. **優先度**: どこから手をつけるべきか

簡潔に、実用的な形式で回答してください。"""

        response = model.generate_content(prompt)
        
        return {
            "analysis": response.text,
            "data_summary": {
                "tasks_analyzed": len(task_summary),
                "risks_analyzed": len(risk_summary),
                "project_id": project_id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

