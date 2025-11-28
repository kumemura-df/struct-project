# Project Progress DB & Risk Dashboard

このプロジェクトは、Gemini (Vertex AI) を使用して会議の議事録からプロジェクトのステータス、タスク、リスクを自動的に抽出し、ダッシュボードで可視化するツールです。

## デプロイ先
**URL**: [https://project-progress-frontend-prod-29226667525.asia-northeast1.run.app](https://project-progress-frontend-prod-29226667525.asia-northeast1.run.app)

## 現在のスペック・実現できること
- **会議議事録のアップロード**: テキストファイル(.txt, .md)をアップロードし、解析を開始できます。
- **AIによる自動抽出**: Gemini (Vertex AI) が議事録から以下の情報を自動抽出します。
    - プロジェクトの進捗状況
    - タスク（担当者、期限付き）
    - リスク（レベル、説明付き）
    - 決定事項
- **プロジェクト進捗ダッシュボード**: プロジェクトごとのタスク一覧や進捗を可視化します。
- **リスク分析ダッシュボード**: 全プロジェクトのリスクをレベル別（高・中・低）に集計・表示し、フィルタリングできます。
- **データエクスポート**: プロジェクト、タスク、リスクの一覧をCSV形式でダウンロードできます。

## 現在の開発状況
- **MVPリリース済み**: 基本的な機能（アップロード、抽出、表示、エクスポート）は実装完了しています。
- **日本語化対応完了**: UIおよびドキュメントは全て日本語化されています。
- **本番環境デプロイ完了**: Cloud Runへのデプロイ、OAuth認証設定、リダイレクト設定が完了し、稼働中です。
- **E2Eテスト実装済み**: 主要なユースケース（アップロード〜データ確認）の自動テストが整備されています。

## アーキテクチャ

```mermaid
graph TD
    User[ユーザー] -->|議事録アップロード| Frontend[Next.js フロントエンド]
    Frontend -->|POST /upload| API[FastAPI バックエンド (Cloud Run)]
    API -->|メタデータ保存| BigQuery[(BigQuery)]
    API -->|ファイルアップロード| GCS[(Cloud Storage)]
    GCS -->|トリガー| PubSub[Pub/Sub]
    PubSub -->|プッシュ| Worker[ワーカーサービス (Cloud Run)]
    Worker -->|ファイル読み込み| GCS
    Worker -->|情報抽出| Gemini[Vertex AI (Gemini)]
    Worker -->|データ保存| BigQuery
    Frontend -->|データ読み込み| API
```

## 技術スタック

- **フロントエンド**: Next.js, Tailwind CSS
- **バックエンド**: Python (FastAPI), Flask (Worker)
- **インフラ**: Google Cloud Platform (Cloud Run, BigQuery, Cloud Storage, Pub/Sub, Vertex AI)
- **IaC**: Terraform

## セットアップ

### 前提条件

- 課金が有効な Google Cloud プロジェクト
- `gcloud` CLI のインストールと認証済み
- `terraform` のインストール
- Python 3.11以上
- Node.js 18以上

### ローカル開発

1. **バックエンド (API)**
   ```bash
   cd backend/api
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   # 環境変数を設定してください (.env.example 参照)
   uvicorn main:app --reload
   ```

2. **フロントエンド**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## デプロイ

Terraformを使用してデプロイします。

```bash
cd terraform
terraform init
terraform apply
```

### OAuth認証の設定 (本番環境)

本番環境でGoogleログインを使用するには、Google Cloud ConsoleでOAuthクライアントIDを作成し、Secret Managerに登録する必要があります。

1. **Google Cloud Console** で「OAuth クライアント ID」を作成（ウェブアプリケーション）。
2. **承認済みのリダイレクト URI** に以下を設定:
   `https://[API_SERVICE_URL]/auth/callback`
   (例: `https://project-progress-api-prod-29226667525.asia-northeast1.run.app/auth/callback`)
3. 取得したクライアントIDとシークレットをSecret Managerに登録:
   ```bash
   printf "YOUR_CLIENT_ID" | gcloud secrets versions add oauth-client-id --data-file=- --project=[PROJECT_ID]
   printf "YOUR_CLIENT_SECRET" | gcloud secrets versions add oauth-client-secret --data-file=- --project=[PROJECT_ID]
   ```
4. APIサービスを再デプロイして設定を反映させます。

## 使い方

### 1. 議事録のアップロード
1. トップページの「議事録アップロード」ボタンをクリックします。
2. 会議日を選択し、タイトル（任意）を入力します。
3. 議事録ファイル（.txt または .md）を選択し、「議事録をアップロード」ボタンをクリックします。
4. アップロードが完了すると、自動的にAIによる解析が始まります。

### 2. ダッシュボードの確認
1. 解析が完了すると、トップページのダッシュボードにプロジェクト一覧が表示されます。
2. プロジェクトを選択すると、関連するタスクが表示されます。
3. 「エクスポート」ボタンから、プロジェクトやタスクの一覧をCSV形式でダウンロードできます。

### 3. リスクの確認
1. トップページの「リスクダッシュボード」ボタンをクリックします。
2. 抽出されたリスク一覧が表示されます。
3. プロジェクトやリスクレベル（高・中・低）でフィルタリングが可能です。

## テスト

### E2Eテスト
デプロイされた環境に対してE2Eテストを実行するには：

```bash
python3 e2e_test.py
```

### ユニットテスト
```bash
cd backend/api
pytest
```
