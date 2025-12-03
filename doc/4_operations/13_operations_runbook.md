# 13. 運用手順書（Operations Runbook）

## 13.1. 概要

本ドキュメントでは、Project Progress DB システムの日常運用および障害対応手順を説明します。

### 監視ダッシュボード

| リソース | URL |
|----------|-----|
| Cloud Run | https://console.cloud.google.com/run |
| Cloud Monitoring | https://console.cloud.google.com/monitoring |
| Error Reporting | https://console.cloud.google.com/errors |
| Cloud Logging | https://console.cloud.google.com/logs |
| BigQuery | https://console.cloud.google.com/bigquery |

---

## 13.2. 日常運用

### 13.2.1. 日次確認項目

1. **Error Reporting の確認**
   - 新規エラーがないか確認
   - 繰り返しエラーの傾向分析

2. **Cloud Run メトリクスの確認**
   - レスポンスタイム（p99 < 2秒）
   - エラーレート（< 1%）
   - インスタンス数

3. **BigQuery 使用量の確認**
   - スキャンバイト数
   - 課金状況

### 13.2.2. 週次確認項目

1. **セキュリティ更新の確認**
   - 依存パッケージの脆弱性チェック
   - Docker ベースイメージの更新

2. **コスト分析**
   - Cloud Run 使用料
   - BigQuery 使用料
   - Vertex AI 使用料

### 13.2.3. ログクエリ例

```bash
# API エラーログの検索
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=project-progress-api-prod AND \
  severity>=ERROR" \
  --limit=50 --format=json

# Worker 処理失敗の検索
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=project-progress-worker-prod AND \
  textPayload:\"Error processing\"" \
  --limit=50
```

---

## 13.3. 障害対応手順

### 13.3.1. アラート: API 高エラーレート

**症状**: API の 5xx エラーが増加

**対応手順**:

1. **影響範囲の確認**
   ```bash
   # エラーログの確認
   gcloud run logs read project-progress-api-prod \
     --region=asia-northeast1 --limit=100 | grep -i error
   ```

2. **原因の特定**
   - BigQuery 接続エラー → BigQuery のステータス確認
   - OAuth エラー → シークレットの有効性確認
   - メモリ不足 → インスタンス設定の確認

3. **対処**
   - 一時的: インスタンス数の増加
     ```bash
     gcloud run services update project-progress-api-prod \
       --region=asia-northeast1 --max-instances=20
     ```
   - 恒久的: 根本原因の修正・デプロイ

4. **復旧確認**
   ```bash
   curl -I https://project-progress-api-prod-xxxxx.run.app/
   ```

### 13.3.2. アラート: Worker 処理失敗

**症状**: 会議議事録の AI 処理が失敗

**対応手順**:

1. **失敗した Meeting の特定**
   ```sql
   -- BigQuery で ERROR ステータスの会議を検索
   SELECT meeting_id, title, error_message, created_at
   FROM `project_id.project_progress_db.meetings`
   WHERE status = 'ERROR'
   ORDER BY created_at DESC
   LIMIT 10;
   ```

2. **エラー内容の確認**
   ```bash
   # Worker ログの確認
   gcloud run logs read project-progress-worker-prod \
     --region=asia-northeast1 --limit=100 | grep -i error
   ```

3. **原因別対処**
   
   | 原因 | 対処 |
   |------|------|
   | Vertex AI クォータ超過 | クォータ引き上げ申請 |
   | ファイル読み取りエラー | GCS バケット権限確認 |
   | JSON パースエラー | AI プロンプト調整 |

4. **リトライ**（手動で再処理）
   ```bash
   # Pub/Sub にメッセージを再送信
   gcloud pubsub topics publish upload-events \
     --message='{"meeting_id":"xxx","gcs_uri":"gs://bucket/path"}'
   ```

### 13.3.3. アラート: API サービスダウン

**症状**: API のヘルスチェック失敗

**緊急度**: 高（ユーザー影響あり）

**対応手順**:

1. **状態確認**
   ```bash
   gcloud run services describe project-progress-api-prod \
     --region=asia-northeast1 --format='value(status.conditions)'
   ```

2. **直近のデプロイ確認**
   ```bash
   gcloud run revisions list \
     --service=project-progress-api-prod \
     --region=asia-northeast1 --limit=5
   ```

3. **ロールバック**（最新デプロイが原因の場合）
   ```bash
   # 前バージョンへロールバック
   gcloud run services update-traffic project-progress-api-prod \
     --region=asia-northeast1 \
     --to-revisions=project-progress-api-prod-00004-xyz=100
   ```

4. **復旧後**
   - 根本原因の調査
   - 修正・テスト
   - 再デプロイ

---

## 13.4. データ運用

### 13.4.1. データバックアップ

BigQuery のデータはスナップショットで自動保護されています。

```sql
-- 特定時点のデータを復元（7日以内）
SELECT * FROM `project_id.project_progress_db.tasks`
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);
```

### 13.4.2. データクリーンアップ

古いデータの削除（必要に応じて実施）:

```sql
-- 1年以上前の会議データを削除
DELETE FROM `project_id.project_progress_db.meetings`
WHERE created_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY);
```

### 13.4.3. データエクスポート

```bash
# BigQuery から GCS へエクスポート
bq extract \
  --destination_format=CSV \
  project_id:project_progress_db.tasks \
  gs://bucket-name/exports/tasks_*.csv
```

---

## 13.5. スケーリング

### 13.5.1. 自動スケーリング設定

現在の設定:

| サービス | Min | Max | CPU | Memory |
|----------|-----|-----|-----|--------|
| API (prod) | 1 | 10 | 1 | 512Mi |
| Worker | 0 | 10 | 2 | 1Gi |
| Frontend | 1 | 10 | 1 | 512Mi |

### 13.5.2. スケールアップ（手動）

```bash
# 最大インスタンス数の増加
gcloud run services update project-progress-api-prod \
  --region=asia-northeast1 \
  --max-instances=20

# リソース増加
gcloud run services update project-progress-api-prod \
  --region=asia-northeast1 \
  --memory=1Gi --cpu=2
```

---

## 13.6. セキュリティ運用

### 13.6.1. シークレットローテーション

JWT シークレットキーのローテーション:

```bash
# 新しいシークレットの生成・登録
python3 -c "import secrets; print(secrets.token_urlsafe(32))" | \
  gcloud secrets versions add jwt-secret-key --data-file=-

# 古いバージョンの無効化（デプロイ後）
gcloud secrets versions disable jwt-secret-key --version=1
```

### 13.6.2. アクセスログ監査

```bash
# API アクセスログの確認
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=project-progress-api-prod" \
  --limit=100 --format=json | \
  jq '.[] | {timestamp: .timestamp, ip: .httpRequest.remoteIp, path: .httpRequest.requestUrl}'
```

### 13.6.3. 権限監査

```bash
# サービスアカウントの権限確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:*@*.iam.gserviceaccount.com"
```

---

## 13.7. 連絡先・エスカレーション

| レベル | 条件 | 担当 |
|--------|------|------|
| L1 | ログ確認で解決可能 | 運用担当 |
| L2 | コード修正が必要 | 開発担当 |
| L3 | インフラ・GCP 障害 | インフラ担当 |

### エスカレーションフロー

```
L1 対応開始
    ↓ 15分で解決しない場合
L2 へエスカレーション
    ↓ 30分で解決しない場合
L3 へエスカレーション + 関係者への状況共有
```

