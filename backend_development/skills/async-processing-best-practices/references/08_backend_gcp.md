# GCP Serverless バックエンド実装ベストプラクティス

Google Cloud Run + Cloud Tasks + Firestoreを使用した非同期処理のバックエンド実装におけるベストプラクティスをまとめます。

## 目次

1. [パラメータの受け取り方](#パラメータの受け取り方)
2. [エラー発生時の処理と通知](#エラー発生時の処理と通知)
3. [進捗の状態管理](#進捗の状態管理)
4. [Cloud Run サービスの設計パターン](#cloud-run-サービスの設計パターン)
5. [継続可能な処理（Continuable Processing）](#継続可能な処理continuable-processing)
6. [テスト戦略](#テスト戦略)

---

## パラメータの受け取り方

### 基本原則

GCPサービスにはそれぞれペイロードサイズの制限があります。

| サービス | 最大サイズ | 備考 |
|---------|-----------|------|
| Cloud Tasks | 100KB | HTTPリクエストボディ |
| Pub/Sub | 10MB | メッセージサイズ |
| Cloud Run リクエスト | 32MB | HTTPリクエストボディ |
| Firestore ドキュメント | 1MB | ドキュメントサイズ |

### Cloud Tasks メッセージの設計

```typescript
// types/task-message.ts
interface TaskPayload {
  taskId: string;
  taskType: string;
  userId: string;
  // 軽量なパラメータのみ（100KB制限）
  params: {
    operation: string;
    options: Record<string, string | number | boolean>;
  };
  // 大きなデータはGCSへの参照
  dataRef?: {
    bucket: string;
    path: string;
  };
  metadata: {
    requestedAt: string;
    traceId: string;
  };
}

// ❌ 悪い例: 大きなデータを直接含める
interface BadPayload {
  taskId: string;
  fileContent: string; // Base64エンコードされた大きなファイル
  userList: User[];    // 大量のユーザーデータ
}

// ✅ 良い例: 参照のみを含める
interface GoodPayload {
  taskId: string;
  inputFileRef: {
    bucket: string;
    path: string;
  };
  queryConditions: {
    status: string[];
    createdAfter: string;
  };
}
```

### 大きなペイロードの処理

```typescript
// services/task-queue.ts
import { CloudTasksClient, protos } from '@google-cloud/tasks';
import { Storage } from '@google-cloud/storage';

const tasksClient = new CloudTasksClient();
const storage = new Storage();

const PAYLOAD_SIZE_THRESHOLD = 50 * 1024; // 50KB（余裕を持たせる）

interface CreateTaskOptions {
  taskId: string;
  payload: Record<string, unknown>;
  scheduleTime?: Date;
}

export async function createTask(options: CreateTaskOptions): Promise<string> {
  const { taskId, payload, scheduleTime } = options;
  const serialized = JSON.stringify(payload);

  let finalPayload: Record<string, unknown>;

  if (serialized.length > PAYLOAD_SIZE_THRESHOLD) {
    // GCSに保存して参照を渡す
    const bucket = storage.bucket(process.env.TASK_PAYLOAD_BUCKET!);
    const file = bucket.file(`payloads/${taskId}.json`);

    await file.save(serialized, {
      contentType: 'application/json',
    });

    finalPayload = {
      taskId,
      payloadRef: {
        bucket: process.env.TASK_PAYLOAD_BUCKET,
        path: `payloads/${taskId}.json`,
      },
    };
  } else {
    finalPayload = payload;
  }

  const parent = tasksClient.queuePath(
    process.env.GCP_PROJECT_ID!,
    process.env.GCP_REGION!,
    process.env.TASK_QUEUE_NAME!
  );

  const task: protos.google.cloud.tasks.v2.ITask = {
    name: `${parent}/tasks/${taskId}`,
    httpRequest: {
      httpMethod: 'POST',
      url: `${process.env.WORKER_URL}/tasks/process`,
      headers: {
        'Content-Type': 'application/json',
      },
      body: Buffer.from(JSON.stringify(finalPayload)).toString('base64'),
      oidcToken: {
        serviceAccountEmail: process.env.SERVICE_ACCOUNT_EMAIL,
      },
    },
  };

  if (scheduleTime) {
    task.scheduleTime = {
      seconds: Math.floor(scheduleTime.getTime() / 1000),
    };
  }

  const [response] = await tasksClient.createTask({ parent, task });

  return response.name!;
}

// ワーカー側でペイロードを復元
export async function resolvePayload(
  body: Record<string, unknown>
): Promise<Record<string, unknown>> {
  if (body.payloadRef) {
    const { bucket, path } = body.payloadRef as { bucket: string; path: string };
    const file = storage.bucket(bucket).file(path);
    const [content] = await file.download();
    return JSON.parse(content.toString());
  }

  return body;
}
```

### Pub/Subを使用した大量データの処理

```typescript
// services/pubsub-publisher.ts
import { PubSub, Topic } from '@google-cloud/pubsub';

const pubsub = new PubSub();

interface BatchJobData {
  taskId: string;
  batchIndex: number;
  itemIds: string[];
}

const BATCH_SIZE = 500; // Pub/Subメッセージあたり

export async function publishBatchJobs(
  taskId: string,
  allItemIds: string[],
  topicName: string
): Promise<void> {
  const topic = pubsub.topic(topicName);

  const batches: BatchJobData[] = [];

  for (let i = 0; i < allItemIds.length; i += BATCH_SIZE) {
    batches.push({
      taskId,
      batchIndex: Math.floor(i / BATCH_SIZE),
      itemIds: allItemIds.slice(i, i + BATCH_SIZE),
    });
  }

  // 並列でパブリッシュ
  const publishPromises = batches.map((batch, index) =>
    topic.publishMessage({
      json: batch,
      orderingKey: taskId, // 順序保証が必要な場合
      attributes: {
        taskId,
        batchIndex: String(index),
        totalBatches: String(batches.length),
      },
    })
  );

  await Promise.all(publishPromises);

  console.log(`Published ${batches.length} batches for task ${taskId}`);
}
```

### リクエストバリデーション

```typescript
// middleware/validation.ts
import { Request, Response, NextFunction } from 'express';
import { z } from 'zod';

const TaskPayloadSchema = z.object({
  taskId: z.string().uuid(),
  taskType: z.enum(['export', 'import', 'analyze', 'notify']),
  userId: z.string(),
  params: z.object({
    operation: z.string(),
    options: z.record(z.union([z.string(), z.number(), z.boolean()])),
  }),
  dataRef: z.object({
    bucket: z.string(),
    path: z.string(),
  }).optional(),
  metadata: z.object({
    requestedAt: z.string().datetime(),
    traceId: z.string(),
  }),
});

export function validateTaskPayload(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const result = TaskPayloadSchema.safeParse(req.body);

  if (!result.success) {
    res.status(400).json({
      error: 'Invalid payload',
      details: result.error.errors,
    });
    return;
  }

  req.body = result.data;
  next();
}

// Cloud Tasks からのリクエスト認証
export async function authenticateCloudTasks(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Missing authorization header' });
    return;
  }

  const token = authHeader.substring(7);

  try {
    // OIDCトークンを検証
    const { OAuth2Client } = await import('google-auth-library');
    const client = new OAuth2Client();

    const ticket = await client.verifyIdToken({
      idToken: token,
      audience: process.env.WORKER_URL,
    });

    const payload = ticket.getPayload();

    if (payload?.email !== process.env.SERVICE_ACCOUNT_EMAIL) {
      res.status(403).json({ error: 'Invalid service account' });
      return;
    }

    next();
  } catch (error) {
    console.error('Token verification failed', error);
    res.status(401).json({ error: 'Invalid token' });
  }
}
```

---

## エラー発生時の処理と通知

### Cloud Tasks のリトライ設定

```typescript
// infrastructure/terraform/cloud-tasks.tf
/*
resource "google_cloud_tasks_queue" "task_queue" {
  name     = "async-task-queue"
  location = var.region

  rate_limits {
    max_concurrent_dispatches = 100
    max_dispatches_per_second = 50
  }

  retry_config {
    max_attempts       = 5
    max_retry_duration = "3600s"  # 1時間
    min_backoff        = "10s"
    max_backoff        = "300s"   # 5分
    max_doublings      = 4
  }

  stackdriver_logging_config {
    sampling_ratio = 1.0  # 全ログを記録
  }
}
*/
```

### エラーハンドリングの実装

```typescript
// handlers/task-processor.ts
import { Request, Response } from 'express';
import { TaskStateManager } from '../services/task-state-manager';
import { ErrorReporter } from '../services/error-reporter';

const stateManager = new TaskStateManager();
const errorReporter = new ErrorReporter();

// カスタムエラークラス
class RetryableError extends Error {
  constructor(message: string, public readonly retryAfter?: number) {
    super(message);
    this.name = 'RetryableError';
  }
}

class NonRetryableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NonRetryableError';
  }
}

export async function processTask(req: Request, res: Response): Promise<void> {
  const payload = req.body;
  const taskId = payload.taskId;

  // Cloud Tasksのリトライ情報を取得
  const taskRetryCount = parseInt(
    req.headers['x-cloudtasks-taskretrycount'] as string || '0'
  );
  const taskExecutionCount = parseInt(
    req.headers['x-cloudtasks-taskexecutioncount'] as string || '0'
  );

  console.log('Processing task', {
    taskId,
    retryCount: taskRetryCount,
    executionCount: taskExecutionCount,
  });

  try {
    await stateManager.updateStatus(taskId, 'processing', {
      attemptNumber: taskRetryCount + 1,
    });

    // ペイロードを解決（GCSから取得する場合）
    const resolvedPayload = await resolvePayload(payload);

    // 実際の処理
    const result = await executeTask(resolvedPayload);

    await stateManager.markCompleted(taskId, result);

    res.status(200).json({ success: true, result });

  } catch (error) {
    await handleError(taskId, error, taskRetryCount, res);
  }
}

async function handleError(
  taskId: string,
  error: unknown,
  retryCount: number,
  res: Response
): Promise<void> {
  const errorMessage = error instanceof Error ? error.message : 'Unknown error';

  if (error instanceof NonRetryableError) {
    // リトライ不要：200を返してタスクを完了
    console.error('Non-retryable error', { taskId, error: errorMessage });

    await stateManager.markFailed(taskId, errorMessage);
    await errorReporter.reportError(taskId, error);

    res.status(200).json({
      success: false,
      error: errorMessage,
      retryable: false,
    });
    return;
  }

  if (error instanceof RetryableError) {
    // リトライ可能：適切なステータスコードを返す
    console.warn('Retryable error', { taskId, error: errorMessage, retryCount });

    await stateManager.updateStatus(taskId, 'retrying', {
      lastError: errorMessage,
      retryCount: retryCount + 1,
    });

    // 429または500-599でCloud Tasksがリトライ
    const statusCode = error.retryAfter ? 429 : 500;

    if (error.retryAfter) {
      res.setHeader('Retry-After', String(error.retryAfter));
    }

    res.status(statusCode).json({
      success: false,
      error: errorMessage,
      retryable: true,
    });
    return;
  }

  // その他のエラー：デフォルトでリトライ
  console.error('Unexpected error', { taskId, error });

  await stateManager.updateStatus(taskId, 'retrying', {
    lastError: errorMessage,
    retryCount: retryCount + 1,
  });

  res.status(500).json({
    success: false,
    error: errorMessage,
    retryable: true,
  });
}
```

### Dead Letter Queueの実装

```typescript
// handlers/dlq-processor.ts
import { Request, Response } from 'express';
import { Firestore } from '@google-cloud/firestore';

const firestore = new Firestore();

interface DeadLetterTask {
  taskId: string;
  originalPayload: Record<string, unknown>;
  errorMessage: string;
  retryCount: number;
  failedAt: FirebaseFirestore.Timestamp;
  queueName: string;
  headers: Record<string, string>;
}

// Cloud Tasks DLQからのリクエストを処理
export async function processDeadLetter(
  req: Request,
  res: Response
): Promise<void> {
  const payload = req.body;
  const taskId = payload.taskId || 'unknown';

  // ヘッダーから情報を取得
  const headers = {
    taskName: req.headers['x-cloudtasks-taskname'] as string,
    queueName: req.headers['x-cloudtasks-queuename'] as string,
    retryCount: req.headers['x-cloudtasks-taskretrycount'] as string,
    executionCount: req.headers['x-cloudtasks-taskexecutioncount'] as string,
  };

  console.error('Task in DLQ', { taskId, headers });

  // Firestoreに記録
  const deadLetterRef = firestore.collection('deadLetterTasks').doc(taskId);
  await deadLetterRef.set({
    taskId,
    originalPayload: payload,
    errorMessage: 'Max retries exceeded',
    retryCount: parseInt(headers.retryCount || '0'),
    failedAt: Firestore.FieldValue.serverTimestamp(),
    queueName: headers.queueName,
    headers,
  });

  // タスクを最終失敗としてマーク
  await stateManager.markFailed(
    taskId,
    `Max retries exceeded after ${headers.retryCount} attempts`
  );

  // アラート送信
  await sendAlert({
    title: `Task Failed: ${taskId}`,
    message: `Task ${taskId} failed after ${headers.retryCount} retries`,
    severity: 'error',
    taskId,
    payload,
  });

  res.status(200).json({ acknowledged: true });
}
```

### Error Reportingの統合

```typescript
// services/error-reporter.ts
import { ErrorReporting } from '@google-cloud/error-reporting';

const errors = new ErrorReporting({
  projectId: process.env.GCP_PROJECT_ID,
  reportMode: 'always',
});

export class ErrorReporter {
  async reportError(
    taskId: string,
    error: Error,
    context?: Record<string, unknown>
  ): Promise<void> {
    // Google Cloud Error Reporting
    errors.report(error, {
      user: context?.userId as string,
      httpRequest: {
        url: `/tasks/${taskId}`,
        method: 'POST',
      },
    });

    // 構造化ログ（Cloud Loggingで検索可能）
    console.error(JSON.stringify({
      severity: 'ERROR',
      message: error.message,
      taskId,
      errorType: error.name,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString(),
    }));
  }

  async reportWarning(
    message: string,
    context?: Record<string, unknown>
  ): Promise<void> {
    console.warn(JSON.stringify({
      severity: 'WARNING',
      message,
      context,
      timestamp: new Date().toISOString(),
    }));
  }
}
```

### Cloud Monitoring アラートの設定

```typescript
// infrastructure/terraform/monitoring.tf
/*
resource "google_monitoring_alert_policy" "task_failure_rate" {
  display_name = "High Task Failure Rate"
  combiner     = "OR"

  conditions {
    display_name = "Task failure rate > 10%"

    condition_threshold {
      filter = <<-EOT
        resource.type = "cloud_run_revision"
        AND resource.labels.service_name = "task-worker"
        AND metric.type = "run.googleapis.com/request_count"
        AND metric.labels.response_code_class = "5xx"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 0.1
      duration        = "300s"

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.slack.name]

  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_alert_policy" "dlq_messages" {
  display_name = "Messages in DLQ"
  combiner     = "OR"

  conditions {
    display_name = "DLQ has messages"

    condition_threshold {
      filter = <<-EOT
        resource.type = "cloud_tasks_queue"
        AND resource.labels.queue_id = "async-task-dlq"
        AND metric.type = "cloudtasks.googleapis.com/queue/depth"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.slack.name]
}
*/
```

---

## 進捗の状態管理

### Firestoreによる状態管理

```typescript
// services/task-state-manager.ts
import {
  Firestore,
  FieldValue,
  Timestamp,
  DocumentReference,
} from '@google-cloud/firestore';

const firestore = new Firestore();

export enum TaskStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

interface TaskState {
  taskId: string;
  userId: string;
  taskType: string;
  status: TaskStatus;
  progress: number;
  totalItems: number | null;
  currentPhase: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
  retryCount: number;
  startedAt: Timestamp | null;
  completedAt: Timestamp | null;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export class TaskStateManager {
  private collection = firestore.collection('tasks');

  async createTask(
    taskId: string,
    userId: string,
    taskType: string,
    params: Record<string, unknown>
  ): Promise<TaskState> {
    const taskRef = this.collection.doc(taskId);

    const task: Omit<TaskState, 'createdAt' | 'updatedAt'> & {
      createdAt: FieldValue;
      updatedAt: FieldValue;
      params: Record<string, unknown>;
    } = {
      taskId,
      userId,
      taskType,
      status: TaskStatus.PENDING,
      progress: 0,
      totalItems: null,
      currentPhase: null,
      result: null,
      error: null,
      retryCount: 0,
      startedAt: null,
      completedAt: null,
      params,
      createdAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp(),
    };

    await taskRef.set(task);

    return this.getTask(taskId) as Promise<TaskState>;
  }

  async updateStatus(
    taskId: string,
    status: TaskStatus,
    additionalData?: Partial<TaskState>
  ): Promise<void> {
    const taskRef = this.collection.doc(taskId);

    const updates: Record<string, unknown> = {
      status,
      updatedAt: FieldValue.serverTimestamp(),
      ...additionalData,
    };

    if (status === TaskStatus.PROCESSING && !additionalData?.startedAt) {
      updates.startedAt = FieldValue.serverTimestamp();
    }

    await taskRef.update(updates);
  }

  async updateProgress(
    taskId: string,
    progress: number,
    totalItems?: number,
    currentPhase?: string
  ): Promise<void> {
    const taskRef = this.collection.doc(taskId);

    const updates: Record<string, unknown> = {
      progress,
      status: TaskStatus.PROCESSING,
      updatedAt: FieldValue.serverTimestamp(),
    };

    if (totalItems !== undefined) {
      updates.totalItems = totalItems;
    }

    if (currentPhase !== undefined) {
      updates.currentPhase = currentPhase;
    }

    await taskRef.update(updates);
  }

  async markCompleted(
    taskId: string,
    result: Record<string, unknown>
  ): Promise<void> {
    const taskRef = this.collection.doc(taskId);

    await taskRef.update({
      status: TaskStatus.COMPLETED,
      result,
      completedAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp(),
    });
  }

  async markFailed(taskId: string, error: string): Promise<void> {
    const taskRef = this.collection.doc(taskId);

    await taskRef.update({
      status: TaskStatus.FAILED,
      error,
      completedAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp(),
    });
  }

  async getTask(taskId: string): Promise<TaskState | null> {
    const doc = await this.collection.doc(taskId).get();

    if (!doc.exists) {
      return null;
    }

    return doc.data() as TaskState;
  }

  async getUserTasks(
    userId: string,
    limit: number = 20
  ): Promise<TaskState[]> {
    const snapshot = await this.collection
      .where('userId', '==', userId)
      .orderBy('createdAt', 'desc')
      .limit(limit)
      .get();

    return snapshot.docs.map(doc => doc.data() as TaskState);
  }

  // タスクの監視用リスナーを取得
  getTaskListener(
    taskId: string,
    callback: (task: TaskState | null) => void
  ): () => void {
    return this.collection.doc(taskId).onSnapshot(
      (snapshot) => {
        if (snapshot.exists) {
          callback(snapshot.data() as TaskState);
        } else {
          callback(null);
        }
      },
      (error) => {
        console.error('Firestore listener error', { taskId, error });
      }
    );
  }
}
```

### 進捗更新を含むタスク処理

```typescript
// handlers/bulk-processor.ts
import { Request, Response } from 'express';
import { TaskStateManager, TaskStatus } from '../services/task-state-manager';

const stateManager = new TaskStateManager();

const PROGRESS_UPDATE_INTERVAL = 10;
const CANCELLATION_CHECK_INTERVAL = 100;

interface BulkProcessPayload {
  taskId: string;
  userId: string;
  params: {
    itemIds: string[];
  };
}

export async function processBulkTask(
  req: Request,
  res: Response
): Promise<void> {
  const payload = req.body as BulkProcessPayload;
  const { taskId, userId, params } = payload;
  const items = params.itemIds;
  const totalItems = items.length;

  try {
    // 処理開始
    await stateManager.updateProgress(taskId, 0, totalItems, 'initializing');

    let processed = 0;
    const results: unknown[] = [];

    for (const itemId of items) {
      // キャンセルチェック
      if (processed % CANCELLATION_CHECK_INTERVAL === 0) {
        const task = await stateManager.getTask(taskId);
        if (task?.status === TaskStatus.CANCELLED) {
          console.log('Task cancelled', { taskId, processed });
          res.status(200).json({
            success: false,
            cancelled: true,
            processedItems: processed,
          });
          return;
        }
      }

      // アイテム処理
      const result = await processItem(itemId);
      results.push(result);
      processed++;

      // 進捗更新
      if (
        processed % PROGRESS_UPDATE_INTERVAL === 0 ||
        processed === totalItems
      ) {
        await stateManager.updateProgress(
          taskId,
          processed,
          totalItems,
          'processing'
        );
      }
    }

    // 完了
    const finalResult = {
      processedItems: processed,
      totalItems,
      results,
    };

    await stateManager.markCompleted(taskId, finalResult);

    res.status(200).json({
      success: true,
      result: finalResult,
    });

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    await stateManager.markFailed(taskId, errorMessage);
    throw error;
  }
}

async function processItem(itemId: string): Promise<unknown> {
  // 実際のアイテム処理
  return { itemId, processed: true };
}
```

### Firestoreリアルタイムリスナー用のAPIエンドポイント

```typescript
// routes/tasks.ts
import { Router, Request, Response } from 'express';
import { TaskStateManager } from '../services/task-state-manager';

const router = Router();
const stateManager = new TaskStateManager();

// タスクステータス取得
router.get('/:taskId/status', async (req: Request, res: Response) => {
  const { taskId } = req.params;
  const userId = req.user?.id; // 認証ミドルウェアから

  const task = await stateManager.getTask(taskId);

  if (!task) {
    res.status(404).json({ error: 'Task not found' });
    return;
  }

  if (task.userId !== userId) {
    res.status(403).json({ error: 'Access denied' });
    return;
  }

  const response = {
    taskId: task.taskId,
    status: task.status,
    progress: task.totalItems
      ? Math.round((task.progress / task.totalItems) * 100)
      : 0,
    currentPhase: task.currentPhase,
    result: task.status === 'completed' ? task.result : null,
    error: task.status === 'failed' ? task.error : null,
    startedAt: task.startedAt?.toDate().toISOString() || null,
    completedAt: task.completedAt?.toDate().toISOString() || null,
  };

  // キャッシュ制御
  if (task.status === 'completed' || task.status === 'failed') {
    res.setHeader('Cache-Control', 'public, max-age=3600');
  } else {
    res.setHeader('Cache-Control', 'no-cache');
  }

  res.json(response);
});

// タスクキャンセル
router.post('/:taskId/cancel', async (req: Request, res: Response) => {
  const { taskId } = req.params;
  const userId = req.user?.id;

  const task = await stateManager.getTask(taskId);

  if (!task) {
    res.status(404).json({ error: 'Task not found' });
    return;
  }

  if (task.userId !== userId) {
    res.status(403).json({ error: 'Access denied' });
    return;
  }

  if (!['pending', 'queued', 'processing'].includes(task.status)) {
    res.status(400).json({ error: 'Task cannot be cancelled' });
    return;
  }

  await stateManager.updateStatus(taskId, 'cancelled' as any);

  res.json({ success: true });
});

// ユーザーのタスク一覧
router.get('/', async (req: Request, res: Response) => {
  const userId = req.user?.id;
  const limit = parseInt(req.query.limit as string || '20');

  const tasks = await stateManager.getUserTasks(userId!, limit);

  res.json({
    tasks: tasks.map(task => ({
      taskId: task.taskId,
      taskType: task.taskType,
      status: task.status,
      progress: task.totalItems
        ? Math.round((task.progress / task.totalItems) * 100)
        : 0,
      createdAt: task.createdAt?.toDate().toISOString(),
      completedAt: task.completedAt?.toDate().toISOString() || null,
    })),
  });
});

export default router;
```

### Server-Sent Events（SSE）による進捗配信

```typescript
// routes/tasks-sse.ts
import { Router, Request, Response } from 'express';
import { TaskStateManager } from '../services/task-state-manager';

const router = Router();
const stateManager = new TaskStateManager();

router.get('/:taskId/stream', async (req: Request, res: Response) => {
  const { taskId } = req.params;
  const userId = req.user?.id;

  const task = await stateManager.getTask(taskId);

  if (!task || task.userId !== userId) {
    res.status(403).json({ error: 'Access denied' });
    return;
  }

  // SSEヘッダー
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  // 初期状態を送信
  sendTaskEvent(res, task);

  // 完了済みの場合は終了
  if (['completed', 'failed', 'cancelled'].includes(task.status)) {
    res.end();
    return;
  }

  // Firestoreリスナーを設定
  const unsubscribe = stateManager.getTaskListener(taskId, (updatedTask) => {
    if (!updatedTask) {
      res.write('event: error\ndata: Task not found\n\n');
      res.end();
      unsubscribe();
      return;
    }

    sendTaskEvent(res, updatedTask);

    if (['completed', 'failed', 'cancelled'].includes(updatedTask.status)) {
      res.end();
      unsubscribe();
    }
  });

  // クライアント切断時にリスナーを解除
  req.on('close', () => {
    unsubscribe();
  });
});

function sendTaskEvent(res: Response, task: any): void {
  const event = {
    taskId: task.taskId,
    status: task.status,
    progress: task.totalItems
      ? Math.round((task.progress / task.totalItems) * 100)
      : 0,
    currentPhase: task.currentPhase,
    result: task.status === 'completed' ? task.result : null,
    error: task.status === 'failed' ? task.error : null,
  };

  res.write(`data: ${JSON.stringify(event)}\n\n`);
}

export default router;
```

---

## Cloud Run サービスの設計パターン

### 冪等性の確保

```typescript
// services/idempotency.ts
import { Firestore, FieldValue } from '@google-cloud/firestore';

const firestore = new Firestore();

interface IdempotencyRecord {
  status: 'in_progress' | 'completed' | 'failed';
  result?: unknown;
  error?: string;
  createdAt: FirebaseFirestore.Timestamp;
  expiresAt: FirebaseFirestore.Timestamp;
}

export class IdempotencyManager {
  private collection = firestore.collection('idempotencyKeys');
  private ttlSeconds: number;

  constructor(ttlSeconds: number = 3600) {
    this.ttlSeconds = ttlSeconds;
  }

  async tryAcquire(key: string): Promise<{
    acquired: boolean;
    existingResult?: unknown;
  }> {
    const docRef = this.collection.doc(key);

    try {
      await firestore.runTransaction(async (transaction) => {
        const doc = await transaction.get(docRef);

        if (doc.exists) {
          const data = doc.data() as IdempotencyRecord;

          if (data.status === 'completed') {
            throw { type: 'already_completed', result: data.result };
          }

          if (data.status === 'in_progress') {
            // 古いin_progressレコードはリトライ可能
            const createdAt = data.createdAt.toDate();
            const age = Date.now() - createdAt.getTime();

            if (age < 5 * 60 * 1000) { // 5分以内
              throw { type: 'in_progress' };
            }
          }
        }

        const expiresAt = new Date(Date.now() + this.ttlSeconds * 1000);

        transaction.set(docRef, {
          status: 'in_progress',
          createdAt: FieldValue.serverTimestamp(),
          expiresAt: Firestore.Timestamp.fromDate(expiresAt),
        });
      });

      return { acquired: true };

    } catch (error: any) {
      if (error.type === 'already_completed') {
        return { acquired: false, existingResult: error.result };
      }

      if (error.type === 'in_progress') {
        throw new Error('Operation is already in progress');
      }

      throw error;
    }
  }

  async markCompleted(key: string, result: unknown): Promise<void> {
    const expiresAt = new Date(Date.now() + this.ttlSeconds * 1000);

    await this.collection.doc(key).update({
      status: 'completed',
      result,
      expiresAt: Firestore.Timestamp.fromDate(expiresAt),
    });
  }

  async markFailed(key: string, error: string): Promise<void> {
    await this.collection.doc(key).update({
      status: 'failed',
      error,
    });
  }
}

// 使用例
export async function idempotentProcess<T>(
  idempotencyKey: string,
  processor: () => Promise<T>
): Promise<T> {
  const manager = new IdempotencyManager();

  const { acquired, existingResult } = await manager.tryAcquire(idempotencyKey);

  if (!acquired && existingResult !== undefined) {
    console.log('Returning cached result', { idempotencyKey });
    return existingResult as T;
  }

  try {
    const result = await processor();
    await manager.markCompleted(idempotencyKey, result);
    return result;
  } catch (error) {
    await manager.markFailed(
      idempotencyKey,
      error instanceof Error ? error.message : 'Unknown error'
    );
    throw error;
  }
}
```

### 長時間処理の分割（Cloud Tasks チェーン）

```typescript
// services/task-chain.ts
import { CloudTasksClient } from '@google-cloud/tasks';

const tasksClient = new CloudTasksClient();

interface ChainState {
  taskId: string;
  currentPhase: string;
  lastProcessedId?: string;
  processedCount: number;
  totalCount: number;
}

export async function scheduleNextPhase(
  state: ChainState,
  delaySeconds: number = 1
): Promise<void> {
  const parent = tasksClient.queuePath(
    process.env.GCP_PROJECT_ID!,
    process.env.GCP_REGION!,
    process.env.TASK_QUEUE_NAME!
  );

  const taskName = `${parent}/tasks/${state.taskId}-${state.currentPhase}-${Date.now()}`;

  await tasksClient.createTask({
    parent,
    task: {
      name: taskName,
      scheduleTime: {
        seconds: Math.floor(Date.now() / 1000) + delaySeconds,
      },
      httpRequest: {
        httpMethod: 'POST',
        url: `${process.env.WORKER_URL}/tasks/process-chain`,
        headers: {
          'Content-Type': 'application/json',
        },
        body: Buffer.from(JSON.stringify(state)).toString('base64'),
        oidcToken: {
          serviceAccountEmail: process.env.SERVICE_ACCOUNT_EMAIL,
        },
      },
    },
  });
}

// 長時間処理のハンドラー
export async function processChain(
  req: Request,
  res: Response
): Promise<void> {
  const state = req.body as ChainState;
  const BATCH_SIZE = 1000;
  const MAX_EXECUTION_TIME = 8 * 60 * 1000; // 8分（Cloud Run 10分制限の余裕）

  const startTime = Date.now();

  try {
    // バッチを取得
    const items = await getItemsBatch(
      state.taskId,
      state.lastProcessedId,
      BATCH_SIZE
    );

    if (items.length === 0) {
      // 完了
      await stateManager.markCompleted(state.taskId, {
        processedCount: state.processedCount,
        totalCount: state.totalCount,
      });

      res.status(200).json({ completed: true });
      return;
    }

    let processed = 0;

    for (const item of items) {
      // タイムアウトチェック
      if (Date.now() - startTime > MAX_EXECUTION_TIME) {
        // 次のフェーズをスケジュール
        await scheduleNextPhase({
          ...state,
          lastProcessedId: item.id,
          processedCount: state.processedCount + processed,
        });

        await stateManager.updateProgress(
          state.taskId,
          state.processedCount + processed,
          state.totalCount,
          'processing'
        );

        res.status(200).json({
          paused: true,
          processedInThisBatch: processed,
        });
        return;
      }

      await processItem(item);
      processed++;
      state.lastProcessedId = item.id;
    }

    // バッチ完了、次のバッチをスケジュール
    if (items.length === BATCH_SIZE) {
      await scheduleNextPhase({
        ...state,
        processedCount: state.processedCount + processed,
      });
    } else {
      // 全完了
      await stateManager.markCompleted(state.taskId, {
        processedCount: state.processedCount + processed,
        totalCount: state.totalCount,
      });
    }

    res.status(200).json({
      processedInThisBatch: processed,
      willContinue: items.length === BATCH_SIZE,
    });

  } catch (error) {
    throw error;
  }
}
```

### Workflowsによるオーケストレーション

```yaml
# workflows/task-processor.yaml
# 注意: Cloud Workflows では except は try ブロック内でのみ使用可能です
main:
  params: [input]
  steps:
    - init:
        assign:
          - taskId: ${input.taskId}
          - userId: ${input.userId}
          - params: ${input.params}

    - mainProcess:
        try:
          steps:
            - updateStatusProcessing:
                call: http.post
                args:
                  url: ${sys.get_env("WORKER_URL") + "/internal/tasks/" + taskId + "/status"}
                  body:
                    status: "processing"
                  auth:
                    type: OIDC
                result: statusResult

            - collectData:
                call: http.post
                args:
                  url: ${sys.get_env("WORKER_URL") + "/internal/tasks/collect"}
                  body:
                    taskId: ${taskId}
                    params: ${params}
                  auth:
                    type: OIDC
                  timeout: 1800  # 30分
                result: collectResult

            - transformData:
                call: http.post
                args:
                  url: ${sys.get_env("WORKER_URL") + "/internal/tasks/transform"}
                  body:
                    taskId: ${taskId}
                    collectedData: ${collectResult.body.data}
                  auth:
                    type: OIDC
                  timeout: 1800
                result: transformResult

            - generateOutput:
                call: http.post
                args:
                  url: ${sys.get_env("WORKER_URL") + "/internal/tasks/output"}
                  body:
                    taskId: ${taskId}
                    transformedData: ${transformResult.body.data}
                  auth:
                    type: OIDC
                  timeout: 1800
                result: outputResult

            - markCompleted:
                call: http.post
                args:
                  url: ${sys.get_env("WORKER_URL") + "/internal/tasks/" + taskId + "/status"}
                  body:
                    status: "completed"
                    result: ${outputResult.body}
                  auth:
                    type: OIDC

            - returnResult:
                return: ${outputResult.body}

        except:
          as: e
          steps:
            - markFailed:
                call: http.post
                args:
                  url: ${sys.get_env("WORKER_URL") + "/internal/tasks/" + taskId + "/status"}
                  body:
                    status: "failed"
                    error: ${e.message}
                  auth:
                    type: OIDC

            - raiseError:
                raise: ${e}
```

---

## 継続可能な処理（Continuable Processing）

GCP環境では、Cloud Run の実行時間制限（最大60分）やコスト効率の観点から、長時間実行される処理を中断・再開可能にする仕組みが重要です。

### Cloud Workflowsによるチェックポイント

Cloud Workflowsは自動的に各ステップの状態を永続化し、失敗時に再開できます。

```yaml
# workflows/resumable-batch-processor.yaml
# 注意: Cloud Workflows では except は try ブロック内でのみ使用可能です
main:
  params: [input]
  steps:
    - init:
        assign:
          - taskId: ${input.taskId}
          - userId: ${input.userId}
          - batchSize: 1000
          - lastProcessedId: ${default(input.checkpoint.lastProcessedId, null)}
          - processedCount: ${default(input.checkpoint.processedCount, 0)}
          - totalCount: ${default(input.checkpoint.totalCount, 0)}

    - mainProcess:
        try:
          steps:
            # 初回のみ総数を取得
            - getTotal:
                switch:
                  - condition: ${totalCount == 0}
                    steps:
                      - fetchTotal:
                          call: http.post
                          args:
                            url: ${sys.get_env("WORKER_URL") + "/internal/count"}
                            body:
                              taskId: ${taskId}
                            auth:
                              type: OIDC
                          result: countResult
                      - setTotal:
                          assign:
                            - totalCount: ${countResult.body.total}

            # バッチ処理ループ
            - processBatches:
                for:
                  value: iteration
                  range: [0, 10000]  # 最大イテレーション数（セーフガード）
                  steps:
                    - checkCompletion:
                        switch:
                          - condition: ${processedCount >= totalCount}
                            next: markCompleted

                    - fetchBatch:
                        call: http.post
                        args:
                          url: ${sys.get_env("WORKER_URL") + "/internal/batch"}
                          body:
                            taskId: ${taskId}
                            lastProcessedId: ${lastProcessedId}
                            batchSize: ${batchSize}
                          auth:
                            type: OIDC
                          timeout: 300
                        result: batchResult

                    - processBatch:
                        call: http.post
                        args:
                          url: ${sys.get_env("WORKER_URL") + "/internal/process"}
                          body:
                            taskId: ${taskId}
                            items: ${batchResult.body.items}
                          auth:
                            type: OIDC
                          timeout: 1800  # 30分
                        result: processResult

                    - updateCheckpoint:
                        assign:
                          - lastProcessedId: ${processResult.body.lastProcessedId}
                          - processedCount: ${processedCount + processResult.body.processedCount}

                    # Firestoreに進捗を保存（外部から監視可能）
                    - saveProgress:
                        call: http.post
                        args:
                          url: ${sys.get_env("WORKER_URL") + "/internal/progress"}
                          body:
                            taskId: ${taskId}
                            processedCount: ${processedCount}
                            totalCount: ${totalCount}
                            lastProcessedId: ${lastProcessedId}
                          auth:
                            type: OIDC

                    - checkBatchCompletion:
                        switch:
                          - condition: ${len(batchResult.body.items) < batchSize}
                            next: markCompleted

            - markCompleted:
                call: http.post
                args:
                  url: ${sys.get_env("WORKER_URL") + "/internal/tasks/" + taskId + "/complete"}
                  body:
                    processedCount: ${processedCount}
                    totalCount: ${totalCount}
                  auth:
                    type: OIDC

            - returnResult:
                return:
                  status: "completed"
                  processedCount: ${processedCount}
                  totalCount: ${totalCount}

        # エラーハンドリング（チェックポイントを保存してリトライ可能に）
        except:
          as: e
          steps:
            - saveCheckpointOnError:
                call: http.post
                args:
                  url: ${sys.get_env("WORKER_URL") + "/internal/checkpoint"}
                  body:
                    taskId: ${taskId}
                    lastProcessedId: ${lastProcessedId}
                    processedCount: ${processedCount}
                    totalCount: ${totalCount}
                    error: ${e.message}
                  auth:
                    type: OIDC
            - raiseError:
                raise: ${e}
```

### Cloud Run Jobs によるチェックポイント処理

長時間のバッチ処理には Cloud Run Jobs を使用し、定期的にチェックポイントを保存します。

```typescript
// jobs/batch-processor.ts
import { Firestore, FieldValue } from '@google-cloud/firestore';
import { Storage } from '@google-cloud/storage';

const firestore = new Firestore();
const storage = new Storage();

interface Checkpoint {
  taskId: string;
  lastProcessedId: string | null;
  processedCount: number;
  totalCount: number;
  phase: string;
  metadata: Record<string, unknown>;
  updatedAt: FirebaseFirestore.Timestamp;
}

class CheckpointManager {
  private collection = firestore.collection('checkpoints');

  async save(checkpoint: Omit<Checkpoint, 'updatedAt'>): Promise<void> {
    await this.collection.doc(checkpoint.taskId).set({
      ...checkpoint,
      updatedAt: FieldValue.serverTimestamp(),
    });
  }

  async load(taskId: string): Promise<Checkpoint | null> {
    const doc = await this.collection.doc(taskId).get();
    return doc.exists ? (doc.data() as Checkpoint) : null;
  }

  async delete(taskId: string): Promise<void> {
    await this.collection.doc(taskId).delete();
  }
}

const checkpointManager = new CheckpointManager();

// Cloud Run Jobs のメインエントリポイント
async function main(): Promise<void> {
  const taskId = process.env.TASK_ID!;
  const BATCH_SIZE = 500;
  const CHECKPOINT_INTERVAL = 100;

  // Cloud Run Jobs は最大24時間実行可能
  // 安全のため、23時間でチェックポイントを保存して終了
  const MAX_EXECUTION_TIME = 23 * 60 * 60 * 1000;
  const startTime = Date.now();

  console.log(`Starting job for task: ${taskId}`);

  try {
    // 既存のチェックポイントを取得
    let checkpoint = await checkpointManager.load(taskId);
    let lastProcessedId = checkpoint?.lastProcessedId || null;
    let processedCount = checkpoint?.processedCount || 0;

    // 総数を取得（初回のみ）
    const totalCount = checkpoint?.totalCount || await getTotalCount(taskId);

    console.log(`Resuming from checkpoint`, {
      lastProcessedId,
      processedCount,
      totalCount,
    });

    // 処理ループ
    while (true) {
      // タイムアウトチェック
      if (Date.now() - startTime > MAX_EXECUTION_TIME) {
        console.log('Approaching max execution time, saving checkpoint');
        await checkpointManager.save({
          taskId,
          lastProcessedId,
          processedCount,
          totalCount,
          phase: 'paused',
          metadata: { pausedAt: new Date().toISOString() },
        });

        // 自分自身を再スケジュール
        await scheduleNextJobExecution(taskId);
        return;
      }

      // バッチを取得
      const items = await fetchBatch(taskId, lastProcessedId, BATCH_SIZE);

      if (items.length === 0) {
        // 完了
        console.log('Processing completed', { taskId, processedCount });
        await checkpointManager.delete(taskId);
        await markTaskCompleted(taskId, { processedCount, totalCount });
        return;
      }

      // バッチを処理
      for (const item of items) {
        await processItem(item);
        lastProcessedId = item.id;
        processedCount++;

        // 定期的にチェックポイントを保存
        if (processedCount % CHECKPOINT_INTERVAL === 0) {
          await checkpointManager.save({
            taskId,
            lastProcessedId,
            processedCount,
            totalCount,
            phase: 'processing',
            metadata: {},
          });

          // 進捗を通知
          await updateTaskProgress(taskId, processedCount, totalCount);

          console.log('Checkpoint saved', { processedCount, totalCount });
        }
      }
    }
  } catch (error) {
    console.error('Job failed', { taskId, error });

    // エラー時もチェックポイントを保存（リトライ可能に）
    const checkpoint = await checkpointManager.load(taskId);
    if (checkpoint) {
      await checkpointManager.save({
        ...checkpoint,
        phase: 'error',
        metadata: {
          ...checkpoint.metadata,
          lastError: error instanceof Error ? error.message : 'Unknown error',
          errorAt: new Date().toISOString(),
        },
      });
    }

    throw error;
  }
}

async function scheduleNextJobExecution(taskId: string): Promise<void> {
  const { CloudSchedulerClient } = await import('@google-cloud/scheduler');
  const scheduler = new CloudSchedulerClient();

  // Cloud Run Jobs を再実行
  // 実際にはCloud Run Jobs APIを使用
  const { v2 } = await import('@google-cloud/run');
  const jobsClient = new v2.JobsClient();

  await jobsClient.runJob({
    name: `projects/${process.env.GCP_PROJECT_ID}/locations/${process.env.GCP_REGION}/jobs/batch-processor`,
    overrides: {
      containerOverrides: [
        {
          env: [{ name: 'TASK_ID', value: taskId }],
        },
      ],
    },
  });
}

// エントリポイント
main().catch((error) => {
  console.error('Fatal error', error);
  process.exit(1);
});
```

### Pub/Sub を使用したイテレーション処理

Pub/Sub を使用して、アイテムを1つずつ処理し、失敗時に自動リトライする仕組みです。

```typescript
// services/pubsub-iterator.ts
import { PubSub, Message } from '@google-cloud/pubsub';
import { Firestore, FieldValue } from '@google-cloud/firestore';

const pubsub = new PubSub();
const firestore = new Firestore();

interface IterationMessage {
  taskId: string;
  itemId: string;
  itemIndex: number;
  totalItems: number;
  retryCount: number;
}

// イテレーションの開始
export async function startIteration(
  taskId: string,
  itemIds: string[]
): Promise<void> {
  const topic = pubsub.topic('task-items');
  const totalItems = itemIds.length;

  // 進捗追跡用のドキュメントを作成
  await firestore.collection('iterationProgress').doc(taskId).set({
    totalItems,
    processedItems: 0,
    failedItems: 0,
    startedAt: FieldValue.serverTimestamp(),
    status: 'processing',
  });

  // 各アイテムをPub/Subに送信
  const publishPromises = itemIds.map((itemId, index) =>
    topic.publishMessage({
      json: {
        taskId,
        itemId,
        itemIndex: index,
        totalItems,
        retryCount: 0,
      } as IterationMessage,
      orderingKey: taskId,
    })
  );

  await Promise.all(publishPromises);
  console.log(`Published ${totalItems} items for task ${taskId}`);
}

// 個別アイテムの処理（Pub/Subサブスクライバー）
export async function processIterationItem(message: Message): Promise<void> {
  const data: IterationMessage = JSON.parse(message.data.toString());
  const { taskId, itemId, itemIndex, totalItems, retryCount } = data;

  const MAX_RETRIES = 3;

  try {
    // アイテムを処理
    await processItem(itemId);

    // 進捗を更新
    await updateIterationProgress(taskId, 'success');

    message.ack();

  } catch (error) {
    console.error('Failed to process item', { taskId, itemId, error });

    if (retryCount < MAX_RETRIES) {
      // リトライ用のメッセージを再発行
      const topic = pubsub.topic('task-items');
      await topic.publishMessage({
        json: {
          ...data,
          retryCount: retryCount + 1,
        },
        orderingKey: taskId,
      });
      message.ack();
    } else {
      // 最大リトライ超過
      await updateIterationProgress(taskId, 'failed', itemId);
      await recordFailedItem(taskId, itemId, error);
      message.ack();
    }
  }

  // 完了チェック
  await checkIterationCompletion(taskId);
}

async function updateIterationProgress(
  taskId: string,
  result: 'success' | 'failed',
  itemId?: string
): Promise<void> {
  const progressRef = firestore.collection('iterationProgress').doc(taskId);

  if (result === 'success') {
    await progressRef.update({
      processedItems: FieldValue.increment(1),
      updatedAt: FieldValue.serverTimestamp(),
    });
  } else {
    await progressRef.update({
      failedItems: FieldValue.increment(1),
      updatedAt: FieldValue.serverTimestamp(),
    });
  }
}

async function checkIterationCompletion(taskId: string): Promise<void> {
  const progressDoc = await firestore
    .collection('iterationProgress')
    .doc(taskId)
    .get();

  if (!progressDoc.exists) return;

  const progress = progressDoc.data()!;
  const completedItems = progress.processedItems + progress.failedItems;

  if (completedItems >= progress.totalItems) {
    // 完了
    await progressDoc.ref.update({
      status: progress.failedItems > 0 ? 'completed_with_errors' : 'completed',
      completedAt: FieldValue.serverTimestamp(),
    });

    // タスク完了を通知
    await markTaskCompleted(taskId, {
      processedItems: progress.processedItems,
      failedItems: progress.failedItems,
      totalItems: progress.totalItems,
    });
  }
}
```

### Cloud Tasks によるセルフチェーン処理

Cloud Tasks を使用して、処理を小さなチャンクに分割し、自動的に次のチャンクをスケジュールします。

```typescript
// services/self-chaining-processor.ts
import { CloudTasksClient } from '@google-cloud/tasks';
import { Firestore, FieldValue } from '@google-cloud/firestore';

const tasksClient = new CloudTasksClient();
const firestore = new Firestore();

interface ChainState {
  taskId: string;
  userId: string;
  phase: string;
  cursor: string | null;
  processedCount: number;
  totalCount: number;
  startedAt: string;
  metadata: Record<string, unknown>;
}

const ITEMS_PER_CHUNK = 500;
const MAX_CHUNK_DURATION_MS = 8 * 60 * 1000; // 8分

export async function processChunk(state: ChainState): Promise<{
  completed: boolean;
  nextState?: ChainState;
}> {
  const startTime = Date.now();
  let cursor = state.cursor;
  let processedInChunk = 0;

  try {
    // バッチを取得
    const items = await fetchItems(state.taskId, cursor, ITEMS_PER_CHUNK);

    if (items.length === 0) {
      return { completed: true };
    }

    for (const item of items) {
      // タイムアウトチェック
      if (Date.now() - startTime > MAX_CHUNK_DURATION_MS) {
        // 時間切れ、次のチャンクをスケジュール
        const nextState: ChainState = {
          ...state,
          cursor,
          processedCount: state.processedCount + processedInChunk,
        };

        await scheduleNextChunk(nextState);
        await saveProgress(nextState);

        return { completed: false, nextState };
      }

      await processItem(item);
      cursor = item.id;
      processedInChunk++;
    }

    // バッチ完了
    const newProcessedCount = state.processedCount + processedInChunk;

    if (items.length < ITEMS_PER_CHUNK) {
      // 全完了
      return { completed: true };
    }

    // 次のチャンクをスケジュール
    const nextState: ChainState = {
      ...state,
      cursor,
      processedCount: newProcessedCount,
    };

    await scheduleNextChunk(nextState);
    await saveProgress(nextState);

    return { completed: false, nextState };

  } catch (error) {
    // エラー時は状態を保存して終了
    await saveProgress({
      ...state,
      cursor,
      processedCount: state.processedCount + processedInChunk,
      metadata: {
        ...state.metadata,
        lastError: error instanceof Error ? error.message : 'Unknown error',
      },
    });
    throw error;
  }
}

async function scheduleNextChunk(state: ChainState): Promise<void> {
  const parent = tasksClient.queuePath(
    process.env.GCP_PROJECT_ID!,
    process.env.GCP_REGION!,
    'task-chain-queue'
  );

  const taskName = `${parent}/tasks/${state.taskId}-chunk-${Date.now()}`;

  await tasksClient.createTask({
    parent,
    task: {
      name: taskName,
      scheduleTime: {
        seconds: Math.floor(Date.now() / 1000) + 1, // 1秒後
      },
      httpRequest: {
        httpMethod: 'POST',
        url: `${process.env.WORKER_URL}/internal/process-chunk`,
        headers: { 'Content-Type': 'application/json' },
        body: Buffer.from(JSON.stringify(state)).toString('base64'),
        oidcToken: {
          serviceAccountEmail: process.env.SERVICE_ACCOUNT_EMAIL,
        },
      },
    },
  });
}

async function saveProgress(state: ChainState): Promise<void> {
  await firestore.collection('chainProgress').doc(state.taskId).set({
    ...state,
    updatedAt: FieldValue.serverTimestamp(),
  });

  // リアルタイム通知
  await firestore.collection('tasks').doc(state.taskId).update({
    progress: state.processedCount,
    totalItems: state.totalCount,
    updatedAt: FieldValue.serverTimestamp(),
  });
}
```

### コールバックパターン（外部システム連携）

外部システムの応答を待つ必要がある場合に、Cloud Workflowsのコールバック機能を使用します。

```yaml
# workflows/with-external-callback.yaml
main:
  params: [input]
  steps:
    - init:
        assign:
          - taskId: ${input.taskId}
          - callbackUrl: ""
          - callbackToken: ""

    - createCallback:
        call: events.create_callback_endpoint
        args:
          http_callback_method: "POST"
        result: callback

    - storeCallback:
        assign:
          - callbackUrl: ${callback.url}

    - requestExternalProcessing:
        call: http.post
        args:
          url: ${sys.get_env("EXTERNAL_SERVICE_URL") + "/process"}
          body:
            taskId: ${taskId}
            callbackUrl: ${callbackUrl}
            data: ${input.data}
          timeout: 30

    - waitForCallback:
        call: events.await_callback
        args:
          callback: ${callback}
          timeout: 86400  # 24時間待機
        result: callbackResult

    - processResult:
        switch:
          - condition: ${callbackResult.body.status == "success"}
            steps:
              - markSuccess:
                  call: http.post
                  args:
                    url: ${sys.get_env("WORKER_URL") + "/internal/tasks/" + taskId + "/complete"}
                    body:
                      result: ${callbackResult.body.result}
                    auth:
                      type: OIDC
          - condition: ${callbackResult.body.status == "failed"}
            steps:
              - markFailure:
                  call: http.post
                  args:
                    url: ${sys.get_env("WORKER_URL") + "/internal/tasks/" + taskId + "/fail"}
                    body:
                      error: ${callbackResult.body.error}
                    auth:
                      type: OIDC

    - return:
        return: ${callbackResult.body}
```

### 手法の比較と選択ガイド

| 観点 | Cloud Workflows | Cloud Run Jobs | Pub/Sub イテレーション | Cloud Tasks チェーン |
|------|-----------------|----------------|----------------------|---------------------|
| ユースケース | 複雑なワークフロー | 長時間バッチ処理 | 大量アイテム並列処理 | 順次処理の分割 |
| 最大処理時間 | 1年（待機含む） | 24時間 | 制限なし | 制限なし |
| スケーラビリティ | 中 | 低〜中 | 非常に高 | 中 |
| 自動チェックポイント | あり | なし（手動実装） | なし（メッセージ単位） | なし（手動実装） |
| コスト | ステップ数課金 | 実行時間課金 | メッセージ数課金 | タスク数課金 |
| 複雑さ | 中〜高（YAML） | 低〜中 | 中 | 中 |
| エラー回復 | 自動再開 | チェックポイントから | アイテム単位リトライ | タスクリトライ |

**選択ガイド:**

- **Cloud Workflows**: 複数のステップを持つ複雑なワークフロー、外部システム連携が必要な場合
- **Cloud Run Jobs**: 単一の長時間バッチ処理、スケジュール実行が必要な場合
- **Pub/Sub イテレーション**: 大量のアイテムを独立して並列処理する場合
- **Cloud Tasks チェーン**: 順序が重要で、処理時間が予測困難な場合

---

## テスト戦略

### ユニットテスト

```typescript
// __tests__/handlers/task-processor.test.ts
import { Request, Response } from 'express';
import { processTask } from '../../handlers/task-processor';
import { TaskStateManager } from '../../services/task-state-manager';

jest.mock('../../services/task-state-manager');

describe('TaskProcessor', () => {
  let mockReq: Partial<Request>;
  let mockRes: Partial<Response>;
  let mockStateManager: jest.Mocked<TaskStateManager>;

  beforeEach(() => {
    jest.clearAllMocks();

    mockRes = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn(),
      setHeader: jest.fn(),
    };

    mockStateManager = new TaskStateManager() as jest.Mocked<TaskStateManager>;
  });

  it('should process task successfully', async () => {
    mockReq = {
      body: {
        taskId: 'test-task-id',
        taskType: 'export',
        userId: 'user-123',
        params: { operation: 'csv' },
      },
      headers: {
        'x-cloudtasks-taskretrycount': '0',
      },
    };

    await processTask(mockReq as Request, mockRes as Response);

    expect(mockRes.status).toHaveBeenCalledWith(200);
    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({ success: true })
    );
  });

  it('should return 200 for non-retryable errors', async () => {
    mockReq = {
      body: {
        taskId: 'test-task-id',
        // Invalid payload
      },
      headers: {},
    };

    await processTask(mockReq as Request, mockRes as Response);

    expect(mockRes.status).toHaveBeenCalledWith(200);
    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        retryable: false,
      })
    );
  });

  it('should return 500 for retryable errors', async () => {
    mockReq = {
      body: {
        taskId: 'test-task-id',
        taskType: 'export',
        userId: 'user-123',
        params: { operation: 'csv' },
      },
      headers: {},
    };

    // 外部サービスエラーをシミュレート
    jest.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Connection timeout'));

    await processTask(mockReq as Request, mockRes as Response);

    expect(mockRes.status).toHaveBeenCalledWith(500);
    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({ retryable: true })
    );
  });
});
```

### Firestoreエミュレータを使用した統合テスト

```typescript
// __tests__/integration/firestore.test.ts
import {
  initializeTestEnvironment,
  RulesTestEnvironment,
} from '@firebase/rules-unit-testing';
import { TaskStateManager, TaskStatus } from '../../services/task-state-manager';

describe('TaskStateManager Integration', () => {
  let testEnv: RulesTestEnvironment;
  let stateManager: TaskStateManager;

  beforeAll(async () => {
    testEnv = await initializeTestEnvironment({
      projectId: 'test-project',
      firestore: {
        host: 'localhost',
        port: 8080,
      },
    });
  });

  beforeEach(async () => {
    await testEnv.clearFirestore();
    stateManager = new TaskStateManager();
  });

  afterAll(async () => {
    await testEnv.cleanup();
  });

  it('should create and update task', async () => {
    const taskId = 'test-task';
    const userId = 'user-123';

    await stateManager.createTask(taskId, userId, 'export', {});

    const task = await stateManager.getTask(taskId);
    expect(task).not.toBeNull();
    expect(task?.status).toBe(TaskStatus.PENDING);

    await stateManager.updateProgress(taskId, 50, 100);

    const updatedTask = await stateManager.getTask(taskId);
    expect(updatedTask?.progress).toBe(50);
    expect(updatedTask?.totalItems).toBe(100);
  });

  it('should complete task with result', async () => {
    const taskId = 'test-task';
    await stateManager.createTask(taskId, 'user-123', 'export', {});

    const result = { items: 100, file: 'output.csv' };
    await stateManager.markCompleted(taskId, result);

    const task = await stateManager.getTask(taskId);
    expect(task?.status).toBe(TaskStatus.COMPLETED);
    expect(task?.result).toEqual(result);
  });
});
```

### E2Eテスト

```typescript
// __tests__/e2e/task-flow.test.ts
import axios from 'axios';

const API_URL = process.env.API_URL || 'https://api.example.com';

describe('Task Flow E2E', () => {
  let authToken: string;

  beforeAll(async () => {
    authToken = await getAuthToken();
  });

  it('should complete task lifecycle', async () => {
    // 1. タスク作成
    const createResponse = await axios.post(
      `${API_URL}/api/tasks`,
      {
        type: 'export',
        params: { format: 'csv' },
      },
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );

    expect(createResponse.status).toBe(201);
    const taskId = createResponse.data.taskId;

    // 2. SSEで進捗を監視
    const updates: any[] = [];

    const eventSource = new EventSource(
      `${API_URL}/api/tasks/${taskId}/stream`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );

    const completionPromise = new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        eventSource.close();
        reject(new Error('Timeout waiting for task completion'));
      }, 60000);

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updates.push(data);

        if (data.status === 'completed') {
          clearTimeout(timeout);
          eventSource.close();
          resolve();
        }

        if (data.status === 'failed') {
          clearTimeout(timeout);
          eventSource.close();
          reject(new Error(data.error));
        }
      };
    });

    await completionPromise;

    // 3. 結果を確認
    expect(updates.length).toBeGreaterThan(0);
    expect(updates[updates.length - 1].status).toBe('completed');
  });
});
```

---

## その他のベストプラクティス

### 構造化ログ

```typescript
// utils/logger.ts
import { LoggingBunyan } from '@google-cloud/logging-bunyan';
import bunyan from 'bunyan';

const loggingBunyan = new LoggingBunyan();

export const logger = bunyan.createLogger({
  name: 'task-worker',
  streams: [
    { stream: process.stdout, level: 'info' },
    loggingBunyan.stream('info'),
  ],
});

export function createTaskLogger(taskId: string, userId: string) {
  return logger.child({
    taskId,
    userId,
    service: 'task-worker',
  });
}

// 使用例
const log = createTaskLogger(taskId, userId);
log.info({ progress: 50, totalItems: 100 }, 'Processing task');
log.error({ error: error.message }, 'Task failed');
```

### メトリクス収集

```typescript
// services/metrics.ts
import { Monitoring } from '@google-cloud/monitoring';

const monitoring = new Monitoring.MetricServiceClient();
const projectPath = monitoring.projectPath(process.env.GCP_PROJECT_ID!);

export async function recordMetric(
  metricType: string,
  value: number,
  labels?: Record<string, string>
): Promise<void> {
  const dataPoint = {
    interval: {
      endTime: {
        seconds: Math.floor(Date.now() / 1000),
      },
    },
    value: {
      doubleValue: value,
    },
  };

  const timeSeriesData = {
    metric: {
      type: `custom.googleapis.com/task/${metricType}`,
      labels: labels || {},
    },
    resource: {
      type: 'cloud_run_revision',
      labels: {
        service_name: process.env.K_SERVICE || 'unknown',
        revision_name: process.env.K_REVISION || 'unknown',
        location: process.env.GCP_REGION || 'unknown',
      },
    },
    points: [dataPoint],
  };

  await monitoring.createTimeSeries({
    name: projectPath,
    timeSeries: [timeSeriesData],
  });
}

// 使用例
await recordMetric('duration_seconds', 5.2, { taskType: 'export' });
await recordMetric('items_processed', 1000, { taskType: 'export' });
```

### コールドスタート対策

```typescript
// index.ts
import express from 'express';

// グローバルで初期化（コールドスタート時に一度だけ）
const app = express();
const stateManager = new TaskStateManager();
const idempotencyManager = new IdempotencyManager();

// ミドルウェア
app.use(express.json());

// ウォームアップエンドポイント
app.get('/_warmup', (req, res) => {
  res.status(200).send('OK');
});

// ヘルスチェック
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

// タスク処理エンドポイント
app.post('/tasks/process', authenticateCloudTasks, processTask);

const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
```

### 最小インスタンス設定

```yaml
# cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: task-worker
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"  # 最小1インスタンス
        autoscaling.knative.dev/maxScale: "100"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 600  # 10分
      containers:
        - image: gcr.io/PROJECT_ID/task-worker
          resources:
            limits:
              cpu: "2"
              memory: "2Gi"
          env:
            - name: GCP_PROJECT_ID
              value: "PROJECT_ID"
```

---

## 参照

- [Cloud Run Best Practices](https://cloud.google.com/run/docs/tips/general)
- [Cloud Tasks Documentation](https://cloud.google.com/tasks/docs)
- [Firestore Best Practices](https://firebase.google.com/docs/firestore/best-practices)
- [Cloud Workflows Documentation](https://cloud.google.com/workflows/docs)
- [Cloud Workflows Callbacks](https://cloud.google.com/workflows/docs/creating-callback-endpoints)
- [Cloud Run Jobs Documentation](https://cloud.google.com/run/docs/create-jobs)
- [Pub/Sub Ordering](https://cloud.google.com/pubsub/docs/ordering)
