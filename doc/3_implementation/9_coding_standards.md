# 9. コーディング規約

## 9.1. 概要

本規約は、Project Progress DB システムの開発における統一的なコーディングスタイルを定義し、コードの可読性・保守性を高めることを目的とする。

---

## 9.2. 共通規約

### ファイル・エンコーディング

- 文字コード: **UTF-8**（BOMなし）
- 改行コード: **LF**（Unix形式）
- インデント: **スペース**（タブ禁止）

### 命名規則（全般）

| 対象 | 規則 | 例 |
|------|------|-----|
| ファイル名 | snake_case（Python）, kebab-case（TypeScript） | `bigquery_client.py`, `upload-form.tsx` |
| ディレクトリ名 | 小文字、ハイフン区切り | `routers`, `components` |
| 定数 | UPPER_SNAKE_CASE | `MAX_FILE_SIZE`, `API_TIMEOUT` |
| 環境変数 | UPPER_SNAKE_CASE | `GCP_PROJECT_ID`, `JWT_SECRET_KEY` |

### コメント

- 複雑なロジックには必ずコメントを付与
- コメントは「なぜ」を説明する（「何を」はコードで表現）
- TODO/FIXME コメントには担当者と期限を記載

```python
# Bad: 何をしているか（コードを読めばわかる）
# リストをループする
for item in items:
    process(item)

# Good: なぜそうしているか
# パフォーマンス最適化のため、バッチサイズを100に制限
for batch in chunks(items, 100):
    process_batch(batch)
```

---

## 9.3. Python（Backend）規約

### スタイルガイド

- 基本: **PEP 8** 準拠
- フォーマッター: **Black** (line-length: 88)
- リンター: **flake8**, **mypy**

### インデント・行長

- インデント: **4スペース**
- 最大行長: **88文字**（Blackデフォルト）

### 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| 変数 | snake_case | `meeting_date`, `task_list` |
| 関数 | snake_case | `get_projects()`, `upload_file()` |
| クラス | PascalCase | `BigQueryClient`, `MeetingService` |
| モジュール | snake_case | `bigquery_client.py` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRIES = 3` |
| プライベート | アンダースコアプレフィックス | `_internal_method()` |

### 型ヒント

- すべての関数に型ヒントを付与
- `Optional`, `List`, `Dict` などを使用
- 複雑な型は `TypeAlias` を定義

```python
from typing import List, Optional
from datetime import date

def get_tasks(
    project_id: str,
    status: Optional[str] = None,
    due_before: Optional[date] = None
) -> List[dict]:
    """タスク一覧を取得する"""
    ...
```

### インポート順序

1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール

各グループは1行空けて区切る。

```python
import os
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from google.cloud import bigquery

from ..services.bigquery_client import BigQueryClient
from ..auth.jwt import get_current_user
```

### 例外処理

- 具体的な例外クラスを捕捉（`except Exception` は避ける）
- カスタム例外はビジネスロジックに応じて定義

```python
# Bad
try:
    result = api_call()
except Exception as e:
    print(e)

# Good
try:
    result = api_call()
except TimeoutError:
    logger.warning("API timeout, retrying...")
    result = api_call_with_retry()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

### ログ出力

- `logging` モジュールを使用
- 適切なログレベルを選択

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed debug info")
logger.info("Processing file: %s", filename)
logger.warning("Retry attempt %d", attempt)
logger.error("Failed to process: %s", error)
```

---

## 9.4. TypeScript/React（Frontend）規約

### スタイルガイド

- 基本: **ESLint** 推奨設定
- フォーマッター: **Prettier**
- フレームワーク: **Next.js App Router**

### インデント・行長

- インデント: **2スペース**
- 最大行長: **100文字**

### 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| 変数 | camelCase | `meetingDate`, `taskList` |
| 関数 | camelCase | `getProjects()`, `handleSubmit()` |
| コンポーネント | PascalCase | `UploadForm`, `TaskList` |
| ファイル（コンポーネント） | PascalCase.tsx | `UploadForm.tsx` |
| ファイル（ユーティリティ） | camelCase.ts | `api.ts`, `auth.ts` |
| 型/インターフェース | PascalCase | `Task`, `MeetingData` |
| 定数 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| Hooks | use + PascalCase | `useAuth`, `useFetchTasks` |

### コンポーネント構造

```tsx
// 1. インポート
import { useState, useEffect } from 'react';
import type { Task } from '@/types';

// 2. 型定義
interface Props {
  projectId: string;
  onSelect: (task: Task) => void;
}

// 3. コンポーネント定義
export function TaskList({ projectId, onSelect }: Props) {
  // 3.1. State
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  // 3.2. Effects
  useEffect(() => {
    fetchTasks(projectId).then(setTasks);
  }, [projectId]);

  // 3.3. Handlers
  const handleClick = (task: Task) => {
    onSelect(task);
  };

  // 3.4. Render
  if (loading) return <LoadingSpinner />;

  return (
    <ul>
      {tasks.map(task => (
        <li key={task.task_id} onClick={() => handleClick(task)}>
          {task.task_title}
        </li>
      ))}
    </ul>
  );
}
```

### 型定義

- `interface` を優先（拡張性のため）
- API レスポンスの型は `types/` に集約

```typescript
// types/index.ts
export interface Task {
  task_id: string;
  task_title: string;
  owner: string | null;
  due_date: string | null;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'DONE';
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface Project {
  project_id: string;
  project_name: string;
  updated_at: string;
}
```

### アクセシビリティ

- `button` には `aria-label` を付与
- フォーム要素には `label` を関連付け
- 色のみで情報を伝えない（アイコン・テキスト併用）

---

## 9.5. SQL（BigQuery）規約

### フォーマット

- キーワード: **大文字**（`SELECT`, `FROM`, `WHERE`）
- テーブル/カラム名: **小文字**（`meetings`, `task_id`）
- インデント: **2スペース**

### クエリ構造

```sql
SELECT
  t.task_id,
  t.task_title,
  t.owner,
  t.due_date,
  p.project_name
FROM
  `project_progress.tasks` AS t
INNER JOIN
  `project_progress.projects` AS p
  ON t.project_id = p.project_id
WHERE
  t.status = 'IN_PROGRESS'
  AND t.due_date < CURRENT_DATE()
ORDER BY
  t.due_date ASC
LIMIT 100;
```

### 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| テーブル名 | 複数形、snake_case | `meetings`, `tasks` |
| カラム名 | snake_case | `meeting_id`, `created_at` |
| エイリアス | 1〜2文字略語 | `t` (tasks), `p` (projects) |

---

## 9.6. Terraform（IaC）規約

### ファイル構成

```
terraform/
├── provider.tf      # プロバイダ設定
├── variables.tf     # 入力変数
├── outputs.tf       # 出力値
├── bigquery.tf      # BigQueryリソース
├── cloudrun.tf      # Cloud Runリソース
├── iam.tf           # IAM設定
└── ...
```

### 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| リソース名 | snake_case | `google_bigquery_table.meetings` |
| 変数名 | snake_case | `project_id`, `region` |
| ローカル値 | snake_case | `local.service_name` |

### リソース定義

```hcl
resource "google_bigquery_table" "meetings" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "meetings"

  schema = jsonencode([
    {
      name = "meeting_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    # ...
  ])

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}
```

---

## 9.7. Git 規約

### ブランチ命名

| ブランチ種別 | 命名規則 | 例 |
|-------------|---------|-----|
| 機能開発 | `feature/{issue-id}-{description}` | `feature/123-add-csv-export` |
| バグ修正 | `fix/{issue-id}-{description}` | `fix/456-auth-error` |
| リリース | `release/{version}` | `release/1.2.0` |
| ホットフィックス | `hotfix/{issue-id}` | `hotfix/789` |

### コミットメッセージ

**形式:**
```
{type}: {subject}

{body}

{footer}
```

**type の種類:**
| type | 説明 |
|------|------|
| feat | 新機能 |
| fix | バグ修正 |
| docs | ドキュメント |
| style | フォーマット修正 |
| refactor | リファクタリング |
| test | テスト追加・修正 |
| chore | ビルド・CI設定 |

**例:**
```
feat: CSVエクスポート機能を追加

- タスク一覧のCSVダウンロード機能を実装
- リスク一覧のCSVダウンロード機能を実装

Closes #123
```

---

## 9.8. セキュリティ規約

### 禁止事項

- シークレット（API キー、パスワード）のハードコーディング
- ログへの機密情報出力
- SQLインジェクションに脆弱なクエリ構築

### 必須事項

- シークレットは Secret Manager 経由で取得
- ユーザー入力は必ずバリデーション
- 認証トークンの有効期限設定

```python
# Bad
API_KEY = "sk-xxxxx"  # ハードコード禁止

# Good
import os
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

---

## 9.9. コードレビュー基準

### 必須チェック項目

- [ ] 命名規則に準拠しているか
- [ ] 型ヒント/型定義があるか
- [ ] エラーハンドリングが適切か
- [ ] テストが追加されているか
- [ ] セキュリティリスクはないか
- [ ] パフォーマンス問題はないか

### レビュー観点

1. **正確性**: 要件を満たしているか
2. **可読性**: コードが理解しやすいか
3. **保守性**: 変更しやすい構造か
4. **効率性**: 無駄な処理がないか
5. **テスト容易性**: テストが書きやすいか
