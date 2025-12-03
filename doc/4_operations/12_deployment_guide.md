# 12. デプロイメントガイド

## 12.1. 概要

本ドキュメントでは、Project Progress DB システムの各環境へのデプロイ手順を説明します。

### 対象環境

| 環境 | 用途 | デプロイトリガー |
|------|------|----------------|
| dev | ローカル開発 | 手動 |
| staging | 本番前検証 | main ブランチへのプッシュ |
| prod | 本番運用 | バージョンタグ (v*.*.*)プッシュ |

---

## 12.2. 前提条件

### 必要なツール

```bash
# gcloud CLI のインストール確認
gcloud --version

# Terraform のインストール確認
terraform --version

# Docker のインストール確認
docker --version
```

### GCP プロジェクト設定

```bash
# プロジェクト ID の設定
export PROJECT_ID=your-gcp-project-id
gcloud config set project $PROJECT_ID

# 必要な API の有効化
gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  pubsub.googleapis.com \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com
```

### 認証情報の準備

1. **OAuth Client ID/Secret の作成**
   - Google Cloud Console > APIs & Services > Credentials
   - 「Create Credentials」 > 「OAuth client ID」
   - Application type: Web application
   - Authorized redirect URIs: `https://[API_URL]/auth/callback`

2. **Secret Manager への登録**
   ```bash
   # JWT シークレットキーの生成・登録
   python3 -c "import secrets; print(secrets.token_urlsafe(32))" | \
     gcloud secrets versions add jwt-secret-key --data-file=-
   
   # OAuth クライアント ID の登録
   echo -n "YOUR_CLIENT_ID" | \
     gcloud secrets versions add oauth-client-id --data-file=-
   
   # OAuth クライアントシークレットの登録
   echo -n "YOUR_CLIENT_SECRET" | \
     gcloud secrets versions add oauth-client-secret --data-file=-
   ```

---

## 12.3. 初回デプロイ（インフラ構築）

### Step 1: Terraform によるインフラ構築

```bash
cd terraform

# 初期化
terraform init

# プラン確認（Staging）
terraform plan -var="project_id=$PROJECT_ID" \
  -var-file=environments/staging.tfvars

# 適用
terraform apply -var="project_id=$PROJECT_ID" \
  -var-file=environments/staging.tfvars
```

### Step 2: Docker イメージのビルド・プッシュ

```bash
# Artifact Registry への認証
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージのビルド
make docker-build

# イメージのプッシュ
make docker-push
```

### Step 3: Cloud Run サービスのデプロイ

```bash
# 全サービスのデプロイ
make deploy-all
```

### Step 4: OAuth リダイレクト URI の更新

デプロイ後、取得した API URL を OAuth の Authorized redirect URI に追加:

```
https://project-progress-api-staging-xxxxx.run.app/auth/callback
```

---

## 12.4. 継続的デプロイ（CI/CD）

### Staging 環境への自動デプロイ

1. `main` ブランチにコードをプッシュ
2. Cloud Build が自動でトリガー
3. `cloudbuild-staging.yaml` に従ってデプロイ

```bash
git checkout main
git merge feature/your-feature
git push origin main
# → Staging への自動デプロイ開始
```

### Production 環境へのデプロイ

1. Staging での検証完了後、バージョンタグを付与
2. Cloud Build が自動でトリガー
3. `cloudbuild-prod.yaml` に従ってデプロイ

```bash
# バージョンタグの作成
git tag v1.0.0 -m "Release v1.0.0"

# タグのプッシュ → Production デプロイ開始
git push origin v1.0.0
```

---

## 12.5. 手動デプロイ

### 特定サービスのみデプロイ

```bash
# API のみ
make deploy-api

# Worker のみ
make deploy-worker

# Frontend のみ
make deploy-frontend
```

### 特定バージョンへのロールバック

```bash
# 利用可能なリビジョンの確認
gcloud run revisions list --service=project-progress-api-prod --region=asia-northeast1

# 特定リビジョンへのトラフィック切り替え
gcloud run services update-traffic project-progress-api-prod \
  --region=asia-northeast1 \
  --to-revisions=project-progress-api-prod-00005-abc=100
```

---

## 12.6. デプロイ後の検証

### ヘルスチェック

```bash
# API
curl https://project-progress-api-prod-xxxxx.run.app/

# 期待レスポンス
# {"message": "Project Progress DB API is running", "version": "1.0.0"}
```

### E2E テスト

```bash
python e2e_test.py
```

### 手動検証チェックリスト

- [ ] ログインが正常に動作する
- [ ] ファイルアップロードが成功する
- [ ] AI 処理が完了する（ステータスが DONE になる）
- [ ] ダッシュボードにデータが表示される
- [ ] CSV エクスポートが動作する

---

## 12.7. トラブルシューティング

### ビルドエラー

```bash
# Cloud Build ログの確認
gcloud builds list --limit=5
gcloud builds log [BUILD_ID]
```

### デプロイエラー

```bash
# Cloud Run サービス状態の確認
gcloud run services describe project-progress-api-prod \
  --region=asia-northeast1

# ログの確認
gcloud run logs read project-progress-api-prod \
  --region=asia-northeast1 --limit=50
```

### シークレットエラー

```bash
# シークレットが存在するか確認
gcloud secrets list

# シークレットのバージョン確認
gcloud secrets versions list oauth-client-id
```

---

## 12.8. 環境変数一覧

### API サービス

| 変数名 | 説明 | 例 |
|--------|------|-----|
| PROJECT_ID | GCP プロジェクト ID | my-project |
| BIGQUERY_DATASET | BigQuery データセット名 | project_progress_db |
| PUBSUB_TOPIC | Pub/Sub トピック名 | upload-events |
| ENVIRONMENT | 環境名 | prod |
| FRONTEND_URL | フロントエンド URL | https://... |
| ALLOWED_OAUTH_DOMAINS | 許可ドメイン（カンマ区切り） | example.com |

### Worker サービス

| 変数名 | 説明 | 例 |
|--------|------|-----|
| PROJECT_ID | GCP プロジェクト ID | my-project |
| BIGQUERY_DATASET | BigQuery データセット名 | project_progress_db |
| REGION | GCP リージョン | asia-northeast1 |

