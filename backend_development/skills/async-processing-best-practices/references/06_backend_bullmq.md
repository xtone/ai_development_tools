# TypeScript BullMQ バックエンド実装ベストプラクティス

TypeScriptとBullMQを使用した非同期処理のバックエンド実装におけるベストプラクティスをまとめます。

## 目次

1. [パラメータの受け取り方](#パラメータの受け取り方)
2. [エラー発生時の処理と通知](#エラー発生時の処理と通知)
3. [進捗の状態管理](#進捗の状態管理)
4. [ジョブの設計パターン](#ジョブの設計パターン)
5. [継続可能なジョブ（Graceful Shutdown & Checkpointing）](#継続可能なジョブgraceful-shutdown--checkpointing)
6. [テスト戦略](#テスト戦略)

---

## パラメータの受け取り方

### 基本原則

BullMQのジョブデータはJSON形式でRedisに保存されるため、シリアライズ可能なデータのみを渡す必要があります。

```typescript
// types/job.ts
interface JobData {
  // IDベースで参照（推奨）
  userId: string;
  orderId: string;

  // プリミティブ型のパラメータ
  options: {
    priority: number;
    notifyOnComplete: boolean;
  };

  // メタデータ
  requestedAt: string; // ISO8601形式
  requestedBy: string;
}

// ❌ 悪い例: 大きなオブジェクトや循環参照を含むデータ
interface BadJobData {
  fullUserObject: User; // DBから取得したオブジェクトをそのまま
  fileContent: Buffer;  // バイナリデータ
  callback: () => void; // 関数は渡せない
}

// ✅ 良い例: IDと必要最小限のパラメータ
interface GoodJobData {
  userId: string;
  fileStorageKey: string; // ファイルはS3等に保存してキーを渡す
  operationType: 'process' | 'export' | 'analyze';
}
```

### パラメータサイズの制限

Redisの文字列最大サイズは512MBですが、実用上はジョブデータを数KB以下に抑えることを推奨します。

```typescript
// utils/job-validator.ts
const MAX_JOB_DATA_SIZE = 64 * 1024; // 64KB

export function validateJobData<T>(data: T): void {
  const serialized = JSON.stringify(data);

  if (serialized.length > MAX_JOB_DATA_SIZE) {
    throw new JobDataTooLargeError(
      `Job data size (${serialized.length} bytes) exceeds maximum (${MAX_JOB_DATA_SIZE} bytes)`
    );
  }
}

// ジョブ追加時にバリデーション
async function addJob(queue: Queue, data: JobData): Promise<Job> {
  validateJobData(data);

  return queue.add('process', data, {
    removeOnComplete: 100,
    removeOnFail: 1000,
  });
}
```

### 大きなパラメータの処理

```typescript
// services/file-processor.ts
import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { Queue, Job } from 'bullmq';

interface FileProcessJobData {
  taskId: string;
  inputFileKey: string;  // S3キー
  outputFileKey: string;
  processingOptions: ProcessingOptions;
}

// ❌ 悪い例: ファイル内容を直接渡す
async function addBadJob(fileContent: Buffer) {
  await queue.add('process', {
    content: fileContent.toString('base64'), // 巨大な文字列
  });
}

// ✅ 良い例: ファイルをS3にアップロードしてキーを渡す
async function addFileProcessJob(
  file: Buffer,
  options: ProcessingOptions
): Promise<string> {
  const taskId = generateTaskId();
  const inputKey = `uploads/${taskId}/input`;
  const outputKey = `outputs/${taskId}/result`;

  // ファイルをS3にアップロード
  await s3Client.send(new PutObjectCommand({
    Bucket: process.env.S3_BUCKET,
    Key: inputKey,
    Body: file,
  }));

  // ジョブには参照キーのみを渡す
  await queue.add('file-process', {
    taskId,
    inputFileKey: inputKey,
    outputFileKey: outputKey,
    processingOptions: options,
  });

  return taskId;
}

// ワーカーでの処理
async function processFileJob(job: Job<FileProcessJobData>): Promise<void> {
  const { inputFileKey, outputFileKey, processingOptions } = job.data;

  // S3からファイルを取得
  const response = await s3Client.send(new GetObjectCommand({
    Bucket: process.env.S3_BUCKET,
    Key: inputFileKey,
  }));

  const fileContent = await streamToBuffer(response.Body);

  // 処理実行
  const result = await processFile(fileContent, processingOptions);

  // 結果をS3に保存
  await s3Client.send(new PutObjectCommand({
    Bucket: process.env.S3_BUCKET,
    Key: outputFileKey,
    Body: result,
  }));
}
```

### 大量のIDリストを処理する場合

```typescript
// services/bulk-processor.ts
interface BulkJobData {
  taskId: string;
  batchIndex: number;
  userIds: string[];
}

const BATCH_SIZE = 100;

// 大量のIDを分割してジョブを作成
async function createBulkJobs(
  allUserIds: string[],
  taskId: string
): Promise<void> {
  const batches: BulkJobData[] = [];

  for (let i = 0; i < allUserIds.length; i += BATCH_SIZE) {
    const batch = allUserIds.slice(i, i + BATCH_SIZE);
    batches.push({
      taskId,
      batchIndex: Math.floor(i / BATCH_SIZE),
      userIds: batch,
    });
  }

  // バルクでジョブを追加
  await queue.addBulk(
    batches.map((data, index) => ({
      name: 'bulk-process',
      data,
      opts: {
        priority: index, // 順序を保持
      },
    }))
  );

  // タスクの総バッチ数を記録
  await updateTask(taskId, { totalBatches: batches.length });
}

// または、DBに対象を保存してクエリ条件を渡す
interface QueryBasedJobData {
  taskId: string;
  queryConditions: {
    createdAfter?: string;
    status?: string[];
    limit?: number;
    offset?: number;
  };
}

async function processQueryBasedJob(job: Job<QueryBasedJobData>): Promise<void> {
  const { taskId, queryConditions } = job.data;

  // DBから対象を取得
  const users = await prisma.user.findMany({
    where: {
      createdAt: queryConditions.createdAfter
        ? { gte: new Date(queryConditions.createdAfter) }
        : undefined,
      status: queryConditions.status
        ? { in: queryConditions.status }
        : undefined,
    },
    take: queryConditions.limit,
    skip: queryConditions.offset,
  });

  for (const user of users) {
    await processUser(user);
    await job.updateProgress(/* ... */);
  }
}
```

### 型安全なジョブデータの定義

```typescript
// types/jobs.ts
import { z } from 'zod';

// Zodスキーマでバリデーション
export const FileProcessJobSchema = z.object({
  taskId: z.string().uuid(),
  inputFileKey: z.string().min(1),
  outputFileKey: z.string().min(1),
  processingOptions: z.object({
    format: z.enum(['json', 'csv', 'xml']),
    compression: z.boolean().default(false),
  }),
});

export type FileProcessJobData = z.infer<typeof FileProcessJobSchema>;

// ジョブ追加時のバリデーション
async function addValidatedJob(
  queue: Queue,
  data: unknown
): Promise<Job<FileProcessJobData>> {
  const validated = FileProcessJobSchema.parse(data);

  return queue.add('file-process', validated);
}

// ワーカーでのバリデーション
const worker = new Worker('file-processing', async (job) => {
  // ジョブデータをバリデーション
  const data = FileProcessJobSchema.parse(job.data);

  // 型安全に処理
  await processFile(data.inputFileKey, data.processingOptions);
});
```

---

## エラー発生時の処理と通知

### リトライ設定

```typescript
// queues/config.ts
import { Queue, Worker, QueueEvents } from 'bullmq';

// キューの作成（リトライ設定付き）
const queue = new Queue('data-processing', {
  connection: redisConnection,
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'exponential',
      delay: 1000, // 初回1秒、以降2秒、4秒、8秒、16秒
    },
    removeOnComplete: {
      count: 1000,  // 完了したジョブは1000件まで保持
      age: 24 * 3600, // または24時間
    },
    removeOnFail: {
      count: 5000,  // 失敗したジョブは5000件まで保持
    },
  },
});

// ジョブごとにカスタムリトライ設定
await queue.add('external-api-call', jobData, {
  attempts: 10,
  backoff: {
    type: 'custom',
  },
});

// ワーカーでカスタムバックオフ計算
const worker = new Worker('data-processing', processor, {
  settings: {
    backoffStrategy: (attemptsMade: number) => {
      // カスタムバックオフロジック
      const delays = [1000, 2000, 5000, 10000, 30000, 60000];
      return delays[Math.min(attemptsMade - 1, delays.length - 1)];
    },
  },
});
```

### 詳細なエラーハンドリング

```typescript
// workers/data-processor.ts
import { Worker, Job } from 'bullmq';
import { ErrorNotifier } from '../services/error-notifier';

// カスタムエラークラス
class RetryableError extends Error {
  constructor(message: string, public readonly retryAfter?: number) {
    super(message);
    this.name = 'RetryableError';
  }
}

class FatalError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FatalError';
  }
}

interface ProcessingResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

const worker = new Worker<JobData, ProcessingResult>(
  'data-processing',
  async (job) => {
    const task = await getTask(job.data.taskId);

    try {
      await updateTask(task.id, {
        status: 'processing',
        startedAt: new Date(),
        attemptNumber: job.attemptsMade + 1,
      });

      const result = await processData(job.data);

      await updateTask(task.id, {
        status: 'completed',
        completedAt: new Date(),
        result,
      });

      await notifyCompletion(task);

      return { success: true, data: result };

    } catch (error) {
      if (error instanceof FatalError) {
        // リトライ不要なエラー
        await updateTask(task.id, {
          status: 'failed',
          completedAt: new Date(),
          lastError: error.message,
        });
        await notifyFailure(task, error);

        // UnrecoverableErrorをスローするとリトライされない
        throw new UnrecoverableError(error.message);
      }

      if (error instanceof RetryableError) {
        // リトライ可能なエラー
        await updateTask(task.id, {
          status: 'retrying',
          lastError: error.message,
          retryCount: (task.retryCount || 0) + 1,
        });

        // エラーをそのまま再スロー（リトライされる）
        throw error;
      }

      // その他のエラー
      await updateTask(task.id, {
        status: 'failed',
        lastError: `${error.name}: ${error.message}`,
      });

      throw error;
    }
  },
  {
    connection: redisConnection,
    concurrency: 5,
  }
);

// ワーカーイベントハンドリング
worker.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result);
});

worker.on('failed', (job, error) => {
  console.error(`Job ${job?.id} failed:`, error);

  // 最終リトライ後の失敗
  if (job && job.attemptsMade >= (job.opts.attempts || 1)) {
    ErrorNotifier.notifyFinalFailure(job, error);
  }
});
```

### エラー通知サービス

```typescript
// services/error-notifier.ts
import { Job } from 'bullmq';
import * as Sentry from '@sentry/node';

interface ErrorContext {
  jobId?: string;
  jobName?: string;
  attemptsMade?: number;
  data?: unknown;
}

export class ErrorNotifier {
  static async notify(
    error: Error,
    context: ErrorContext
  ): Promise<void> {
    // 構造化ログ出力
    console.error(JSON.stringify({
      event: 'job_error',
      timestamp: new Date().toISOString(),
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack?.split('\n').slice(0, 10),
      },
      context: this.sanitizeContext(context),
    }));

    // Sentryに送信
    Sentry.captureException(error, {
      tags: {
        jobName: context.jobName,
        jobId: context.jobId,
      },
      extra: this.sanitizeContext(context),
    });

    // 重大なエラーの場合はSlack通知
    if (this.isCriticalError(error)) {
      await this.sendSlackNotification(error, context);
    }
  }

  static async notifyFinalFailure(
    job: Job,
    error: Error
  ): Promise<void> {
    // すべてのリトライが失敗した場合の通知
    await this.notify(error, {
      jobId: job.id,
      jobName: job.name,
      attemptsMade: job.attemptsMade,
      data: job.data,
    });

    // Dead Letter Queue的な記録
    await this.recordDeadJob(job, error);
  }

  private static sanitizeContext(context: ErrorContext): ErrorContext {
    if (!context.data) return context;

    // センシティブなフィールドを除去
    const sensitiveFields = ['password', 'token', 'secret', 'apiKey'];
    const sanitized = { ...context };

    if (typeof sanitized.data === 'object' && sanitized.data !== null) {
      sanitized.data = Object.fromEntries(
        Object.entries(sanitized.data as Record<string, unknown>)
          .filter(([key]) => !sensitiveFields.some(f =>
            key.toLowerCase().includes(f.toLowerCase())
          ))
      );
    }

    return sanitized;
  }

  private static isCriticalError(error: Error): boolean {
    const criticalPatterns = [
      /ECONNREFUSED/,
      /ETIMEDOUT/,
      /database.*connection/i,
      /redis.*connection/i,
    ];

    return criticalPatterns.some(pattern =>
      pattern.test(error.message)
    );
  }

  private static async sendSlackNotification(
    error: Error,
    context: ErrorContext
  ): Promise<void> {
    // Slack Webhook送信
    await fetch(process.env.SLACK_WEBHOOK_URL!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: `:rotating_light: Job Failed: ${context.jobName}`,
        attachments: [{
          color: 'danger',
          fields: [
            { title: 'Job ID', value: context.jobId, short: true },
            { title: 'Attempts', value: String(context.attemptsMade), short: true },
            { title: 'Error', value: error.message },
          ],
        }],
      }),
    });
  }

  private static async recordDeadJob(
    job: Job,
    error: Error
  ): Promise<void> {
    // DBに失敗したジョブを記録
    await prisma.deadJob.create({
      data: {
        jobId: job.id || 'unknown',
        jobName: job.name,
        queueName: job.queueName,
        data: JSON.stringify(job.data),
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack,
        attemptsMade: job.attemptsMade,
        failedAt: new Date(),
      },
    });
  }
}
```

### QueueEventsによるイベント監視

```typescript
// services/queue-monitor.ts
import { QueueEvents } from 'bullmq';

const queueEvents = new QueueEvents('data-processing', {
  connection: redisConnection,
});

// ジョブ完了イベント
queueEvents.on('completed', async ({ jobId, returnvalue }) => {
  console.log(`Job ${jobId} completed with result:`, returnvalue);

  // メトリクス記録
  await recordMetric('job_completed', { jobId });
});

// ジョブ失敗イベント
queueEvents.on('failed', async ({ jobId, failedReason }) => {
  console.error(`Job ${jobId} failed:`, failedReason);

  // メトリクス記録
  await recordMetric('job_failed', { jobId, reason: failedReason });
});

// ジョブ進捗イベント
queueEvents.on('progress', async ({ jobId, data }) => {
  console.log(`Job ${jobId} progress:`, data);

  // WebSocketで進捗を配信
  await broadcastProgress(jobId, data);
});

// ジョブ遅延イベント
queueEvents.on('delayed', async ({ jobId, delay }) => {
  console.log(`Job ${jobId} delayed for ${delay}ms`);
});

// ジョブ停滞イベント（長時間処理中）
queueEvents.on('stalled', async ({ jobId }) => {
  console.warn(`Job ${jobId} has stalled`);

  // アラート送信
  await sendAlert(`Job ${jobId} has stalled and may need attention`);
});
```

---

## 進捗の状態管理

### 状態管理用データモデル

```typescript
// prisma/schema.prisma
/*
model AsyncTask {
  id            String    @id @default(uuid())
  userId        String
  taskType      String
  status        String    @default("pending")
  progress      Int       @default(0)
  totalItems    Int?
  params        Json      @default("{}")
  result        Json      @default("{}")
  lastError     String?
  retryCount    Int       @default(0)
  startedAt     DateTime?
  completedAt   DateTime?
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  @@index([userId, status])
  @@index([taskType, status])
}
*/

// types/task.ts
export enum TaskStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface AsyncTask {
  id: string;
  userId: string;
  taskType: string;
  status: TaskStatus;
  progress: number;
  totalItems: number | null;
  params: Record<string, unknown>;
  result: Record<string, unknown>;
  lastError: string | null;
  retryCount: number;
  startedAt: Date | null;
  completedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
}

// services/task-service.ts
export class TaskService {
  async createTask(
    userId: string,
    taskType: string,
    params: Record<string, unknown>
  ): Promise<AsyncTask> {
    return prisma.asyncTask.create({
      data: {
        userId,
        taskType,
        params,
        status: TaskStatus.PENDING,
      },
    });
  }

  async updateProgress(
    taskId: string,
    progress: number,
    totalItems?: number
  ): Promise<AsyncTask> {
    return prisma.asyncTask.update({
      where: { id: taskId },
      data: {
        progress,
        totalItems,
        status: TaskStatus.PROCESSING,
      },
    });
  }

  async markCompleted(
    taskId: string,
    result: Record<string, unknown>
  ): Promise<AsyncTask> {
    return prisma.asyncTask.update({
      where: { id: taskId },
      data: {
        status: TaskStatus.COMPLETED,
        result,
        completedAt: new Date(),
      },
    });
  }

  async markFailed(
    taskId: string,
    error: string
  ): Promise<AsyncTask> {
    return prisma.asyncTask.update({
      where: { id: taskId },
      data: {
        status: TaskStatus.FAILED,
        lastError: error,
        completedAt: new Date(),
      },
    });
  }

  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const task = await prisma.asyncTask.findUnique({
      where: { id: taskId },
    });

    if (!task) {
      throw new NotFoundError(`Task ${taskId} not found`);
    }

    return {
      id: task.id,
      status: task.status,
      progress: this.calculateProgressPercentage(task),
      estimatedRemainingSeconds: this.estimateRemainingTime(task),
      result: task.status === TaskStatus.COMPLETED ? task.result : null,
      error: task.status === TaskStatus.FAILED ? task.lastError : null,
      startedAt: task.startedAt?.toISOString() || null,
      completedAt: task.completedAt?.toISOString() || null,
    };
  }

  private calculateProgressPercentage(task: AsyncTask): number {
    if (!task.totalItems || task.totalItems === 0) return 0;
    return Math.min(Math.round((task.progress / task.totalItems) * 100), 100);
  }

  private estimateRemainingTime(task: AsyncTask): number | null {
    if (
      task.status !== TaskStatus.PROCESSING ||
      !task.startedAt ||
      !task.totalItems ||
      task.progress === 0
    ) {
      return null;
    }

    const elapsed = Date.now() - task.startedAt.getTime();
    const rate = task.progress / elapsed;
    const remaining = task.totalItems - task.progress;

    return Math.round(remaining / rate / 1000);
  }
}
```

### 進捗更新を含むワーカー実装

```typescript
// workers/bulk-processor.ts
import { Worker, Job } from 'bullmq';
import { TaskService } from '../services/task-service';
import { WebSocketServer } from '../services/websocket-server';

interface BulkProcessJobData {
  taskId: string;
  batchSize?: number;
}

const PROGRESS_UPDATE_INTERVAL = 10;
const CANCELLATION_CHECK_INTERVAL = 100;

const taskService = new TaskService();
const wsServer = new WebSocketServer();

const worker = new Worker<BulkProcessJobData>(
  'bulk-processing',
  async (job) => {
    const { taskId, batchSize = 100 } = job.data;

    // タスク取得
    const task = await prisma.asyncTask.findUnique({
      where: { id: taskId },
    });

    if (!task) {
      throw new Error(`Task ${taskId} not found`);
    }

    // キャンセルチェック
    if (task.status === 'cancelled') {
      return { cancelled: true };
    }

    // 処理対象の取得
    const items = await getItemsToProcess(task.params);
    const totalItems = items.length;

    // タスク開始
    await taskService.updateProgress(taskId, 0, totalItems);
    await broadcastProgress(task.userId, taskId, 0, totalItems);

    let processed = 0;

    for (const item of items) {
      // キャンセルチェック
      if (processed % CANCELLATION_CHECK_INTERVAL === 0) {
        const currentTask = await prisma.asyncTask.findUnique({
          where: { id: taskId },
          select: { status: true },
        });

        if (currentTask?.status === 'cancelled') {
          await job.updateProgress({
            status: 'cancelled',
            processed,
            total: totalItems,
          });
          return { cancelled: true, processedItems: processed };
        }
      }

      // アイテム処理
      await processItem(item);
      processed++;

      // 進捗更新
      if (processed % PROGRESS_UPDATE_INTERVAL === 0) {
        await taskService.updateProgress(taskId, processed, totalItems);

        // BullMQの進捗更新（QueueEventsでキャッチ可能）
        await job.updateProgress({
          processed,
          total: totalItems,
          percentage: Math.round((processed / totalItems) * 100),
        });

        // WebSocket経由でリアルタイム通知
        await broadcastProgress(task.userId, taskId, processed, totalItems);
      }
    }

    // 完了
    const result = { processedItems: processed, totalItems };
    await taskService.markCompleted(taskId, result);
    await broadcastCompletion(task.userId, taskId, result);

    return result;
  },
  {
    connection: redisConnection,
    concurrency: 3,
  }
);

async function broadcastProgress(
  userId: string,
  taskId: string,
  processed: number,
  total: number
): Promise<void> {
  const message = {
    type: 'progress',
    taskId,
    progress: {
      processed,
      total,
      percentage: Math.round((processed / total) * 100),
    },
    timestamp: new Date().toISOString(),
  };

  wsServer.sendToUser(userId, message);
}

async function broadcastCompletion(
  userId: string,
  taskId: string,
  result: Record<string, unknown>
): Promise<void> {
  const message = {
    type: 'completed',
    taskId,
    result,
    timestamp: new Date().toISOString(),
  };

  wsServer.sendToUser(userId, message);
}
```

### Socket.IOによるリアルタイム通知

```typescript
// services/websocket-server.ts
import { Server as SocketIOServer, Socket } from 'socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import { createClient } from 'redis';

export class WebSocketServer {
  private io: SocketIOServer;

  async initialize(httpServer: http.Server): Promise<void> {
    this.io = new SocketIOServer(httpServer, {
      cors: {
        origin: process.env.FRONTEND_URL,
        credentials: true,
      },
    });

    // Redis Adapterでスケールアウト対応
    const pubClient = createClient({ url: process.env.REDIS_URL });
    const subClient = pubClient.duplicate();

    await Promise.all([pubClient.connect(), subClient.connect()]);

    this.io.adapter(createAdapter(pubClient, subClient));

    this.io.on('connection', this.handleConnection.bind(this));
  }

  private handleConnection(socket: Socket): void {
    console.log(`Client connected: ${socket.id}`);

    // 認証
    socket.on('authenticate', async (token: string) => {
      try {
        const user = await verifyToken(token);
        socket.data.userId = user.id;
        socket.join(`user:${user.id}`);
        socket.emit('authenticated', { userId: user.id });
      } catch (error) {
        socket.emit('error', { message: 'Authentication failed' });
        socket.disconnect();
      }
    });

    // タスク購読
    socket.on('subscribe:task', (taskId: string) => {
      if (!socket.data.userId) {
        socket.emit('error', { message: 'Not authenticated' });
        return;
      }

      socket.join(`task:${taskId}`);
    });

    // タスク購読解除
    socket.on('unsubscribe:task', (taskId: string) => {
      socket.leave(`task:${taskId}`);
    });

    socket.on('disconnect', () => {
      console.log(`Client disconnected: ${socket.id}`);
    });
  }

  sendToUser(userId: string, message: unknown): void {
    this.io.to(`user:${userId}`).emit('task:update', message);
  }

  sendToTask(taskId: string, message: unknown): void {
    this.io.to(`task:${taskId}`).emit('task:update', message);
  }
}
```

### REST APIによるポーリング

```typescript
// routes/tasks.ts
import { Router } from 'express';
import { TaskService } from '../services/task-service';

const router = Router();
const taskService = new TaskService();

// タスクステータス取得
router.get('/:taskId/status', async (req, res) => {
  try {
    const status = await taskService.getTaskStatus(req.params.taskId);

    // キャッシュ制御
    if (status.status === 'completed' || status.status === 'failed') {
      res.set('Cache-Control', 'public, max-age=3600');
    } else {
      res.set('Cache-Control', 'no-cache');
    }

    res.json(status);
  } catch (error) {
    if (error instanceof NotFoundError) {
      res.status(404).json({ error: 'Task not found' });
    } else {
      throw error;
    }
  }
});

// SSE（Server-Sent Events）エンドポイント
router.get('/:taskId/stream', async (req, res) => {
  const { taskId } = req.params;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  const sendEvent = (data: unknown) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  // 初期状態を送信
  const initialStatus = await taskService.getTaskStatus(taskId);
  sendEvent(initialStatus);

  if (['completed', 'failed', 'cancelled'].includes(initialStatus.status)) {
    res.end();
    return;
  }

  // Redis Pub/Subで更新を購読
  const subscriber = createClient({ url: process.env.REDIS_URL });
  await subscriber.connect();

  const channel = `task:${taskId}:updates`;

  await subscriber.subscribe(channel, (message) => {
    const data = JSON.parse(message);
    sendEvent(data);

    if (['completed', 'failed', 'cancelled'].includes(data.status)) {
      subscriber.unsubscribe(channel);
      subscriber.quit();
      res.end();
    }
  });

  // クライアント切断時のクリーンアップ
  req.on('close', () => {
    subscriber.unsubscribe(channel);
    subscriber.quit();
  });
});

export default router;
```

---

## ジョブの設計パターン

### 冪等性の確保

```typescript
// workers/idempotent-processor.ts
import { Worker, Job, UnrecoverableError } from 'bullmq';
import { createHash } from 'crypto';

interface IdempotentJobData {
  idempotencyKey: string;
  payload: Record<string, unknown>;
}

// 冪等性キーの生成
function generateIdempotencyKey(data: Record<string, unknown>): string {
  const hash = createHash('sha256');
  hash.update(JSON.stringify(data));
  return hash.digest('hex');
}

// 冪等なジョブ処理
const worker = new Worker<IdempotentJobData>(
  'idempotent-queue',
  async (job) => {
    const { idempotencyKey, payload } = job.data;

    // 既に処理済みかチェック
    const existing = await prisma.jobExecution.findUnique({
      where: { idempotencyKey },
    });

    if (existing) {
      if (existing.status === 'completed') {
        console.log(`Job already completed: ${idempotencyKey}`);
        return existing.result;
      }

      if (existing.status === 'processing') {
        // 別のワーカーが処理中の可能性
        throw new Error('Job is being processed by another worker');
      }
    }

    // 処理開始を記録（楽観的ロック）
    try {
      await prisma.jobExecution.upsert({
        where: { idempotencyKey },
        create: {
          idempotencyKey,
          jobId: job.id!,
          status: 'processing',
          startedAt: new Date(),
        },
        update: {
          jobId: job.id!,
          status: 'processing',
          startedAt: new Date(),
        },
      });
    } catch (error) {
      // 競合発生
      throw new Error('Concurrent execution detected');
    }

    try {
      // 実際の処理
      const result = await processPayload(payload);

      // 完了を記録
      await prisma.jobExecution.update({
        where: { idempotencyKey },
        data: {
          status: 'completed',
          result,
          completedAt: new Date(),
        },
      });

      return result;

    } catch (error) {
      // エラーを記録
      await prisma.jobExecution.update({
        where: { idempotencyKey },
        data: {
          status: 'failed',
          error: error.message,
          completedAt: new Date(),
        },
      });

      throw error;
    }
  }
);

// 冪等性を保証したジョブ追加
async function addIdempotentJob(
  queue: Queue,
  payload: Record<string, unknown>
): Promise<Job> {
  const idempotencyKey = generateIdempotencyKey(payload);

  // 同じキーのジョブが既にあるかチェック
  const existingJobs = await queue.getJobs(['waiting', 'active', 'delayed']);
  const duplicate = existingJobs.find(
    j => (j.data as IdempotentJobData).idempotencyKey === idempotencyKey
  );

  if (duplicate) {
    console.log(`Job already queued: ${idempotencyKey}`);
    return duplicate;
  }

  return queue.add('process', {
    idempotencyKey,
    payload,
  });
}
```

### ジョブのチェーンとフロー

```typescript
// flows/data-export-flow.ts
import { FlowProducer, Queue } from 'bullmq';

const flowProducer = new FlowProducer({ connection: redisConnection });

// フローを使ったジョブチェーン
async function createExportFlow(exportId: string): Promise<void> {
  await flowProducer.add({
    name: 'export-complete',
    queueName: 'exports',
    data: { exportId },
    children: [
      {
        name: 'generate-output',
        queueName: 'exports',
        data: { exportId },
        children: [
          {
            name: 'transform-data',
            queueName: 'exports',
            data: { exportId },
            children: [
              {
                name: 'collect-data',
                queueName: 'exports',
                data: { exportId },
              },
            ],
          },
        ],
      },
    ],
  });
}

// 各ステップのワーカー
const collectWorker = new Worker('exports', async (job) => {
  if (job.name !== 'collect-data') return;

  const { exportId } = job.data;
  const data = await collectDataFromSources(exportId);

  // 結果は子ジョブに自動的に渡される
  return { collectedData: data };
});

const transformWorker = new Worker('exports', async (job) => {
  if (job.name !== 'transform-data') return;

  const { exportId } = job.data;

  // 親ジョブの結果を取得
  const childrenValues = await job.getChildrenValues();
  const collectedData = childrenValues['collect-data']?.collectedData;

  const transformed = await transformData(collectedData);

  return { transformedData: transformed };
});

// シンプルなチェーン（フロー不使用）
async function processWithChain(taskId: string): Promise<void> {
  // フェーズ1
  await collectQueue.add('collect', { taskId });
}

// collectジョブ完了時に次のジョブを追加
collectQueue.on('completed', async (job) => {
  const { taskId } = job.data;
  await transformQueue.add('transform', { taskId });
});

transformQueue.on('completed', async (job) => {
  const { taskId } = job.data;
  await outputQueue.add('generate', { taskId });
});
```

### タイムアウト対策

```typescript
// workers/long-running-processor.ts
import { Worker, Job, DelayedError } from 'bullmq';

interface LongRunningJobData {
  taskId: string;
  lastProcessedId?: string;
  startTime?: string;
}

const PROCESSING_TIMEOUT_MS = 25 * 60 * 1000; // 25分
const BATCH_SIZE = 1000;

const worker = new Worker<LongRunningJobData>(
  'long-running',
  async (job) => {
    const { taskId, lastProcessedId, startTime } = job.data;
    const jobStartTime = startTime ? new Date(startTime) : new Date();

    const task = await prisma.asyncTask.findUnique({
      where: { id: taskId },
    });

    if (!task) {
      throw new UnrecoverableError(`Task ${taskId} not found`);
    }

    // 処理対象を取得
    const items = await getItemsToProcess(task.params, lastProcessedId, BATCH_SIZE);

    if (items.length === 0) {
      // すべて処理完了
      await taskService.markCompleted(taskId, { processed: task.progress });
      return { completed: true };
    }

    let processedInThisBatch = 0;
    let lastId = lastProcessedId;

    for (const item of items) {
      // タイムアウトチェック
      if (Date.now() - jobStartTime.getTime() > PROCESSING_TIMEOUT_MS) {
        // タイムアウト前に中断し、続きをスケジュール
        await job.queue.add('continue', {
          taskId,
          lastProcessedId: lastId,
          startTime: jobStartTime.toISOString(),
        }, {
          delay: 1000, // 1秒後に続行
        });

        return {
          paused: true,
          processedInThisBatch,
          willContinue: true,
        };
      }

      await processItem(item);
      processedInThisBatch++;
      lastId = item.id;

      // 進捗更新
      await taskService.updateProgress(taskId, task.progress + processedInThisBatch);
    }

    // バッチ完了、次のバッチをスケジュール
    if (items.length === BATCH_SIZE) {
      await job.queue.add('continue', {
        taskId,
        lastProcessedId: lastId,
        startTime: jobStartTime.toISOString(),
      });

      return {
        paused: true,
        processedInThisBatch,
        willContinue: true,
      };
    }

    // すべて完了
    await taskService.markCompleted(taskId, {
      processed: task.progress + processedInThisBatch,
    });

    return { completed: true };
  },
  {
    connection: redisConnection,
  }
);

async function getItemsToProcess(
  params: Record<string, unknown>,
  lastProcessedId: string | undefined,
  limit: number
): Promise<Array<{ id: string }>> {
  const where: any = { ...params };

  if (lastProcessedId) {
    where.id = { gt: lastProcessedId };
  }

  return prisma.item.findMany({
    where,
    orderBy: { id: 'asc' },
    take: limit,
  });
}
```

---

## 継続可能なジョブ（Graceful Shutdown & Checkpointing）

長時間実行されるジョブを途中で中断し、後から続きを再開できるようにするパターンを説明します。

### グレースフルシャットダウン

BullMQは、ワーカーのグレースフルシャットダウンをサポートしています。

```typescript
// workers/graceful-worker.ts
import { Worker, Job } from 'bullmq';

const worker = new Worker('my-queue', processor, {
  connection: redisConnection,
});

// SIGTERM/SIGINTシグナルのハンドリング
const gracefulShutdown = async (signal: string) => {
  console.log(`Received ${signal}, shutting down gracefully...`);

  // worker.close() は以下を行う:
  // 1. 新しいジョブの受け付けを停止
  // 2. 現在処理中のジョブが完了するまで待機
  await worker.close();

  // Redis接続を閉じる
  await redisConnection.quit();

  console.log('Worker shut down complete');
  process.exit(0);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));
```

### AbortSignalを使用したジョブキャンセル

BullMQは標準の`AbortController`/`AbortSignal` APIを使用してジョブのキャンセルをサポートしています。

```typescript
// workers/cancellable-worker.ts
import { Worker, Job } from 'bullmq';

const worker = new Worker<JobData, JobResult>(
  'my-queue',
  async (job: Job, token?: string) => {
    // jobにはabortSignalが含まれる（BullMQ 4.0+）
    const abortSignal = job.abortSignal;

    for (let i = 0; i < 1000; i++) {
      // 定期的にキャンセルをチェック
      if (abortSignal?.aborted) {
        console.log(`Job ${job.id} was cancelled`);
        throw new Error('Job cancelled');
      }

      await processItem(i);
      await job.updateProgress(i + 1);
    }

    return { processed: 1000 };
  },
  {
    connection: redisConnection,
  }
);

// 外部からジョブをキャンセル
async function cancelJob(jobId: string): Promise<void> {
  const job = await queue.getJob(jobId);
  if (job) {
    await job.moveToFailed(new Error('Cancelled by user'), 'cancelled');
  }
}
```

### チェックポイントパターン

BullMQにはRailsの`job-iteration`のような組み込みのチェックポイント機能はありませんが、`job.updateProgress()`と`job.updateData()`を使用して同様のパターンを実装できます。

```typescript
// types/checkpoint.ts
interface CheckpointData {
  lastProcessedId: string | null;
  processedCount: number;
  totalCount: number;
  phase: string;
}

interface CheckpointableJobData {
  taskId: string;
  checkpoint?: CheckpointData;
}
```

```typescript
// workers/checkpointable-worker.ts
import { Worker, Job, UnrecoverableError } from 'bullmq';

const CHECKPOINT_INTERVAL = 100; // 100件ごとにチェックポイント
const MAX_RUNTIME_MS = 4 * 60 * 1000; // 4分（5分タイムアウトの余裕）

const worker = new Worker<CheckpointableJobData>(
  'bulk-processing',
  async (job) => {
    const startTime = Date.now();
    const { taskId, checkpoint } = job.data;

    // 前回のチェックポイントから再開
    let lastProcessedId = checkpoint?.lastProcessedId || null;
    let processedCount = checkpoint?.processedCount || 0;

    // 処理対象を取得
    const items = await getItemsToProcess(taskId, lastProcessedId);
    const totalCount = checkpoint?.totalCount || items.length + processedCount;

    for (const item of items) {
      // タイムアウトチェック
      if (Date.now() - startTime > MAX_RUNTIME_MS) {
        // チェックポイントを保存して再エンキュー
        const newCheckpoint: CheckpointData = {
          lastProcessedId,
          processedCount,
          totalCount,
          phase: 'processing',
        };

        // ジョブデータを更新（次回実行時に使用）
        await job.updateData({
          ...job.data,
          checkpoint: newCheckpoint,
        });

        // 自己リエンキュー
        await job.queue.add(job.name, {
          taskId,
          checkpoint: newCheckpoint,
        }, {
          delay: 1000, // 1秒後に再開
        });

        console.log(`Job ${job.id} paused at item ${lastProcessedId}, will resume`);
        return { paused: true, processedCount };
      }

      // アイテム処理
      await processItem(item);
      lastProcessedId = item.id;
      processedCount++;

      // 定期的にチェックポイントを保存
      if (processedCount % CHECKPOINT_INTERVAL === 0) {
        await job.updateProgress({
          processedCount,
          totalCount,
          percentage: Math.round((processedCount / totalCount) * 100),
        });

        // チェックポイントデータを更新
        await job.updateData({
          ...job.data,
          checkpoint: {
            lastProcessedId,
            processedCount,
            totalCount,
            phase: 'processing',
          },
        });
      }
    }

    // 完了
    return {
      completed: true,
      processedCount,
      totalCount,
    };
  },
  {
    connection: redisConnection,
  }
);

async function getItemsToProcess(
  taskId: string,
  afterId: string | null
): Promise<Array<{ id: string }>> {
  const query: any = { taskId };

  if (afterId) {
    query.id = { $gt: afterId };
  }

  return db.items.find(query).sort({ id: 1 }).limit(1000).toArray();
}
```

### イテレーションベースのパターン

Railsの`job-iteration`に近いパターンをTypeScriptで実装する例です。

```typescript
// lib/iterable-job.ts
import { Worker, Job, Queue } from 'bullmq';

interface IterableJobOptions {
  batchSize: number;
  maxRuntime: number;
  checkpointInterval: number;
}

interface IterationState<TCursor> {
  cursor: TCursor | null;
  processedCount: number;
  iterationCount: number;
}

type BuildIterator<TData, TCursor, TItem> = (
  data: TData,
  cursor: TCursor | null
) => AsyncGenerator<{ item: TItem; nextCursor: TCursor }>;

type ProcessItem<TItem> = (item: TItem) => Promise<void>;

export function createIterableWorker<TData, TCursor, TItem>(
  queueName: string,
  options: IterableJobOptions,
  buildIterator: BuildIterator<TData, TCursor, TItem>,
  processItem: ProcessItem<TItem>
): Worker {
  return new Worker<TData & { _iterationState?: IterationState<TCursor> }>(
    queueName,
    async (job) => {
      const startTime = Date.now();
      const state: IterationState<TCursor> = job.data._iterationState || {
        cursor: null,
        processedCount: 0,
        iterationCount: 0,
      };

      const iterator = buildIterator(job.data, state.cursor);

      for await (const { item, nextCursor } of iterator) {
        // タイムアウトチェック
        if (Date.now() - startTime > options.maxRuntime) {
          // 状態を保存して再エンキュー
          const newState: IterationState<TCursor> = {
            cursor: state.cursor,
            processedCount: state.processedCount,
            iterationCount: state.iterationCount + 1,
          };

          await job.queue.add(job.name, {
            ...job.data,
            _iterationState: newState,
          }, {
            delay: 100,
          });

          return {
            interrupted: true,
            iteration: newState.iterationCount,
            processedCount: state.processedCount,
          };
        }

        // アイテム処理
        await processItem(item);
        state.cursor = nextCursor;
        state.processedCount++;

        // 進捗更新
        if (state.processedCount % options.checkpointInterval === 0) {
          await job.updateProgress({
            processedCount: state.processedCount,
            cursor: state.cursor,
          });
        }
      }

      return {
        completed: true,
        processedCount: state.processedCount,
        iterations: state.iterationCount + 1,
      };
    },
    {
      connection: redisConnection,
    }
  );
}

// 使用例
const worker = createIterableWorker<
  { userId: string },
  string,
  { id: string; email: string }
>(
  'send-notifications',
  {
    batchSize: 100,
    maxRuntime: 4 * 60 * 1000,
    checkpointInterval: 10,
  },
  async function* (data, cursor) {
    const users = await db.users
      .find({ subscribedTo: data.userId, id: { $gt: cursor || '' } })
      .sort({ id: 1 })
      .limit(1000)
      .toArray();

    for (const user of users) {
      yield { item: user, nextCursor: user.id };
    }
  },
  async (user) => {
    await sendNotification(user.email);
  }
);
```

### Stalled Jobs（停滞ジョブ）の処理

グレースフルでないシャットダウンが発生した場合、ジョブは「stalled」状態になる可能性があります。BullMQ 2.0以降では自動的に検出・回復されます。

```typescript
// config/worker-with-stall-detection.ts
const worker = new Worker('my-queue', processor, {
  connection: redisConnection,
  // Stalled job の検出設定
  stalledInterval: 30000, // 30秒ごとにチェック
  maxStalledCount: 3, // 3回stalledになったら失敗として処理
});

// Stalledイベントのリスニング
worker.on('stalled', (jobId: string) => {
  console.warn(`Job ${jobId} has stalled and will be reprocessed`);
});

// QueueEventsでもリスニング可能
const queueEvents = new QueueEvents('my-queue', { connection: redisConnection });

queueEvents.on('stalled', async ({ jobId }) => {
  console.warn(`Job ${jobId} stalled, sending alert...`);
  await sendAlert(`Job ${jobId} has stalled`);
});
```

### Kubernetes/Docker環境でのグレースフルシャットダウン

```typescript
// workers/k8s-worker.ts
import { Worker } from 'bullmq';

let isShuttingDown = false;

const worker = new Worker('my-queue', async (job) => {
  // シャットダウン中は早期リターン
  if (isShuttingDown) {
    throw new Error('Worker is shutting down');
  }

  // 長時間処理中も定期的にチェック
  for (const item of items) {
    if (isShuttingDown) {
      // チェックポイントを保存
      await saveCheckpoint(job);
      throw new Error('Worker shutdown requested');
    }

    await processItem(item);
  }
}, {
  connection: redisConnection,
});

// Kubernetesのpreストップフック用
const gracefulShutdown = async () => {
  isShuttingDown = true;
  console.log('Graceful shutdown initiated');

  // Kubernetesのterminationグレースピリオド内で完了させる
  const shutdownTimeout = setTimeout(() => {
    console.error('Shutdown timeout, forcing exit');
    process.exit(1);
  }, 25000); // 25秒（Kubernetesデフォルト30秒の余裕）

  try {
    await worker.close();
    clearTimeout(shutdownTimeout);
    console.log('Worker closed successfully');
    process.exit(0);
  } catch (error) {
    console.error('Error during shutdown:', error);
    process.exit(1);
  }
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);
```

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: worker
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]
```

---

## テスト戦略

### ジョブのユニットテスト

```typescript
// __tests__/workers/data-processor.test.ts
import { Job } from 'bullmq';
import { processDataJob } from '../../workers/data-processor';

// BullMQ Jobのモック
function createMockJob<T>(data: T, options: Partial<Job> = {}): Job<T> {
  return {
    id: 'test-job-id',
    data,
    name: 'test',
    attemptsMade: 0,
    opts: {},
    updateProgress: jest.fn(),
    log: jest.fn(),
    ...options,
  } as unknown as Job<T>;
}

describe('DataProcessor', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('processDataJob', () => {
    it('should process data successfully', async () => {
      const task = await createTestTask({
        status: 'pending',
        params: { type: 'export' },
      });

      const job = createMockJob({ taskId: task.id });

      const result = await processDataJob(job);

      expect(result.success).toBe(true);

      const updatedTask = await prisma.asyncTask.findUnique({
        where: { id: task.id },
      });
      expect(updatedTask?.status).toBe('completed');
    });

    it('should update progress during processing', async () => {
      const items = await createTestItems(25);
      const task = await createTestTask({
        params: { itemIds: items.map(i => i.id) },
      });

      const job = createMockJob({ taskId: task.id });

      await processDataJob(job);

      // 進捗更新が呼ばれたことを確認
      expect(job.updateProgress).toHaveBeenCalled();
    });

    it('should handle cancellation', async () => {
      const task = await createTestTask({ status: 'cancelled' });

      const job = createMockJob({ taskId: task.id });

      const result = await processDataJob(job);

      expect(result.cancelled).toBe(true);
    });

    it('should throw UnrecoverableError for missing task', async () => {
      const job = createMockJob({ taskId: 'non-existent-id' });

      await expect(processDataJob(job)).rejects.toThrow(UnrecoverableError);
    });

    it('should retry on transient errors', async () => {
      const task = await createTestTask();
      const job = createMockJob({ taskId: task.id }, { attemptsMade: 1 });

      // 一時的なエラーをシミュレート
      jest.spyOn(externalService, 'call').mockRejectedValueOnce(
        new Error('Connection timeout')
      );

      await expect(processDataJob(job)).rejects.toThrow('Connection timeout');

      // リトライ設定を確認
      const updatedTask = await prisma.asyncTask.findUnique({
        where: { id: task.id },
      });
      expect(updatedTask?.status).toBe('retrying');
    });
  });
});
```

### キューの統合テスト

```typescript
// __tests__/integration/queue.test.ts
import { Queue, Worker, Job } from 'bullmq';
import IORedis from 'ioredis';

describe('Queue Integration', () => {
  let queue: Queue;
  let worker: Worker;
  let connection: IORedis;

  beforeAll(async () => {
    connection = new IORedis(process.env.REDIS_TEST_URL);

    queue = new Queue('test-queue', { connection });
  });

  afterAll(async () => {
    await queue.close();
    await connection.quit();
  });

  beforeEach(async () => {
    // キューをクリア
    await queue.drain();
  });

  afterEach(async () => {
    if (worker) {
      await worker.close();
    }
  });

  it('should process job successfully', async () => {
    const processedJobs: Job[] = [];

    worker = new Worker(
      'test-queue',
      async (job) => {
        processedJobs.push(job);
        return { processed: true };
      },
      { connection }
    );

    const job = await queue.add('test', { value: 123 });

    // ジョブ完了を待つ
    await job.waitUntilFinished(queue.events);

    expect(processedJobs).toHaveLength(1);
    expect(processedJobs[0].data).toEqual({ value: 123 });
  });

  it('should retry failed jobs', async () => {
    let attempts = 0;

    worker = new Worker(
      'test-queue',
      async () => {
        attempts++;
        if (attempts < 3) {
          throw new Error('Simulated failure');
        }
        return { success: true };
      },
      { connection }
    );

    const job = await queue.add('test', {}, {
      attempts: 3,
      backoff: { type: 'fixed', delay: 100 },
    });

    await job.waitUntilFinished(queue.events);

    expect(attempts).toBe(3);
  });

  it('should respect job priority', async () => {
    const processOrder: number[] = [];

    // 処理を遅延させるため、ワーカーを後で起動
    await queue.add('low', { priority: 3 }, { priority: 3 });
    await queue.add('high', { priority: 1 }, { priority: 1 });
    await queue.add('medium', { priority: 2 }, { priority: 2 });

    worker = new Worker(
      'test-queue',
      async (job) => {
        processOrder.push(job.data.priority);
      },
      { connection }
    );

    // すべてのジョブが処理されるまで待つ
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 優先度順（1が最高）で処理される
    expect(processOrder).toEqual([1, 2, 3]);
  });
});
```

### E2Eテスト

```typescript
// __tests__/e2e/async-task.test.ts
import request from 'supertest';
import { app } from '../../app';

describe('Async Task E2E', () => {
  let authToken: string;
  let userId: string;

  beforeAll(async () => {
    const user = await createTestUser();
    userId = user.id;
    authToken = generateToken(user);
  });

  describe('POST /api/tasks', () => {
    it('should create a task and process it', async () => {
      // タスク作成
      const createResponse = await request(app)
        .post('/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          type: 'data-export',
          params: { format: 'csv' },
        });

      expect(createResponse.status).toBe(201);
      const taskId = createResponse.body.id;

      // ジョブが処理されるまで待つ
      await waitForTaskCompletion(taskId, 30000);

      // 結果を確認
      const statusResponse = await request(app)
        .get(`/api/tasks/${taskId}/status`)
        .set('Authorization', `Bearer ${authToken}`);

      expect(statusResponse.status).toBe(200);
      expect(statusResponse.body.status).toBe('completed');
      expect(statusResponse.body.result).toBeDefined();
    });
  });

  describe('DELETE /api/tasks/:id/cancel', () => {
    it('should cancel a pending task', async () => {
      // 長時間かかるタスクを作成
      const createResponse = await request(app)
        .post('/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          type: 'long-running',
          params: { items: 10000 },
        });

      const taskId = createResponse.body.id;

      // 少し待ってからキャンセル
      await new Promise(resolve => setTimeout(resolve, 100));

      const cancelResponse = await request(app)
        .delete(`/api/tasks/${taskId}/cancel`)
        .set('Authorization', `Bearer ${authToken}`);

      expect(cancelResponse.status).toBe(200);

      // キャンセルされたことを確認
      const statusResponse = await request(app)
        .get(`/api/tasks/${taskId}/status`)
        .set('Authorization', `Bearer ${authToken}`);

      expect(statusResponse.body.status).toBe('cancelled');
    });
  });
});

async function waitForTaskCompletion(
  taskId: string,
  timeout: number
): Promise<void> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const task = await prisma.asyncTask.findUnique({
      where: { id: taskId },
    });

    if (task?.status === 'completed' || task?.status === 'failed') {
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 500));
  }

  throw new Error(`Task ${taskId} did not complete within ${timeout}ms`);
}
```

---

## その他のベストプラクティス

### ログ出力

```typescript
// utils/job-logger.ts
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
});

export function createJobLogger(job: Job) {
  return logger.child({
    jobId: job.id,
    jobName: job.name,
    queueName: job.queueName,
    attemptsMade: job.attemptsMade,
  });
}

// ワーカーでの使用
const worker = new Worker('queue', async (job) => {
  const log = createJobLogger(job);

  log.info({ data: sanitize(job.data) }, 'Job started');

  try {
    const result = await process(job);
    log.info({ result }, 'Job completed');
    return result;
  } catch (error) {
    log.error({ error }, 'Job failed');
    throw error;
  }
});
```

### メトリクス収集

```typescript
// services/metrics.ts
import { Counter, Histogram, Gauge } from 'prom-client';

export const jobsProcessed = new Counter({
  name: 'bullmq_jobs_processed_total',
  help: 'Total number of jobs processed',
  labelNames: ['queue', 'status'],
});

export const jobDuration = new Histogram({
  name: 'bullmq_job_duration_seconds',
  help: 'Job processing duration in seconds',
  labelNames: ['queue', 'name'],
  buckets: [0.1, 0.5, 1, 5, 10, 30, 60, 300],
});

export const activeJobs = new Gauge({
  name: 'bullmq_active_jobs',
  help: 'Number of currently active jobs',
  labelNames: ['queue'],
});

// ワーカーでメトリクス収集
worker.on('active', () => {
  activeJobs.inc({ queue: 'my-queue' });
});

worker.on('completed', (job) => {
  activeJobs.dec({ queue: 'my-queue' });
  jobsProcessed.inc({ queue: 'my-queue', status: 'completed' });

  const duration = (Date.now() - job.processedOn!) / 1000;
  jobDuration.observe({ queue: 'my-queue', name: job.name }, duration);
});

worker.on('failed', () => {
  activeJobs.dec({ queue: 'my-queue' });
  jobsProcessed.inc({ queue: 'my-queue', status: 'failed' });
});
```

### レート制限

```typescript
// queues/rate-limited-queue.ts
import { Queue, Worker } from 'bullmq';

const queue = new Queue('api-calls', {
  connection: redisConnection,
});

// BullMQのレート制限はWorker側で設定する
const worker = new Worker(
  'api-calls',
  processor,
  {
    connection: redisConnection,
    limiter: {
      max: 100,     // 最大100ジョブ
      duration: 60000, // 1分間あたり
    },
  }
);

// グループ別のレート制限が必要な場合は、FlowProducerを使用するか
// ジョブデータに基づいてプロセッサ内で制御する
```

---

## 参照

- [BullMQ Documentation](https://docs.bullmq.io/)
- [BullMQ Best Practices](https://docs.bullmq.io/guide/best-practices)
- [Redis Best Practices](https://redis.io/docs/management/optimization/)
