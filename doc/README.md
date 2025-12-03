# Project Progress DB - 設計ドキュメント

## 概要

本ディレクトリは、Project Progress DB システムの設計・実装ドキュメントを体系的に管理する。

### システム概要

**Project Progress DB** は、会議議事録から AI を活用してタスク・リスク・決定事項を自動抽出し、プロジェクト進捗を可視化するシステムである。

### 想定ユーザー

| ユーザー | 役割 | 主な利用機能 |
|----------|------|-------------|
| PM / PMO | プロジェクト管理者 | 全機能（アップロード、ダッシュボード、レポート、エクスポート） |
| Member | プロジェクトメンバー | ダッシュボード閲覧、タスク確認 |
| Executive | 経営層 | ダッシュボード閲覧、リスク確認 |

### 提供価値

1. **時間削減**: 議事録からのタスク抽出を自動化
2. **可視化**: プロジェクト横断でのリスク・遅延タスクを一元管理
3. **トレーサビリティ**: 抽出元文（発言）を保持し、根拠を明確化

---

## ドキュメント構成

### 1. 企画・要件定義フェーズ

| # | ドキュメント | ファイル | 概要 |
|---|-------------|---------|------|
| 1.1 | 機能一覧 | [1_requirements_spec.md](1_requirements/1_requirements_spec.md#11-feature-list) | システム機能の一覧 |
| 1.2 | 機能要求 | [1_requirements_spec.md](1_requirements/1_requirements_spec.md#12-functional-requirements) | 機能の詳細仕様 |
| 1.3 | 非機能要求 | [1_requirements_spec.md](1_requirements/1_requirements_spec.md#13-non-functional-requirements) | パフォーマンス、セキュリティ等 |
| 2.1 | ユースケース図 | [2_use_case_def.md](1_requirements/2_use_case_def.md#21-use-case-diagram) | アクターとシステムの関係 |
| 2.2 | ユースケース記述 | [2_use_case_def.md](1_requirements/2_use_case_def.md#22-use-case-descriptions) | 各ユースケースのシナリオ |

### 2. 設計フェーズ

#### 2.1. アーキテクチャ・全体設計

| # | ドキュメント | ファイル | 概要 |
|---|-------------|---------|------|
| 3.1 | 技術スタック | [3_architecture.md](2_design/3_architecture.md#31-technology-stack) | 言語・フレームワーク選定 |
| 3.2 | システム構成図 | [3_architecture.md](2_design/3_architecture.md#32-system-configuration-diagram) | インフラ構成 |
| 3.3 | 接続パターン一覧 | [3_architecture.md](2_design/3_architecture.md#33-connection-patterns) | コンポーネント間連携方式 |

#### 2.2. データ・静的構造設計

| # | ドキュメント | ファイル | 概要 |
|---|-------------|---------|------|
| 4.1 | ドメインモデル | [4_data_model.md](2_design/4_data_model.md#41-domain-model-conceptual) | 概念モデル（クラス図） |
| 4.2 | データ定義書 | [4_data_model.md](2_design/4_data_model.md#42-data-dictionary-detailed) | データディクショナリ |
| 5.1 | ER図 | [5_database_design.md](2_design/5_database_design.md#51-er-diagram) | エンティティ関連図 |
| 5.2 | テーブル定義書 | [5_database_design.md](2_design/5_database_design.md#52-table-definitions-bigquery) | 物理テーブル設計 |
| 6.1 | クラス図（静的構造） | [6_object_design_static.md](2_design/6_object_design_static.md) | バックエンド・フロントエンド設計 |

#### 2.3. 動的振る舞い・プロセス設計

| # | ドキュメント | ファイル | 概要 |
|---|-------------|---------|------|
| 7.1 | ユーザーフロー図 | [7_process_flow.md](2_design/7_process_flow.md#71-user-flow-diagram) | 画面遷移・操作フロー |
| 7.2 | アクティビティ図 | [7_process_flow.md](2_design/7_process_flow.md#72-activity-diagram-analysis-process) | 処理フロー |
| 8.1 | シーケンス図 | [8_object_design_dynamic.md](2_design/8_object_design_dynamic.md#81-sequence-diagram-upload--analysis) | メッセージシーケンス |
| 8.2 | 状態マシン図 | [8_object_design_dynamic.md](2_design/8_object_design_dynamic.md#82-state-machine-diagram-meeting-status) | 状態遷移 |

### 3. 実装・テスト・移行フェーズ

| # | ドキュメント | ファイル | 概要 |
|---|-------------|---------|------|
| 9.1 | コーディング規約 | [9_coding_standards.md](3_implementation/9_coding_standards.md) | 命名規則、スタイルガイド |
| 10.1 | テスト計画書 | [10_test_documentation.md](3_implementation/10_test_documentation.md#101-テスト計画書) | テスト方針・スケジュール |
| 10.2 | テスト仕様書 | [10_test_documentation.md](3_implementation/10_test_documentation.md#102-テスト仕様書) | テスト観点 |
| 10.3 | テストケース | [10_test_documentation.md](3_implementation/10_test_documentation.md#103-テストケース) | 具体的なテスト手順 |
| 11.1 | 本番データ化処理仕様書 | [11_migration_spec.md](3_implementation/11_migration_spec.md) | データ移行・初期化手順 |

### 4. 運用フェーズ

| # | ドキュメント | ファイル | 概要 |
|---|-------------|---------|------|
| 12.1 | デプロイメントガイド | [12_deployment_guide.md](4_operations/12_deployment_guide.md) | デプロイ手順書 |
| 13.1 | 運用手順書 | [13_operations_runbook.md](4_operations/13_operations_runbook.md) | 障害対応・日常運用 |

---

## クイックリファレンス

### 画面遷移（ユーザーフロー）

```
ログイン → ダッシュボード → プロジェクト詳細
                ↓
          アップロード → 処理中 → 完了
                ↓
          リスク一覧 → フィルタ
                ↓
          エクスポート → CSV ダウンロード
```

### 主要エンティティ関係

```
Meeting ──┬── 1:N ──→ Task
          ├── 1:N ──→ Risk
          └── 1:N ──→ Decision

Project ──┬── 1:N ──→ Task
          └── 1:N ──→ Risk
```

### 技術スタック概要

| 層 | 技術 |
|---|------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend API | FastAPI, Python 3.9 |
| Worker | Flask, Pub/Sub |
| Database | BigQuery |
| Storage | Cloud Storage |
| AI | Vertex AI (Gemini 1.5 Flash) |
| Infra | Cloud Run, Terraform |

---

## ドキュメント間の整合性

### エンティティ定義の一貫性

以下のドキュメントで同一のエンティティ定義を使用:

- `4_data_model.md` - 概念・論理モデル
- `5_database_design.md` - 物理テーブル定義
- `backend/api/schemas.py` - Pydantic スキーマ

### ステータス値の一貫性

| エンティティ | ステータス値 | 定義場所 |
|-------------|-------------|---------|
| Meeting.status | PENDING, PROCESSING, DONE, ERROR | データ定義書 4.2 |
| Task.status | NOT_STARTED, IN_PROGRESS, DONE, BLOCKED | データ定義書 4.2 |
| Task.priority | LOW, MEDIUM, HIGH | データ定義書 4.2 |
| Risk.risk_level | LOW, MEDIUM, HIGH | データ定義書 4.2 |

### API エンドポイントとユースケースの対応

| ユースケース | API エンドポイント |
|-------------|-------------------|
| UC-01: アップロード | POST /upload/ |
| UC-02: ダッシュボード | GET /projects/, GET /tasks/ |
| UC-03: タスク確認 | GET /tasks/?status=OVERDUE |
| UC-04: レポート生成 | (将来対応) |
| エクスポート | GET /export/csv/tasks |

---

## 更新履歴

| 日付 | 更新内容 | 担当 |
|------|---------|------|
| 2024-12-03 | 初版作成（全ドキュメント体系化） | - |
