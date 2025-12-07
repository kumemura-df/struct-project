"""Gemini AI service for meeting notes extraction.

Features:
- Exponential backoff retry for transient failures
- Timeout handling
- Structured response validation
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, DeadlineExceeded

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("PROJECT_ID")
# Default: Gemini 2.5 Pro in us-central1 (can be overridden by env vars)
LOCATION = os.getenv("GEMINI_LOCATION", "us-central1")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# Retry configuration
MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
INITIAL_BACKOFF_SECONDS = float(os.getenv("GEMINI_INITIAL_BACKOFF", "1.0"))
MAX_BACKOFF_SECONDS = float(os.getenv("GEMINI_MAX_BACKOFF", "30.0"))
TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT", "120"))

_initialized = False


def _ensure_initialized():
    """Initialize Vertex AI if not already done."""
    global _initialized
    if not _initialized:
        if not PROJECT_ID:
            # Fail fast with clear error when PROJECT_ID is missing
            raise RuntimeError(
                "PROJECT_ID is not set. Vertex AI cannot be initialized. "
                "Make sure the Cloud Run service has PROJECT_ID in env vars."
            )

        vertexai.init(project=PROJECT_ID, location=LOCATION)
        _initialized = True


def is_available() -> bool:
    """Check if Gemini service is available."""
    try:
        _ensure_initialized()
        # Just check if we can create the model instance
        GenerativeModel(MODEL_NAME)
        return True
    except Exception as e:
        # Log at WARNING level so Cloud Run logs /ready failures clearly
        logger.warning(
            "Gemini availability check failed",
            extra={
                "error": str(e),
                "project_id": PROJECT_ID,
                "location": LOCATION,
                "model_name": MODEL_NAME,
            },
        )
        return False


# JSON Schema for structured output (Notion DB compatible)
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        # 会議情報
        "meeting": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "date": {"type": "string"},
                "summary": {"type": "string"},
                "participants": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["name", "date", "summary"]
        },
        # 論点（階層構造対応）
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["PURPOSE", "ISSUE", "SUB_ISSUE"]
                    },
                    "parent_issue_id": {"type": "string"},
                    "related_issue_ids": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "status": {
                        "type": "string",
                        "enum": ["OPEN", "IN_DISCUSSION", "RESOLVED", "DEFERRED"]
                    },
                    "description": {"type": "string"},
                    "source_sentence": {"type": "string"}
                },
                "required": ["id", "name", "type", "status"]
            }
        },
        # 意思決定（理由付き）
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "date": {"type": "string"},
                    "reason": {"type": "string"},
                    "related_issue_ids": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "decided_by": {"type": "string"},
                    "source_sentence": {"type": "string"}
                },
                "required": ["name", "reason", "source_sentence"]
            }
        },
        # アクション（担当者・期日・優先度）
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "owner": {"type": "string"},
                    "due_date": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                    },
                    "status": {
                        "type": "string",
                        "enum": ["NOT_STARTED", "IN_PROGRESS", "DONE", "BLOCKED"]
                    },
                    "related_issue_ids": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "source_sentence": {"type": "string"}
                },
                "required": ["name", "owner", "priority", "status"]
            }
        },
        # リスク（カテゴリ・重大度・軽減策）
        "risks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["SCHEDULE", "RESOURCE", "TECHNICAL", "EXTERNAL", "COST", "QUALITY", "OTHER"]
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                    },
                    "likelihood": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH"]
                    },
                    "mitigation": {"type": "string"},
                    "owner": {"type": "string"},
                    "related_issue_ids": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "source_sentence": {"type": "string"}
                },
                "required": ["name", "category", "severity", "source_sentence"]
            }
        },
        # 後方互換性のため projects も維持
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"}
                },
                "required": ["project_name"]
            }
        },
        # 後方互換性のため tasks も維持（actions と同期）
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "task_title": {"type": "string"},
                    "task_description": {"type": "string"},
                    "owner": {"type": "string"},
                    "due_date_text": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["NOT_STARTED", "IN_PROGRESS", "DONE", "UNKNOWN"]
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH"]
                    },
                    "source_sentence": {"type": "string"}
                },
                "required": ["task_title", "owner"]
            }
        }
    },
    "required": ["meeting", "issues", "decisions", "actions", "risks", "projects", "tasks"]
}


def _build_prompt(text: str, meeting_date: str) -> str:
    """Build the extraction prompt."""
    return f"""あなたは優秀なプロジェクト管理アシスタントです。
以下の議事録を、Notion データベースに格納できる構造化 JSON に変換してください。

会議日: {meeting_date}

---

## 出力構造（すべて必須）

### 1. meeting（会議情報）
会議のメタ情報を抽出:
- name: 会議名（推定可）
- date: 会議日（{meeting_date}）
- summary: 会議全体の要約（3-5文で）
- participants: 参加者リスト（言及された人名）

### 2. issues（論点）- 階層構造で抽出！
**論点は「目的 → 論点 → 小論点」の階層構造で分類してください。**

各論点に一意の id を付与（例: "issue-1", "issue-2"）:
- id: 一意の識別子
- name: 論点の名前（簡潔に）
- type: PURPOSE（目的/ゴール）, ISSUE（主要論点）, SUB_ISSUE（小論点/詳細）
- parent_issue_id: 親論点のid（最上位はnull）
- related_issue_ids: 関連する他の論点のidリスト
- status: OPEN（未解決）, IN_DISCUSSION（議論中）, RESOLVED（解決済み）, DEFERRED（保留）
- description: 詳細説明
- source_sentence: 原文

**論点抽出のコツ:**
- 「〜について」「〜の件」「〜の問題」→ 論点
- 「どうするか」「どう進めるか」→ 論点
- 議題、アジェンダ項目 → 論点
- 関連する論点同士は related_issue_ids でつなげる

### 3. decisions（意思決定）- 理由付きで抽出！
**決定事項は必ず「理由」とセットで抽出してください。**

- name: 決定内容（簡潔に）
- date: 決定日（{meeting_date}）
- reason: 決定の理由・背景（なぜその決定に至ったか）
- related_issue_ids: 関連する論点のidリスト
- decided_by: 決定者（わかれば）
- source_sentence: 原文

**決定事項のパターン:**
- 「〜に決定」「〜で合意」「〜することになった」
- 「〜で進める」「〜を採用」「〜に決めた」
- 「結論として〜」「最終的に〜」

### 4. actions（アクション）- 最重要！積極的に抽出！
**アクションは漏れなく抽出してください。少しでもやるべきことがあればアクションです。**

- name: アクション名（動詞で始める）
- description: 詳細説明
- owner: 担当者（不明なら "Unassigned"）
- due_date: 期限（"2025-12-15" 形式、または "来週金曜" など原文のまま）
- priority: LOW, MEDIUM, HIGH, CRITICAL
- status: NOT_STARTED, IN_PROGRESS, DONE, BLOCKED
- related_issue_ids: 関連する論点のidリスト
- source_sentence: 原文

**アクション抽出パターン（すべてチェック！）:**
- 「〜する」「〜します」「〜を行う」「〜を実施」
- 「〜を確認」「〜を調整」「〜を対応」「〜を検討」
- 「〜してください」「〜をお願い」「〜の依頼」
- 「〜が必要」「〜しなければ」「〜すべき」
- 「〜を進める」「〜を完了させる」「〜を準備」
- 「〜さんが担当」「〜さんにお願い」
- 暗黙的: 「田中さん、どうですか？」→ 田中さんのアクション

**優先度の判断基準:**
- CRITICAL: 緊急かつ重要、ブロッカー
- HIGH: 今週中、重要、影響大
- MEDIUM: 通常の作業
- LOW: いつでも良い、nice-to-have

### 5. risks（リスク）- カテゴリ・軽減策付きで抽出！
明示的・暗黙的なリスクを両方抽出:

- name: リスク名（簡潔に）
- description: リスクの詳細説明
- category: SCHEDULE（スケジュール）, RESOURCE（リソース）, TECHNICAL（技術）, EXTERNAL（外部要因）, COST（コスト）, QUALITY（品質）, OTHER（その他）
- severity: LOW, MEDIUM, HIGH, CRITICAL
- likelihood: LOW, MEDIUM, HIGH（発生可能性）
- mitigation: 軽減策・対応策（議論されていれば）
- owner: リスクオーナー
- related_issue_ids: 関連する論点のidリスト
- source_sentence: 原文

**リスク抽出パターン:**
- 明示的: 「リスク」「懸念」「問題」「課題」
- 暗黙的: 「心配」「厳しい」「間に合わない」「不明」「遅延」「難しい」

### 6. projects（プロジェクト）
議論されているプロジェクト・案件名を抽出:
- project_name: プロジェクト名

### 7. tasks（タスク）- 後方互換性用
actionsと同じ内容をtasks形式でも出力:
- task_title: アクション名
- task_description: 詳細
- owner: 担当者
- due_date_text: 期限
- status: NOT_STARTED, IN_PROGRESS, DONE, UNKNOWN
- priority: LOW, MEDIUM, HIGH
- source_sentence: 原文
- project_name: 関連プロジェクト

---

## 議事録

{text}

---

## 重要な注意事項

1. **論点は階層構造で**: PURPOSE → ISSUE → SUB_ISSUE
2. **決定には必ず理由を**: なぜその決定に至ったか
3. **アクションは漏れなく**: 少しでもやることがあれば抽出
4. **リスクには軽減策を**: 議論されていれば記載
5. **関連付けを忘れずに**: related_issue_ids で論点とつなげる
6. **重複は統合**: 同じ内容は1つにまとめる
7. **source_sentenceは必ず**: 原文を必ず記載

必ず指定されたJSONスキーマに従って出力してください。"""


def extract_info(text: str, meeting_date: str) -> Dict[str, Any]:
    """Extract structured information from meeting notes.
    
    Args:
        text: Meeting notes text content
        meeting_date: Date of the meeting (YYYY-MM-DD format)
        
    Returns:
        Dict with projects, tasks, risks, and decisions
        
    Raises:
        Exception: On Gemini API errors
    """
    _ensure_initialized()
    
    model = GenerativeModel(MODEL_NAME)
    prompt = _build_prompt(text, meeting_date)
    
    generation_config = GenerationConfig(
        response_mime_type="application/json",
        response_schema=EXTRACTION_SCHEMA,
        temperature=0.1,  # Low temperature for consistent extraction
        max_output_tokens=8192,
    )
    
    response = model.generate_content(
        prompt,
        generation_config=generation_config,
    )
    
    result = json.loads(response.text)
    
    # Validate and sanitize output
    return _validate_and_sanitize(result)


def extract_info_with_retry(text: str, meeting_date: str) -> Dict[str, Any]:
    """Extract info with exponential backoff retry.
    
    Args:
        text: Meeting notes text content
        meeting_date: Date of the meeting
        
    Returns:
        Extracted data dictionary
        
    Raises:
        Exception: After all retries exhausted
    """
    last_exception: Optional[Exception] = None
    backoff = INITIAL_BACKOFF_SECONDS
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            return extract_info(text, meeting_date)
            
        except (ResourceExhausted, ServiceUnavailable, DeadlineExceeded) as e:
            last_exception = e
            
            if attempt < MAX_RETRIES:
                # Log retry attempt
                logger.warning(
                    f"Gemini API error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {backoff:.1f}s..."
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
            else:
                logger.error(f"Gemini API error after {MAX_RETRIES + 1} attempts: {e}")
                
        except json.JSONDecodeError as e:
            # JSON parsing error - might be a model issue, retry with backoff
            last_exception = e
            
            if attempt < MAX_RETRIES:
                logger.warning(
                    f"JSON decode error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {backoff:.1f}s..."
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
            else:
                logger.error(f"JSON decode error after {MAX_RETRIES + 1} attempts: {e}")
                
        except Exception as e:
            # Unexpected errors - don't retry
            logger.error(f"Unexpected Gemini error: {e}")
            raise
    
    # All retries exhausted
    raise last_exception or Exception("Gemini extraction failed after retries")


def _validate_and_sanitize(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize extracted data.
    
    Ensures all required fields exist and have valid values.
    Supports both new Notion-compatible schema and legacy schema.
    """
    # Ensure all top-level structures exist
    result = {
        # New Notion-compatible structure
        "meeting": data.get("meeting", {
            "name": "会議",
            "date": "",
            "summary": "",
            "participants": []
        }),
        "issues": data.get("issues", []),
        "decisions": data.get("decisions", []),
        "actions": data.get("actions", []),
        "risks": data.get("risks", []),
        # Legacy structure (for backward compatibility)
        "projects": data.get("projects", []),
        "tasks": data.get("tasks", []),
    }
    
    # Sanitize meeting
    meeting = result["meeting"]
    meeting["name"] = meeting.get("name", "会議")
    meeting["date"] = meeting.get("date", "")
    meeting["summary"] = meeting.get("summary", "")
    meeting["participants"] = meeting.get("participants", [])
    
    # Sanitize issues
    for i, issue in enumerate(result["issues"]):
        issue["id"] = issue.get("id", f"issue-{i+1}")
        issue["name"] = issue.get("name", "Untitled Issue")
        issue["type"] = issue.get("type", "ISSUE")
        issue["status"] = issue.get("status", "OPEN")
        issue["parent_issue_id"] = issue.get("parent_issue_id")
        issue["related_issue_ids"] = issue.get("related_issue_ids", [])
        issue["description"] = issue.get("description", "")
        issue["source_sentence"] = issue.get("source_sentence", "")
        
        # Validate enums
        if issue["type"] not in ["PURPOSE", "ISSUE", "SUB_ISSUE"]:
            issue["type"] = "ISSUE"
        if issue["status"] not in ["OPEN", "IN_DISCUSSION", "RESOLVED", "DEFERRED"]:
            issue["status"] = "OPEN"
    
    # Sanitize decisions (new format)
    for decision in result["decisions"]:
        decision["name"] = decision.get("name") or decision.get("decision_content", "")
        decision["date"] = decision.get("date", "")
        decision["reason"] = decision.get("reason", "")
        decision["related_issue_ids"] = decision.get("related_issue_ids", [])
        decision["decided_by"] = decision.get("decided_by", "")
        decision["source_sentence"] = decision.get("source_sentence", "")
        # Legacy compatibility
        decision["decision_content"] = decision["name"]
    
    # Sanitize actions
    for action in result["actions"]:
        action["name"] = action.get("name", "Untitled Action")
        action["description"] = action.get("description", "")
        action["owner"] = action.get("owner", "Unassigned")
        action["due_date"] = action.get("due_date", "")
        action["priority"] = action.get("priority", "MEDIUM")
        action["status"] = action.get("status", "NOT_STARTED")
        action["related_issue_ids"] = action.get("related_issue_ids", [])
        action["source_sentence"] = action.get("source_sentence", "")
        
        # Validate enums
        if action["priority"] not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            action["priority"] = "MEDIUM"
        if action["status"] not in ["NOT_STARTED", "IN_PROGRESS", "DONE", "BLOCKED"]:
            action["status"] = "NOT_STARTED"
    
    # Sanitize risks (new format)
    for risk in result["risks"]:
        risk["name"] = risk.get("name") or risk.get("risk_description", "")
        risk["description"] = risk.get("description") or risk.get("risk_description", "")
        risk["category"] = risk.get("category", "OTHER")
        risk["severity"] = risk.get("severity") or risk.get("risk_level", "MEDIUM")
        risk["likelihood"] = risk.get("likelihood", "MEDIUM")
        risk["mitigation"] = risk.get("mitigation", "")
        risk["owner"] = risk.get("owner", "")
        risk["related_issue_ids"] = risk.get("related_issue_ids", [])
        risk["source_sentence"] = risk.get("source_sentence", "")
        # Legacy compatibility
        risk["risk_description"] = risk["description"]
        risk["risk_level"] = risk["severity"]
        
        # Validate enums
        if risk["category"] not in ["SCHEDULE", "RESOURCE", "TECHNICAL", "EXTERNAL", "COST", "QUALITY", "OTHER"]:
            risk["category"] = "OTHER"
        if risk["severity"] not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            risk["severity"] = "MEDIUM"
        if risk["likelihood"] not in ["LOW", "MEDIUM", "HIGH"]:
            risk["likelihood"] = "MEDIUM"
    
    # Sanitize tasks (legacy format)
    for task in result["tasks"]:
        task["task_title"] = task.get("task_title", "Untitled Task")
        task["task_description"] = task.get("task_description", "")
        task["owner"] = task.get("owner", "Unassigned")
        task["due_date_text"] = task.get("due_date_text", "")
        task["status"] = task.get("status", "UNKNOWN")
        task["priority"] = task.get("priority", "MEDIUM")
        task["source_sentence"] = task.get("source_sentence", "")
        task["project_name"] = task.get("project_name", "")
        
        # Validate enums
        if task["status"] not in ["NOT_STARTED", "IN_PROGRESS", "DONE", "UNKNOWN"]:
            task["status"] = "UNKNOWN"
        if task["priority"] not in ["LOW", "MEDIUM", "HIGH"]:
            task["priority"] = "MEDIUM"
    
    # If tasks is empty but actions exists, populate tasks from actions
    if not result["tasks"] and result["actions"]:
        for action in result["actions"]:
            result["tasks"].append({
                "task_title": action["name"],
                "task_description": action["description"],
                "owner": action["owner"],
                "due_date_text": action["due_date"],
                "status": action["status"] if action["status"] != "BLOCKED" else "UNKNOWN",
                "priority": action["priority"] if action["priority"] != "CRITICAL" else "HIGH",
                "source_sentence": action["source_sentence"],
                "project_name": "",
            })
    
    return result
