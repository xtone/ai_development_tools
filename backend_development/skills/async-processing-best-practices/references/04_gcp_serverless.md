---
title: Google Cloud Tasks + Firestoreによる実装
---

## Google Cloud Tasks + Firestoreによる実装

Google Cloudのマネージドサービスを組み合わせて、サーバーレスアーキテクチャで非同期処理を実現します。Cloud Tasksでタスクキューイング、Cloud Runでジョブ実行、Firestoreでリアルタイム通知と状態管理を行います。

### アーキテクチャの特徴

- **フルマネージド**: インフラ管理が不要
- **リアルタイム同期**: Firestoreのリアルタイムリスナーでフロントエンドに自動通知
- **スケーラブル**: Cloud RunとCloud Tasksの自動スケーリング
- **HTTPベース**: Cloud TasksはHTTPエンドポイントを直接呼び出すシンプルな設計

### 採用基準

#### この構成を選ぶべきケース

- Google Cloudをメインで利用している
- Firebase/Firestoreを既に利用している
- リアルタイム通知をシンプルに実現したい（Firestoreのリアルタイムリスナー活用）
- Cloud Run/Cloud Functionsでバックエンドを構築している
- HTTPベースのシンプルな設計を好む

#### 他の選択肢を検討すべきケース

- 複雑なメッセージルーティングが必要 → Pub/Sub
- 超高スループット（数万件/秒）が必要 → Pub/Sub + Dataflow
- マルチクラウド環境 → BullMQ
- 詳細なジョブ管理UIが必要 → BullMQ + Bull Board

## アーキテクチャ

### 全体構成

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client     │────▶│  Cloud Run   │────▶│ Cloud Tasks  │
│  (API Call)  │     │  (Producer)  │     │   (Queue)    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                         │
       │     Realtime                            ▼
       │     Listener    ┌──────────────┐ ┌──────────────┐
       └────────────────▶│  Firestore   │◀│  Cloud Run   │
                         │ (状態管理)    │ │   (Worker)   │
                         └──────────────┘ └──────────────┘
```

### コンポーネントの役割

- **Cloud Run (Producer)**: APIリクエストを受け付け、Cloud Tasksにタスクを投入
- **Cloud Tasks**: タスクのキューイング、スケジューリング、リトライ管理
- **Cloud Run (Worker)**: Cloud Tasksからのコールバックを受けてジョブを処理
- **Firestore**: ジョブの状態管理、リアルタイム通知の配信

## 実装サンプル

### プロジェクト構成

```
src/
├── api/
│   ├── enqueue.ts         # ジョブ投入エンドポイント
│   ├── worker.ts          # ワーカーエンドポイント
│   └── status.ts          # 状態確認エンドポイント
├── lib/
│   ├── firestore.ts       # Firestore操作
│   ├── cloudTasks.ts      # Cloud Tasks操作
│   └── auth.ts            # 認証ヘルパー
└── types/
    └── job.ts             # 型定義
```

### 型定義

```typescript
// src/types/job.ts
export interface Job {
  jobId: string;
  type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  payload: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: string;
  progress?: number;
  createdAt: FirebaseFirestore.Timestamp;
  updatedAt: FirebaseFirestore.Timestamp;
  completedAt?: FirebaseFirestore.Timestamp;
}

export interface EnqueueRequest {
  type: string;
  payload: Record<string, unknown>;
  scheduleTime?: string; // ISO8601形式の実行予定時刻
}

export interface TaskPayload {
  jobId: string;
  type: string;
  payload: Record<string, unknown>;
}
```

### Firestore操作

```typescript
// src/lib/firestore.ts
import { Firestore, FieldValue } from '@google-cloud/firestore';
import { Job } from '../types/job';

const firestore = new Firestore();
const JOBS_COLLECTION = 'async_jobs';

export const createJob = async (
  job: Omit<Job, 'createdAt' | 'updatedAt'>
): Promise<void> => {
  const now = FieldValue.serverTimestamp();
  await firestore.collection(JOBS_COLLECTION).doc(job.jobId).set({
    ...job,
    createdAt: now,
    updatedAt: now,
  });
};

export const getJob = async (jobId: string): Promise<Job | null> => {
  const doc = await firestore.collection(JOBS_COLLECTION).doc(jobId).get();
  if (!doc.exists) return null;
  return { jobId: doc.id, ...doc.data() } as Job;
};

export const updateJobStatus = async (
  jobId: string,
  status: Job['status'],
  updates?: Partial<Pick<Job, 'result' | 'error' | 'progress'>>
): Promise<void> => {
  const data: Record<string, unknown> = {
    status,
    updatedAt: FieldValue.serverTimestamp(),
  };

  if (updates?.result !== undefined) data.result = updates.result;
  if (updates?.error !== undefined) data.error = updates.error;
  if (updates?.progress !== undefined) data.progress = updates.progress;
  if (status === 'completed' || status === 'failed') {
    data.completedAt = FieldValue.serverTimestamp();
  }

  await firestore.collection(JOBS_COLLECTION).doc(jobId).update(data);
};

// ジョブの自動削除（TTL）設定用
export const setJobTTL = async (
  jobId: string,
  expiresAt: Date
): Promise<void> => {
  await firestore.collection(JOBS_COLLECTION).doc(jobId).update({
    expiresAt: expiresAt,
  });
};
```

### Cloud Tasks操作

```typescript
// src/lib/cloudTasks.ts
import { CloudTasksClient } from '@google-cloud/tasks';
import { TaskPayload } from '../types/job';

const client = new CloudTasksClient();

const PROJECT_ID = process.env.GOOGLE_CLOUD_PROJECT!;
const LOCATION = process.env.CLOUD_TASKS_LOCATION || 'asia-northeast1';
const QUEUE_NAME = process.env.CLOUD_TASKS_QUEUE || 'async-jobs';
const WORKER_URL = process.env.WORKER_URL!;

const queuePath = client.queuePath(PROJECT_ID, LOCATION, QUEUE_NAME);

export const createTask = async (
  payload: TaskPayload,
  options?: {
    scheduleTime?: Date;
    dispatchDeadlineSeconds?: number;
  }
): Promise<string> => {
  const task: any = {
    httpRequest: {
      httpMethod: 'POST',
      url: WORKER_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      body: Buffer.from(JSON.stringify(payload)).toString('base64'),
      // OIDCトークンでCloud Run認証
      oidcToken: {
        serviceAccountEmail: `${PROJECT_ID}@appspot.gserviceaccount.com`,
      },
    },
  };

  // 実行予定時刻の設定
  if (options?.scheduleTime) {
    task.scheduleTime = {
      seconds: Math.floor(options.scheduleTime.getTime() / 1000),
    };
  }

  // タイムアウト設定（デフォルト10分）
  if (options?.dispatchDeadlineSeconds) {
    task.dispatchDeadline = {
      seconds: options.dispatchDeadlineSeconds,
    };
  }

  const [response] = await client.createTask({
    parent: queuePath,
    task,
  });

  return response.name!;
};
```

### Producer API

```typescript
// src/api/enqueue.ts
import { Request, Response } from 'express';
import { randomUUID } from 'crypto';
import { createJob } from '../lib/firestore';
import { createTask } from '../lib/cloudTasks';
import { EnqueueRequest } from '../types/job';

export const enqueueHandler = async (
  req: Request,
  res: Response
): Promise<void> => {
  try {
    const body: EnqueueRequest = req.body;

    if (!body.type || !body.payload) {
      res.status(400).json({ error: 'type and payload are required' });
      return;
    }

    const jobId = randomUUID();

    // Firestoreにジョブを作成
    await createJob({
      jobId,
      type: body.type,
      status: 'pending',
      payload: body.payload,
      progress: 0,
    });

    // Cloud Tasksにタスクを投入
    const taskName = await createTask(
      {
        jobId,
        type: body.type,
        payload: body.payload,
      },
      {
        scheduleTime: body.scheduleTime
          ? new Date(body.scheduleTime)
          : undefined,
      }
    );

    res.status(202).json({
      jobId,
      status: 'pending',
      taskName,
    });
  } catch (error) {
    console.error('Error enqueueing job:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};
```

### Worker API

```typescript
// src/api/worker.ts
import { Request, Response } from 'express';
import { updateJobStatus } from '../lib/firestore';
import { TaskPayload } from '../types/job';

// ジョブタイプごとの処理関数
const jobProcessors: Record<
  string,
  (
    jobId: string,
    payload: Record<string, unknown>,
    updateProgress: (progress: number) => Promise<void>
  ) => Promise<Record<string, unknown>>
> = {
  'send-email': async (jobId, payload, updateProgress) => {
    const { to, subject, body } = payload as {
      to: string;
      subject: string;
      body: string;
    };

    await updateProgress(10);
    // メール送信ロジック...
    await updateProgress(100);

    return { messageId: `msg-${Date.now()}`, sentAt: new Date().toISOString() };
  },

  'process-image': async (jobId, payload, updateProgress) => {
    const { imageUrl } = payload as { imageUrl: string };

    await updateProgress(10);
    // 画像処理ロジック...
    await updateProgress(50);
    // さらに処理...
    await updateProgress(100);

    return { processedUrl: `${imageUrl}-processed` };
  },
};

export const workerHandler = async (
  req: Request,
  res: Response
): Promise<void> => {
  // Cloud Tasksからのリクエスト検証
  const taskName = req.headers['x-cloudtasks-taskname'];
  if (!taskName) {
    res.status(403).json({ error: 'Forbidden' });
    return;
  }

  const taskPayload: TaskPayload = req.body;
  const { jobId, type, payload } = taskPayload;

  console.log(`Processing job ${jobId} of type ${type}`);

  try {
    // 状態を processing に更新
    await updateJobStatus(jobId, 'processing', { progress: 0 });

    const processor = jobProcessors[type];
    if (!processor) {
      throw new Error(`Unknown job type: ${type}`);
    }

    // 進捗更新用のヘルパー
    const updateProgress = async (progress: number) => {
      await updateJobStatus(jobId, 'processing', { progress });
    };

    const result = await processor(jobId, payload, updateProgress);

    // 状態を completed に更新
    await updateJobStatus(jobId, 'completed', { result, progress: 100 });

    console.log(`Job ${jobId} completed successfully`);
    res.status(200).json({ success: true });
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error';
    console.error(`Job ${jobId} failed:`, errorMessage);

    // 状態を failed に更新
    await updateJobStatus(jobId, 'failed', { error: errorMessage });

    // 5xxを返すとCloud Tasksがリトライする
    // リトライ不要な場合は2xxを返す
    res.status(500).json({ error: errorMessage });
  }
};
```

### Status API

```typescript
// src/api/status.ts
import { Request, Response } from 'express';
import { getJob } from '../lib/firestore';

export const statusHandler = async (
  req: Request,
  res: Response
): Promise<void> => {
  const jobId = req.params.jobId;

  if (!jobId) {
    res.status(400).json({ error: 'jobId is required' });
    return;
  }

  const job = await getJob(jobId);

  if (!job) {
    res.status(404).json({ error: 'Job not found' });
    return;
  }

  res.status(200).json(job);
};
```

### Express サーバー

```typescript
// src/server.ts
import express from 'express';
import { enqueueHandler } from './api/enqueue';
import { workerHandler } from './api/worker';
import { statusHandler } from './api/status';

const app = express();
app.use(express.json());

// API Routes
app.post('/jobs', enqueueHandler);
app.post('/worker', workerHandler);
app.get('/jobs/:jobId', statusHandler);

// Health check
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
```

## Dockerfile

```dockerfile
# syntax = docker/dockerfile:1
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-slim AS base

WORKDIR /app
ENV NODE_ENV="production"

# --- Build stage ---
FROM base AS build
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y build-essential python3

COPY package*.json ./
RUN npm ci --include=dev

COPY . .
RUN npm run build && \
    npm prune --production

# --- Final stage ---
FROM base
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /app/node_modules /app/node_modules
COPY --from=build /app/dist /app/dist
COPY --from=build /app/package.json /app/package.json

# 非特権ユーザーで実行
RUN useradd -m appuser
USER appuser

EXPOSE 8080
CMD ["node", "dist/server.js"]
```

## Terraform

```hcl
# Variables
variable "project_id" {
  description = "GCP Project ID"
}

variable "region" {
  default = "asia-northeast1"
}

variable "environment" {
  default = "production"
}

# Enable APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudtasks.googleapis.com",
    "firestore.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_on_destroy = false
}

# Artifact Registry
resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "app"
  format        = "DOCKER"
}

# Cloud Tasks Queue
resource "google_cloud_tasks_queue" "jobs" {
  name     = "${var.environment}-async-jobs"
  location = var.region

  rate_limits {
    max_dispatches_per_second = 100
    max_concurrent_dispatches = 10
  }

  retry_config {
    max_attempts       = 5
    max_retry_duration = "3600s"  # 1時間
    min_backoff        = "10s"
    max_backoff        = "300s"
    max_doublings      = 4
  }

  stackdriver_logging_config {
    sampling_ratio = 1.0
  }
}

# Service Account
resource "google_service_account" "app" {
  account_id   = "${var.environment}-async-app"
  display_name = "Async Processing App Service Account"
}

# IAM bindings
resource "google_project_iam_member" "app_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "app_tasks" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "app_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Cloud Run Service (API + Worker)
resource "google_cloud_run_v2_service" "app" {
  name     = "${var.environment}-async-app"
  location = var.region

  template {
    service_account = google_service_account.app.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/app/async-app:latest"

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "CLOUD_TASKS_LOCATION"
        value = var.region
      }
      env {
        name  = "CLOUD_TASKS_QUEUE"
        value = google_cloud_tasks_queue.jobs.name
      }
      env {
        name  = "WORKER_URL"
        value = "https://${var.environment}-async-app-${random_id.suffix.hex}-an.a.run.app/worker"
      }

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        period_seconds = 30
      }
    }

    scaling {
      min_instance_count = 1  # ワーカー処理のため常時1台
      max_instance_count = 10
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

# Public access for API endpoints
resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_v2_service.app.location
  service  = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Tasks can invoke worker endpoint
resource "google_cloud_run_service_iam_member" "tasks_invoker" {
  location = google_cloud_run_v2_service.app.location
  service  = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.app.email}"
}

# Firestore Database (Native mode)
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
}

# Firestore Index for job queries
resource "google_firestore_index" "jobs_by_status" {
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = "async_jobs"

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }

  fields {
    field_path = "createdAt"
    order      = "DESCENDING"
  }
}

# Firestore TTL Policy (requires Firestore Native mode)
resource "google_firestore_field" "jobs_ttl" {
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = "async_jobs"
  field      = "expiresAt"

  ttl_config {}
}

# Outputs
output "service_url" {
  value = google_cloud_run_v2_service.app.uri
}

output "tasks_queue" {
  value = google_cloud_tasks_queue.jobs.name
}
```

## フロントエンド連携（Firestore リアルタイムリスナー）

```typescript
// frontend/src/lib/firebase.ts
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
```

```typescript
// frontend/src/hooks/useJobStatus.ts
import { useState, useEffect } from 'react';
import { doc, onSnapshot } from 'firebase/firestore';
import { db } from '../lib/firebase';

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

export const useJobStatus = (jobId: string | null) => {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) {
      setLoading(false);
      return;
    }

    setLoading(true);

    const unsubscribe = onSnapshot(
      doc(db, 'async_jobs', jobId),
      (snapshot) => {
        if (snapshot.exists()) {
          const data = snapshot.data();
          setStatus({
            status: data.status,
            progress: data.progress,
            result: data.result,
            error: data.error,
          });
        } else {
          setStatus(null);
        }
        setLoading(false);
      },
      (error) => {
        console.error('Error listening to job status:', error);
        setLoading(false);
      }
    );

    return () => unsubscribe();
  }, [jobId]);

  return { status, loading };
};
```

### React Component

```tsx
// frontend/src/components/JobProgress.tsx
import { useJobStatus } from '../hooks/useJobStatus';

interface JobProgressProps {
  jobId: string;
  onComplete?: (result: Record<string, unknown>) => void;
  onError?: (error: string) => void;
}

export const JobProgress: React.FC<JobProgressProps> = ({
  jobId,
  onComplete,
  onError,
}) => {
  const { status, loading } = useJobStatus(jobId);

  useEffect(() => {
    if (status?.status === 'completed' && status.result) {
      onComplete?.(status.result);
    }
    if (status?.status === 'failed' && status.error) {
      onError?.(status.error);
    }
  }, [status, onComplete, onError]);

  if (loading) {
    return <div>読み込み中...</div>;
  }

  if (!status) {
    return <div>ジョブが見つかりません</div>;
  }

  return (
    <div className="job-progress">
      <div className="status">状態: {status.status}</div>
      {status.progress !== undefined && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${status.progress}%` }}
          />
          <span>{status.progress}%</span>
        </div>
      )}
      {status.status === 'failed' && (
        <div className="error">エラー: {status.error}</div>
      )}
      {status.status === 'completed' && (
        <div className="result">完了しました</div>
      )}
    </div>
  );
};
```

## 監視とアラート

```hcl
# Cloud Monitoring Alert Policy
resource "google_monitoring_alert_policy" "tasks_failed" {
  display_name = "${var.environment} - Cloud Tasks Failed"
  combiner     = "OR"

  conditions {
    display_name = "High task failure rate"

    condition_threshold {
      filter          = "resource.type=\"cloud_tasks_queue\" AND metric.type=\"cloudtasks.googleapis.com/queue/task_attempt_count\" AND metric.label.response_code!=\"200\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

resource "google_monitoring_alert_policy" "run_errors" {
  display_name = "${var.environment} - Cloud Run Errors"
  combiner     = "OR"

  conditions {
    display_name = "High error rate"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notification"
  type         = "email"

  labels = {
    email_address = "alerts@example.com"
  }
}
```

## セキュリティ設定

### Firestore Security Rules

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // async_jobs コレクション
    match /async_jobs/{jobId} {
      // 認証済みユーザーのみ読み取り可能
      allow read: if request.auth != null;

      // サーバーサイドからのみ書き込み可能（Service Account経由）
      allow write: if false;
    }
  }
}
```

## 制限事項と注意点

### Cloud Tasks制限

- **最大タスクサイズ**: 100KB
- **最大スケジュール期間**: 30日先まで
- **最大リトライ回数**: 設定可能（推奨5回程度）
- **タイムアウト**: 最大30分（Cloud Run宛ての場合）

### Cloud Run制限

- **最大リクエストタイムアウト**: 60分
- **最大インスタンス数**: デフォルト1000（引き上げ可能）
- **コールドスタート**: min_instance_count=0だと発生

### Firestore制限

- **ドキュメントサイズ**: 最大1MB
- **書き込みレート**: 1ドキュメントあたり1回/秒（推奨）
- **同時リアルタイムリスナー**: プロジェクトあたり最大500（課金有効時）
- **注意**: 効率的なクエリとリスナーの設計で制限内に収める

### コスト最適化

- Cloud Run: min_instance_countを調整
- Cloud Tasks: 不要なタスクを早期キャンセル
- Firestore: TTLで古いドキュメントを自動削除
