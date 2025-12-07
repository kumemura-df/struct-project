# デプロイメントチェックリスト

## 概要

このドキュメントは、Project Progress DB をGCPにデプロイする際のチェックリストです。
**特にフロントエンドのAPI URL設定に関する問題を防ぐための手順**を記載しています。

---

## ⚠️ 重要: API URL の動的設定

### 問題の背景

Cloud Run のサービスURLは `https://SERVICE_NAME-HASH-REGION.a.run.app` の形式で、
サービスを再作成した場合などにHASH部分が変更されることがあります。

フロントエンドは `NEXT_PUBLIC_API_URL` 環境変数でAPIのURLを参照しますが、
この値をハードコードすると、API URLが変更された際にフロントエンドがAPIに接続できなくなります。

### 解決策

**フロントエンドをデプロイする際は、必ずAPI URLを動的に取得して設定してください。**

---

## デプロイ方法

### 方法1: Cloud Build を使用（推奨）

```bash
cd /path/to/struct-project

gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=\
SHORT_SHA=$(git rev-parse --short HEAD),\
_ENVIRONMENT=prod,\
_API_SA_EMAIL=api-sa-8fd82014@sandbox-471809.iam.gserviceaccount.com,\
_WORKER_SA_EMAIL=worker-sa-8fd82014@sandbox-471809.iam.gserviceaccount.com,\
_ALLOWED_OAUTH_DOMAINS=datafluct.com,\
_FRONTEND_URL=https://project-progress-frontend-prod-52e5pqzdua-an.a.run.app \
  .
```

`cloudbuild.yaml` は自動的に以下を行います：
1. API をデプロイ
2. デプロイされた API の URL を取得
3. その URL を使って Frontend をデプロイ（`NEXT_PUBLIC_API_URL` を自動設定）

### 方法2: 手動デプロイ

#### ステップ1: API をデプロイ（FRONTEND_URL を必ず指定）

```bash
FRONTEND_URL=https://project-progress-frontend-prod-52e5pqzdua-an.a.run.app

gcloud run deploy project-progress-api-prod \
  --image=asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/api:latest \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=api-sa-8fd82014@sandbox-471809.iam.gserviceaccount.com \
  --set-env-vars=PROJECT_ID=sandbox-471809,BIGQUERY_DATASET=project_progress_db,ENVIRONMENT=prod,GCS_BUCKET=sandbox-471809-meeting-notes-raw,ALLOWED_OAUTH_DOMAINS=datafluct.com,FRONTEND_URL=$FRONTEND_URL \
  --set-secrets=OAUTH_CLIENT_ID=oauth-client-id:latest,OAUTH_CLIENT_SECRET=oauth-client-secret:latest,JWT_SECRET_KEY=jwt-secret-key:latest
```

#### ステップ2: API URL を取得

```bash
API_URL=$(gcloud run services describe project-progress-api-prod --region=asia-northeast1 --format='value(status.url)')
echo "API URL: $API_URL"
```

#### ステップ3: Frontend をデプロイ（API URL を環境変数に設定）

```bash
gcloud run deploy project-progress-frontend-prod \
  --image=asia-northeast1-docker.pkg.dev/sandbox-471809/project-progress-db/frontend:latest \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=NEXT_PUBLIC_API_URL=$API_URL
```

---

## デプロイ後の確認

### 1. サービスURL の確認

```bash
# API URL
gcloud run services describe project-progress-api-prod --region=asia-northeast1 --format='value(status.url)'

# Frontend URL
gcloud run services describe project-progress-frontend-prod --region=asia-northeast1 --format='value(status.url)'
```

### 2. Frontend の環境変数確認

```bash
gcloud run revisions describe $(gcloud run revisions list --service=project-progress-frontend-prod --region=asia-northeast1 --format='value(REVISION)' --limit=1) \
  --region=asia-northeast1 \
  --format='yaml(spec.containers[0].env)'
```

出力に `NEXT_PUBLIC_API_URL` が正しい API URL を指していることを確認してください。

### 3. ヘルスチェック

```bash
# API
curl -s $(gcloud run services describe project-progress-api-prod --region=asia-northeast1 --format='value(status.url)')/

# Frontend (ログインページが表示されるか)
curl -s -o /dev/null -w "%{http_code}" $(gcloud run services describe project-progress-frontend-prod --region=asia-northeast1 --format='value(status.url)')/
```

---

## トラブルシューティング

### 問題1: フロントエンドでログインできない / "Loading..." のまま

**原因**: `NEXT_PUBLIC_API_URL` が古いまたは間違った API URL を指している

**解決策（API URL 周り）**:
1. 現在の Frontend の環境変数を確認
2. API URL を取得
3. Frontend を正しい API URL で再デプロイ

```bash
# 現在の設定を確認
gcloud run revisions describe $(gcloud run revisions list --service=project-progress-frontend-prod --region=asia-northeast1 --format='value(REVISION)' --limit=1) \
  --region=asia-northeast1 \
  --format='yaml(spec.containers[0].env)'

# 正しい API URL を取得
API_URL=$(gcloud run services describe project-progress-api-prod --region=asia-northeast1 --format='value(status.url)')

# Frontend を再デプロイ
gcloud run deploy project-progress-frontend-prod \
  --image=$(gcloud run revisions describe $(gcloud run revisions list --service=project-progress-frontend-prod --region=asia-northeast1 --format='value(REVISION)' --limit=1) --region=asia-northeast1 --format='value(spec.containers[0].image)') \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=NEXT_PUBLIC_API_URL=$API_URL
```

### 問題2: Google ログイン後に `http://localhost:3000` などローカルにリダイレクトされる

**原因**: `FRONTEND_URL` が `localhost` のまま、本番APIに設定されている。

**解決策（FRONTEND_URL 周り）**:

```bash
# 1. 現在の FRONTEND_URL を確認
gcloud run revisions describe $(gcloud run revisions list --service=project-progress-api-prod --region=asia-northeast1 --format='value(REVISION)' --limit=1) \
  --region=asia-northeast1 \
  --format='yaml(spec.containers[0].env)'

# 2. 正しい FRONTEND_URL を指定して再デプロイ
FRONTEND_URL=https://project-progress-frontend-prod-52e5pqzdua-an.a.run.app

API_IMAGE=$(gcloud run services describe project-progress-api-prod --region=asia-northeast1 --format='value(spec.template.spec.containers[0].image)')

gcloud run deploy project-progress-api-prod \
  --image=$API_IMAGE \
  --region=asia-northeast1 \
  --platform=managed \
  --allow-unauthenticated \
  --update-env-vars=FRONTEND_URL=$FRONTEND_URL
```

---

## チェックリスト

デプロイ前:
- [ ] `gcloud auth login` で認証済み
- [ ] `gcloud config set project sandbox-471809` でプロジェクト設定済み
- [ ] 必要なシークレットが Secret Manager に登録済み

デプロイ後:
- [ ] API ヘルスチェック OK (`/` エンドポイントが 200 を返す)
- [ ] Frontend が正しい API URL を参照している
- [ ] Frontend でログインできる
- [ ] 各機能（アップロード、タスク一覧、リスク一覧）が動作する

