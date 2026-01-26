# AWS Serverless バックエンド実装ベストプラクティス

AWS Lambda + SQS + DynamoDB + AppSync Eventsを使用した非同期処理のバックエンド実装におけるベストプラクティスをまとめます。

## 目次

1. [パラメータの受け取り方](#パラメータの受け取り方)
2. [エラー発生時の処理と通知](#エラー発生時の処理と通知)
3. [進捗の状態管理](#進捗の状態管理)
4. [Lambda関数の設計パターン](#lambda関数の設計パターン)
5. [継続可能な処理（Continuable Processing）](#継続可能な処理continuable-processing)
6. [テスト戦略](#テスト戦略)

---

## パラメータの受け取り方

### 基本原則

AWSサービスにはそれぞれペイロードサイズの制限があります。

| サービス | 最大サイズ | 備考 |
|---------|-----------|------|
| SQS | 1MB (2025年8月以降) | 以前は256KB |
| Lambda同期呼び出し | 6MB | リクエスト/レスポンス |
| Lambda非同期呼び出し | 256KB | イベントペイロード |
| DynamoDB | 400KB | アイテムサイズ |
| Step Functions | 256KB | 入力/出力 |

### SQSメッセージの設計

```typescript
// types/sqs-message.ts
interface TaskMessage {
  taskId: string;
  taskType: string;
  userId: string;
  // 軽量なパラメータのみ
  params: {
    operation: string;
    options: Record<string, string | number | boolean>;
  };
  // 大きなデータはS3への参照
  dataRef?: {
    bucket: string;
    key: string;
  };
  metadata: {
    requestedAt: string;
    requestId: string;
    traceId: string;
  };
}

// ❌ 悪い例: 大きなデータを直接メッセージに含める
interface BadMessage {
  taskId: string;
  csvContent: string; // 数MBのCSVデータ
  userList: User[];   // 大量のユーザーオブジェクト
}

// ✅ 良い例: 参照のみを含める
interface GoodMessage {
  taskId: string;
  inputFileRef: {
    bucket: string;
    key: string;
  };
  queryConditions: {
    status: string[];
    createdAfter: string;
  };
}
```

### 大きなペイロードの処理（Extended Client Pattern）

```typescript
// services/sqs-extended-client.ts
import {
  SQSClient,
  SendMessageCommand,
  ReceiveMessageCommand,
} from '@aws-sdk/client-sqs';
import {
  S3Client,
  PutObjectCommand,
  GetObjectCommand,
} from '@aws-sdk/client-s3';

const PAYLOAD_SIZE_THRESHOLD = 256 * 1024; // 256KB

interface ExtendedMessage<T> {
  isExtended: boolean;
  s3Ref?: {
    bucket: string;
    key: string;
  };
  body?: T;
}

export class SQSExtendedClient {
  constructor(
    private sqs: SQSClient,
    private s3: S3Client,
    private bucket: string
  ) {}

  async sendMessage<T>(
    queueUrl: string,
    message: T,
    messageGroupId?: string
  ): Promise<void> {
    const serialized = JSON.stringify(message);

    if (serialized.length > PAYLOAD_SIZE_THRESHOLD) {
      // S3に保存して参照を送信
      const key = `sqs-payloads/${Date.now()}-${Math.random().toString(36)}`;

      await this.s3.send(new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: serialized,
        ContentType: 'application/json',
      }));

      const extendedMessage: ExtendedMessage<T> = {
        isExtended: true,
        s3Ref: { bucket: this.bucket, key },
      };

      await this.sqs.send(new SendMessageCommand({
        QueueUrl: queueUrl,
        MessageBody: JSON.stringify(extendedMessage),
        MessageGroupId: messageGroupId,
      }));
    } else {
      // 直接送信
      const extendedMessage: ExtendedMessage<T> = {
        isExtended: false,
        body: message,
      };

      await this.sqs.send(new SendMessageCommand({
        QueueUrl: queueUrl,
        MessageBody: JSON.stringify(extendedMessage),
        MessageGroupId: messageGroupId,
      }));
    }
  }

  async receiveMessage<T>(
    queueUrl: string
  ): Promise<{ message: T; receiptHandle: string } | null> {
    const response = await this.sqs.send(new ReceiveMessageCommand({
      QueueUrl: queueUrl,
      MaxNumberOfMessages: 1,
      WaitTimeSeconds: 20,
    }));

    if (!response.Messages || response.Messages.length === 0) {
      return null;
    }

    const sqsMessage = response.Messages[0];
    const extendedMessage: ExtendedMessage<T> = JSON.parse(sqsMessage.Body!);

    let message: T;

    if (extendedMessage.isExtended && extendedMessage.s3Ref) {
      // S3から取得
      const s3Response = await this.s3.send(new GetObjectCommand({
        Bucket: extendedMessage.s3Ref.bucket,
        Key: extendedMessage.s3Ref.key,
      }));

      const body = await s3Response.Body!.transformToString();
      message = JSON.parse(body);
    } else {
      message = extendedMessage.body!;
    }

    return {
      message,
      receiptHandle: sqsMessage.ReceiptHandle!,
    };
  }
}
```

### Lambda関数でのパラメータバリデーション

```typescript
// handlers/process-task.ts
import { SQSEvent, SQSRecord, Context } from 'aws-lambda';
import { z } from 'zod';

// バリデーションスキーマ
const TaskMessageSchema = z.object({
  taskId: z.string().uuid(),
  taskType: z.enum(['export', 'import', 'analyze']),
  userId: z.string(),
  params: z.object({
    operation: z.string(),
    options: z.record(z.union([z.string(), z.number(), z.boolean()])),
  }),
  dataRef: z.object({
    bucket: z.string(),
    key: z.string(),
  }).optional(),
  metadata: z.object({
    requestedAt: z.string().datetime(),
    requestId: z.string(),
    traceId: z.string(),
  }),
});

type TaskMessage = z.infer<typeof TaskMessageSchema>;

export async function handler(
  event: SQSEvent,
  context: Context
): Promise<void> {
  for (const record of event.Records) {
    await processRecord(record, context);
  }
}

async function processRecord(
  record: SQSRecord,
  context: Context
): Promise<void> {
  const logger = createLogger(context);

  try {
    // JSON解析
    const rawMessage = JSON.parse(record.body);

    // バリデーション
    const validationResult = TaskMessageSchema.safeParse(rawMessage);

    if (!validationResult.success) {
      logger.error('Invalid message format', {
        errors: validationResult.error.errors,
        messageId: record.messageId,
      });

      // バリデーションエラーはリトライしても意味がないのでDLQへ
      throw new ValidationError(
        `Invalid message: ${validationResult.error.message}`
      );
    }

    const message = validationResult.data;

    logger.info('Processing message', {
      taskId: message.taskId,
      taskType: message.taskType,
    });

    await processTask(message);

  } catch (error) {
    logger.error('Failed to process message', { error });
    throw error; // SQSがリトライを処理
  }
}
```

### DynamoDBアイテムサイズの管理

```typescript
// services/task-repository.ts
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import {
  DynamoDBDocumentClient,
  PutCommand,
  GetCommand,
} from '@aws-sdk/lib-dynamodb';
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';

const DYNAMODB_ITEM_SIZE_LIMIT = 400 * 1024; // 400KB
const LARGE_ATTRIBUTE_THRESHOLD = 100 * 1024; // 100KB

interface TaskRecord {
  pk: string;
  sk: string;
  taskId: string;
  status: string;
  result?: Record<string, unknown>;
  resultRef?: {
    bucket: string;
    key: string;
  };
  // その他の属性
}

export class TaskRepository {
  constructor(
    private ddb: DynamoDBDocumentClient,
    private s3: S3Client,
    private tableName: string,
    private bucket: string
  ) {}

  async saveTask(task: TaskRecord): Promise<void> {
    // 結果が大きい場合はS3に保存
    if (task.result) {
      const resultSize = JSON.stringify(task.result).length;

      if (resultSize > LARGE_ATTRIBUTE_THRESHOLD) {
        const key = `task-results/${task.taskId}/result.json`;

        await this.s3.send(new PutObjectCommand({
          Bucket: this.bucket,
          Key: key,
          Body: JSON.stringify(task.result),
          ContentType: 'application/json',
        }));

        // DynamoDBには参照のみ保存
        const taskToSave = {
          ...task,
          result: undefined,
          resultRef: { bucket: this.bucket, key },
        };

        await this.ddb.send(new PutCommand({
          TableName: this.tableName,
          Item: taskToSave,
        }));

        return;
      }
    }

    // 通常の保存
    await this.ddb.send(new PutCommand({
      TableName: this.tableName,
      Item: task,
    }));
  }

  async getTask(taskId: string): Promise<TaskRecord | null> {
    const response = await this.ddb.send(new GetCommand({
      TableName: this.tableName,
      Key: {
        pk: `TASK#${taskId}`,
        sk: `TASK#${taskId}`,
      },
    }));

    if (!response.Item) {
      return null;
    }

    const task = response.Item as TaskRecord;

    // S3から結果を取得
    if (task.resultRef) {
      const s3Response = await this.s3.send(new GetObjectCommand({
        Bucket: task.resultRef.bucket,
        Key: task.resultRef.key,
      }));

      const body = await s3Response.Body!.transformToString();
      task.result = JSON.parse(body);
    }

    return task;
  }
}
```

---

## エラー発生時の処理と通知

### SQSとLambdaのエラーハンドリング

```typescript
// handlers/process-task.ts
import { SQSEvent, SQSBatchResponse, SQSBatchItemFailure } from 'aws-lambda';

// 部分的バッチ失敗レポート（推奨）
export async function handler(
  event: SQSEvent
): Promise<SQSBatchResponse> {
  const batchItemFailures: SQSBatchItemFailure[] = [];

  for (const record of event.Records) {
    try {
      await processRecord(record);
    } catch (error) {
      console.error('Failed to process record', {
        messageId: record.messageId,
        error,
      });

      // 失敗したメッセージのみを報告
      batchItemFailures.push({
        itemIdentifier: record.messageId,
      });
    }
  }

  return { batchItemFailures };
}

// カスタムエラークラス
class RetryableError extends Error {
  constructor(message: string) {
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

async function processRecord(record: SQSRecord): Promise<void> {
  const message = JSON.parse(record.body);
  const task = await getTask(message.taskId);

  try {
    await updateTaskStatus(task.id, 'processing');
    await executeTask(task);
    await updateTaskStatus(task.id, 'completed');

  } catch (error) {
    if (error instanceof NonRetryableError) {
      // リトライ不要なエラー：タスクを失敗としてマークし、例外を投げない
      await updateTaskStatus(task.id, 'failed', error.message);
      await sendErrorNotification(task, error);
      // 正常終了として扱い、メッセージを削除
      return;
    }

    if (error instanceof RetryableError) {
      // リトライ可能なエラー：タスクをリトライ中としてマーク
      await updateTaskStatus(task.id, 'retrying', error.message);
      // 例外を投げてSQSにリトライさせる
      throw error;
    }

    // その他のエラー：デフォルトでリトライ
    await updateTaskStatus(task.id, 'retrying', `${error.name}: ${error.message}`);
    throw error;
  }
}
```

### Dead Letter Queue（DLQ）の処理

```typescript
// handlers/dlq-processor.ts
import { SQSEvent, SQSRecord } from 'aws-lambda';
import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';

const sns = new SNSClient({});

export async function handler(event: SQSEvent): Promise<void> {
  for (const record of event.Records) {
    await processDLQRecord(record);
  }
}

async function processDLQRecord(record: SQSRecord): Promise<void> {
  const attributes = record.attributes;
  const messageAttributes = record.messageAttributes;

  // 元のメッセージ情報を取得
  const originalMessage = JSON.parse(record.body);
  const approximateReceiveCount = parseInt(
    attributes.ApproximateReceiveCount || '0'
  );

  console.error('Message in DLQ', {
    messageId: record.messageId,
    receiveCount: approximateReceiveCount,
    firstReceiveTimestamp: attributes.ApproximateFirstReceiveTimestamp,
    taskId: originalMessage.taskId,
  });

  // タスクを最終失敗としてマーク
  await updateTaskStatus(
    originalMessage.taskId,
    'failed',
    `Max retries exceeded after ${approximateReceiveCount} attempts`
  );

  // DynamoDBに詳細を記録
  await recordDeadLetter({
    messageId: record.messageId,
    taskId: originalMessage.taskId,
    originalMessage,
    receiveCount: approximateReceiveCount,
    failedAt: new Date().toISOString(),
  });

  // SNSで通知
  await sns.send(new PublishCommand({
    TopicArn: process.env.ALERT_TOPIC_ARN,
    Subject: `[ALERT] Task Failed: ${originalMessage.taskType}`,
    Message: JSON.stringify({
      taskId: originalMessage.taskId,
      taskType: originalMessage.taskType,
      userId: originalMessage.userId,
      receiveCount: approximateReceiveCount,
      timestamp: new Date().toISOString(),
    }, null, 2),
  }));
}
```

### CloudWatch Alarmの設定

```typescript
// infrastructure/alarms.ts (CDK)
import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatch_actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as sns from 'aws-cdk-lib/aws-sns';

export function createAlarms(
  scope: cdk.Stack,
  lambdaFunction: cdk.aws_lambda.Function,
  dlqQueue: cdk.aws_sqs.Queue,
  alertTopic: sns.Topic
): void {
  // Lambda エラー率アラーム
  const errorRateAlarm = new cloudwatch.Alarm(scope, 'LambdaErrorRateAlarm', {
    metric: lambdaFunction.metricErrors({
      statistic: 'Sum',
      period: cdk.Duration.minutes(5),
    }),
    threshold: 10,
    evaluationPeriods: 2,
    comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    alarmDescription: 'Lambda function error rate is high',
  });

  errorRateAlarm.addAlarmAction(
    new cloudwatch_actions.SnsAction(alertTopic)
  );

  // DLQ メッセージ数アラーム
  const dlqAlarm = new cloudwatch.Alarm(scope, 'DLQMessagesAlarm', {
    metric: dlqQueue.metricApproximateNumberOfMessagesVisible({
      statistic: 'Sum',
      period: cdk.Duration.minutes(5),
    }),
    threshold: 1,
    evaluationPeriods: 1,
    comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    alarmDescription: 'Messages in DLQ detected',
  });

  dlqAlarm.addAlarmAction(
    new cloudwatch_actions.SnsAction(alertTopic)
  );

  // Lambda Duration アラーム（タイムアウト近い）
  const durationAlarm = new cloudwatch.Alarm(scope, 'LambdaDurationAlarm', {
    metric: lambdaFunction.metricDuration({
      statistic: 'p99',
      period: cdk.Duration.minutes(5),
    }),
    threshold: 14 * 60 * 1000, // 14分（15分タイムアウトの93%）
    evaluationPeriods: 2,
    comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    alarmDescription: 'Lambda function duration approaching timeout',
  });

  durationAlarm.addAlarmAction(
    new cloudwatch_actions.SnsAction(alertTopic)
  );
}
```

### 構造化ログとX-Ray トレーシング

```typescript
// utils/logger.ts
import { Context } from 'aws-lambda';

interface LogContext {
  requestId: string;
  functionName: string;
  traceId?: string;
}

export function createLogger(context: Context) {
  const logContext: LogContext = {
    requestId: context.awsRequestId,
    functionName: context.functionName,
    traceId: process.env._X_AMZN_TRACE_ID,
  };

  return {
    info: (message: string, data?: Record<string, unknown>) => {
      console.log(JSON.stringify({
        level: 'INFO',
        message,
        ...logContext,
        ...data,
        timestamp: new Date().toISOString(),
      }));
    },

    error: (message: string, data?: Record<string, unknown>) => {
      console.error(JSON.stringify({
        level: 'ERROR',
        message,
        ...logContext,
        ...data,
        timestamp: new Date().toISOString(),
      }));
    },

    warn: (message: string, data?: Record<string, unknown>) => {
      console.warn(JSON.stringify({
        level: 'WARN',
        message,
        ...logContext,
        ...data,
        timestamp: new Date().toISOString(),
      }));
    },
  };
}

// X-Ray セグメント追加
import AWSXRay from 'aws-xray-sdk';

export function addXRayAnnotation(
  key: string,
  value: string | number | boolean
): void {
  const segment = AWSXRay.getSegment();
  if (segment) {
    segment.addAnnotation(key, value);
  }
}

export function addXRayMetadata(
  key: string,
  value: Record<string, unknown>
): void {
  const segment = AWSXRay.getSegment();
  if (segment) {
    segment.addMetadata(key, value);
  }
}
```

---

## 進捗の状態管理

### DynamoDBによる状態管理

```typescript
// services/task-state-manager.ts
import {
  DynamoDBDocumentClient,
  UpdateCommand,
  GetCommand,
  QueryCommand,
} from '@aws-sdk/lib-dynamodb';

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
  status: TaskStatus;
  progress: number;
  totalItems: number | null;
  currentPhase: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
  startedAt: string | null;
  completedAt: string | null;
  updatedAt: string;
  ttl: number;
}

export class TaskStateManager {
  constructor(
    private ddb: DynamoDBDocumentClient,
    private tableName: string
  ) {}

  async initializeTask(
    taskId: string,
    userId: string,
    totalItems?: number
  ): Promise<void> {
    const now = new Date().toISOString();
    const ttl = Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60; // 30日

    await this.ddb.send(new UpdateCommand({
      TableName: this.tableName,
      Key: {
        pk: `TASK#${taskId}`,
        sk: `TASK#${taskId}`,
      },
      UpdateExpression: `
        SET #status = :status,
            #userId = :userId,
            #progress = :progress,
            #totalItems = :totalItems,
            #startedAt = :startedAt,
            #updatedAt = :updatedAt,
            #ttl = :ttl,
            #gsi1pk = :gsi1pk,
            #gsi1sk = :gsi1sk
      `,
      ExpressionAttributeNames: {
        '#status': 'status',
        '#userId': 'userId',
        '#progress': 'progress',
        '#totalItems': 'totalItems',
        '#startedAt': 'startedAt',
        '#updatedAt': 'updatedAt',
        '#ttl': 'ttl',
        '#gsi1pk': 'gsi1pk',
        '#gsi1sk': 'gsi1sk',
      },
      ExpressionAttributeValues: {
        ':status': TaskStatus.PROCESSING,
        ':userId': userId,
        ':progress': 0,
        ':totalItems': totalItems ?? null,
        ':startedAt': now,
        ':updatedAt': now,
        ':ttl': ttl,
        ':gsi1pk': `USER#${userId}`,
        ':gsi1sk': `TASK#${now}#${taskId}`,
      },
    }));
  }

  async updateProgress(
    taskId: string,
    progress: number,
    currentPhase?: string
  ): Promise<void> {
    const updateExpression = currentPhase
      ? 'SET #progress = :progress, #currentPhase = :currentPhase, #updatedAt = :updatedAt'
      : 'SET #progress = :progress, #updatedAt = :updatedAt';

    const expressionAttributeNames: Record<string, string> = {
      '#progress': 'progress',
      '#updatedAt': 'updatedAt',
    };

    const expressionAttributeValues: Record<string, unknown> = {
      ':progress': progress,
      ':updatedAt': new Date().toISOString(),
    };

    if (currentPhase) {
      expressionAttributeNames['#currentPhase'] = 'currentPhase';
      expressionAttributeValues[':currentPhase'] = currentPhase;
    }

    await this.ddb.send(new UpdateCommand({
      TableName: this.tableName,
      Key: {
        pk: `TASK#${taskId}`,
        sk: `TASK#${taskId}`,
      },
      UpdateExpression: updateExpression,
      ExpressionAttributeNames: expressionAttributeNames,
      ExpressionAttributeValues: expressionAttributeValues,
    }));
  }

  async completeTask(
    taskId: string,
    result: Record<string, unknown>
  ): Promise<void> {
    const now = new Date().toISOString();

    await this.ddb.send(new UpdateCommand({
      TableName: this.tableName,
      Key: {
        pk: `TASK#${taskId}`,
        sk: `TASK#${taskId}`,
      },
      UpdateExpression: `
        SET #status = :status,
            #result = :result,
            #completedAt = :completedAt,
            #updatedAt = :updatedAt
      `,
      ExpressionAttributeNames: {
        '#status': 'status',
        '#result': 'result',
        '#completedAt': 'completedAt',
        '#updatedAt': 'updatedAt',
      },
      ExpressionAttributeValues: {
        ':status': TaskStatus.COMPLETED,
        ':result': result,
        ':completedAt': now,
        ':updatedAt': now,
      },
    }));
  }

  async failTask(taskId: string, error: string): Promise<void> {
    const now = new Date().toISOString();

    await this.ddb.send(new UpdateCommand({
      TableName: this.tableName,
      Key: {
        pk: `TASK#${taskId}`,
        sk: `TASK#${taskId}`,
      },
      UpdateExpression: `
        SET #status = :status,
            #error = :error,
            #completedAt = :completedAt,
            #updatedAt = :updatedAt
      `,
      ExpressionAttributeNames: {
        '#status': 'status',
        '#error': 'error',
        '#completedAt': 'completedAt',
        '#updatedAt': 'updatedAt',
      },
      ExpressionAttributeValues: {
        ':status': TaskStatus.FAILED,
        ':error': error,
        ':completedAt': now,
        ':updatedAt': now,
      },
    }));
  }

  async getTaskState(taskId: string): Promise<TaskState | null> {
    const response = await this.ddb.send(new GetCommand({
      TableName: this.tableName,
      Key: {
        pk: `TASK#${taskId}`,
        sk: `TASK#${taskId}`,
      },
    }));

    return response.Item as TaskState | null;
  }

  async getUserTasks(
    userId: string,
    limit: number = 20
  ): Promise<TaskState[]> {
    const response = await this.ddb.send(new QueryCommand({
      TableName: this.tableName,
      IndexName: 'gsi1',
      KeyConditionExpression: '#gsi1pk = :gsi1pk',
      ExpressionAttributeNames: {
        '#gsi1pk': 'gsi1pk',
      },
      ExpressionAttributeValues: {
        ':gsi1pk': `USER#${userId}`,
      },
      ScanIndexForward: false, // 新しい順
      Limit: limit,
    }));

    return (response.Items || []) as TaskState[];
  }
}
```

### AppSync Eventsによるリアルタイム通知

AppSync Events APIへの発行は、SigV4署名を使ったHTTPリクエストで行います。

> **注意**: `@aws-sdk/client-appsync-events`というパッケージは存在しません。AppSync Events APIはSigV4署名付きHTTPリクエストで呼び出します。

```typescript
// services/realtime-notifier.ts
import { SignatureV4 } from '@smithy/signature-v4';
import { Sha256 } from '@aws-crypto/sha256-js';
import { defaultProvider } from '@aws-sdk/credential-provider-node';
import { HttpRequest } from '@smithy/protocol-http';

interface TaskUpdateEvent {
  type: 'progress' | 'completed' | 'failed';
  taskId: string;
  data: {
    status: string;
    progress?: number;
    totalItems?: number;
    currentPhase?: string;
    result?: Record<string, unknown>;
    error?: string;
  };
  timestamp: string;
}

export class RealtimeNotifier {
  private httpEndpoint: string;
  private region: string;

  constructor(httpEndpoint: string, region?: string) {
    this.httpEndpoint = httpEndpoint;
    this.region = region || process.env.AWS_REGION || 'ap-northeast-1';
  }

  async notifyProgress(
    userId: string,
    taskId: string,
    progress: number,
    totalItems: number,
    currentPhase?: string
  ): Promise<void> {
    const event: TaskUpdateEvent = {
      type: 'progress',
      taskId,
      data: {
        status: 'processing',
        progress,
        totalItems,
        currentPhase,
      },
      timestamp: new Date().toISOString(),
    };

    await this.publishEvent(`/tasks/${userId}`, event);
  }

  async notifyCompletion(
    userId: string,
    taskId: string,
    result: Record<string, unknown>
  ): Promise<void> {
    const event: TaskUpdateEvent = {
      type: 'completed',
      taskId,
      data: {
        status: 'completed',
        result,
      },
      timestamp: new Date().toISOString(),
    };

    await this.publishEvent(`/tasks/${userId}`, event);
  }

  async notifyFailure(
    userId: string,
    taskId: string,
    error: string
  ): Promise<void> {
    const event: TaskUpdateEvent = {
      type: 'failed',
      taskId,
      data: {
        status: 'failed',
        error,
      },
      timestamp: new Date().toISOString(),
    };

    await this.publishEvent(`/tasks/${userId}`, event);
  }

  private async publishEvent(
    channel: string,
    event: TaskUpdateEvent
  ): Promise<void> {
    const url = new URL(`${this.httpEndpoint}/event`);
    const body = JSON.stringify({
      channel,
      events: [JSON.stringify(event)],
    });

    // SigV4署名付きHTTPリクエストを作成
    const request = new HttpRequest({
      method: 'POST',
      hostname: url.hostname,
      path: url.pathname,
      headers: {
        'Content-Type': 'application/json',
        host: url.hostname,
      },
      body,
    });

    const signer = new SignatureV4({
      credentials: defaultProvider(),
      region: this.region,
      service: 'appsync',
      sha256: Sha256,
    });

    const signedRequest = await signer.sign(request);

    // 署名付きリクエストを送信
    const response = await fetch(`${this.httpEndpoint}/event`, {
      method: signedRequest.method,
      headers: signedRequest.headers as HeadersInit,
      body: signedRequest.body as string,
    });

    if (!response.ok) {
      console.error('Failed to publish event', {
        status: response.status,
        channel,
        event,
      });
    }
  }
}
```

### 進捗更新を含むLambda実装

```typescript
// handlers/bulk-process.ts
import { SQSEvent } from 'aws-lambda';
import { TaskStateManager } from '../services/task-state-manager';
import { RealtimeNotifier } from '../services/realtime-notifier';

const stateManager = new TaskStateManager(ddbClient, process.env.TABLE_NAME!);
const notifier = new RealtimeNotifier(process.env.APPSYNC_ENDPOINT!);

const PROGRESS_UPDATE_INTERVAL = 10;

interface BulkProcessMessage {
  taskId: string;
  userId: string;
  items: string[];
}

export async function handler(event: SQSEvent): Promise<void> {
  for (const record of event.Records) {
    const message: BulkProcessMessage = JSON.parse(record.body);
    await processBulkTask(message);
  }
}

async function processBulkTask(message: BulkProcessMessage): Promise<void> {
  const { taskId, userId, items } = message;
  const totalItems = items.length;

  try {
    // タスク開始
    await stateManager.initializeTask(taskId, userId, totalItems);

    let processed = 0;

    for (const item of items) {
      // アイテム処理
      await processItem(item);
      processed++;

      // 進捗更新
      if (processed % PROGRESS_UPDATE_INTERVAL === 0 || processed === totalItems) {
        await stateManager.updateProgress(taskId, processed);

        // リアルタイム通知
        await notifier.notifyProgress(
          userId,
          taskId,
          processed,
          totalItems
        );
      }
    }

    // 完了
    const result = { processedItems: processed };
    await stateManager.completeTask(taskId, result);
    await notifier.notifyCompletion(userId, taskId, result);

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    await stateManager.failTask(taskId, errorMessage);
    await notifier.notifyFailure(userId, taskId, errorMessage);
    throw error;
  }
}
```

### API Gatewayエンドポイント

```typescript
// handlers/api/tasks.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { TaskStateManager } from '../../services/task-state-manager';

const stateManager = new TaskStateManager(ddbClient, process.env.TABLE_NAME!);

// GET /tasks/{taskId}/status
export async function getTaskStatus(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  const taskId = event.pathParameters?.taskId;

  if (!taskId) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'taskId is required' }),
    };
  }

  const task = await stateManager.getTaskState(taskId);

  if (!task) {
    return {
      statusCode: 404,
      body: JSON.stringify({ error: 'Task not found' }),
    };
  }

  // 認証ユーザーのタスクかチェック
  const userId = event.requestContext.authorizer?.userId;
  if (task.userId !== userId) {
    return {
      statusCode: 403,
      body: JSON.stringify({ error: 'Access denied' }),
    };
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
    startedAt: task.startedAt,
    completedAt: task.completedAt,
  };

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': task.status === 'completed' || task.status === 'failed'
        ? 'public, max-age=3600'
        : 'no-cache',
    },
    body: JSON.stringify(response),
  };
}

// GET /tasks (ユーザーのタスク一覧)
export async function listTasks(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  const userId = event.requestContext.authorizer?.userId;
  const limit = parseInt(event.queryStringParameters?.limit || '20');

  const tasks = await stateManager.getUserTasks(userId, limit);

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      tasks: tasks.map(task => ({
        taskId: task.taskId,
        status: task.status,
        progress: task.totalItems
          ? Math.round((task.progress / task.totalItems) * 100)
          : 0,
        startedAt: task.startedAt,
        completedAt: task.completedAt,
      })),
    }),
  };
}
```

---

## Lambda関数の設計パターン

### 冪等性の確保

```typescript
// services/idempotency.ts
import {
  DynamoDBDocumentClient,
  PutCommand,
  GetCommand,
  DeleteCommand,
} from '@aws-sdk/lib-dynamodb';
import { ConditionalCheckFailedException } from '@aws-sdk/client-dynamodb';

interface IdempotencyRecord {
  pk: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  result?: unknown;
  error?: string;
  expiresAt: number;
  createdAt: string;
}

export class IdempotencyManager {
  constructor(
    private ddb: DynamoDBDocumentClient,
    private tableName: string,
    private ttlSeconds: number = 3600
  ) {}

  async acquireLock(idempotencyKey: string): Promise<boolean> {
    const expiresAt = Math.floor(Date.now() / 1000) + this.ttlSeconds;

    try {
      await this.ddb.send(new PutCommand({
        TableName: this.tableName,
        Item: {
          pk: `IDEMPOTENCY#${idempotencyKey}`,
          status: 'IN_PROGRESS',
          expiresAt,
          createdAt: new Date().toISOString(),
        },
        ConditionExpression: 'attribute_not_exists(pk) OR #status = :failed',
        ExpressionAttributeNames: {
          '#status': 'status',
        },
        ExpressionAttributeValues: {
          ':failed': 'FAILED',
        },
      }));

      return true;
    } catch (error) {
      if (error instanceof ConditionalCheckFailedException) {
        // 既に処理中または完了
        return false;
      }
      throw error;
    }
  }

  async getExistingResult(idempotencyKey: string): Promise<unknown | null> {
    const response = await this.ddb.send(new GetCommand({
      TableName: this.tableName,
      Key: { pk: `IDEMPOTENCY#${idempotencyKey}` },
    }));

    const record = response.Item as IdempotencyRecord | undefined;

    if (record?.status === 'COMPLETED') {
      return record.result;
    }

    return null;
  }

  async recordSuccess(
    idempotencyKey: string,
    result: unknown
  ): Promise<void> {
    await this.ddb.send(new PutCommand({
      TableName: this.tableName,
      Item: {
        pk: `IDEMPOTENCY#${idempotencyKey}`,
        status: 'COMPLETED',
        result,
        expiresAt: Math.floor(Date.now() / 1000) + this.ttlSeconds,
        createdAt: new Date().toISOString(),
      },
    }));
  }

  async recordFailure(
    idempotencyKey: string,
    error: string
  ): Promise<void> {
    await this.ddb.send(new PutCommand({
      TableName: this.tableName,
      Item: {
        pk: `IDEMPOTENCY#${idempotencyKey}`,
        status: 'FAILED',
        error,
        expiresAt: Math.floor(Date.now() / 1000) + this.ttlSeconds,
        createdAt: new Date().toISOString(),
      },
    }));
  }
}

// 使用例
export async function idempotentHandler<T>(
  idempotencyKey: string,
  handler: () => Promise<T>
): Promise<T> {
  const manager = new IdempotencyManager(ddbClient, process.env.IDEMPOTENCY_TABLE!);

  // 既存の結果をチェック
  const existingResult = await manager.getExistingResult(idempotencyKey);
  if (existingResult !== null) {
    console.log('Returning cached result', { idempotencyKey });
    return existingResult as T;
  }

  // ロック取得
  const acquired = await manager.acquireLock(idempotencyKey);
  if (!acquired) {
    // 他の実行が進行中
    throw new Error('Operation is already in progress');
  }

  try {
    const result = await handler();
    await manager.recordSuccess(idempotencyKey, result);
    return result;
  } catch (error) {
    await manager.recordFailure(
      idempotencyKey,
      error instanceof Error ? error.message : 'Unknown error'
    );
    throw error;
  }
}
```

### Step Functionsによる長時間処理

```typescript
// step-functions/task-processor.asl.json
{
  "Comment": "Long-running task processor",
  "StartAt": "Initialize",
  "States": {
    "Initialize": {
      "Type": "Task",
      "Resource": "${InitializeFunctionArn}",
      "ResultPath": "$.taskState",
      "Next": "ProcessBatch"
    },
    "ProcessBatch": {
      "Type": "Task",
      "Resource": "${ProcessBatchFunctionArn}",
      "ResultPath": "$.batchResult",
      "Retry": [
        {
          "ErrorEquals": ["RetryableError"],
          "IntervalSeconds": 5,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "MarkFailed"
        }
      ],
      "Next": "CheckCompletion"
    },
    "CheckCompletion": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.batchResult.isComplete",
          "BooleanEquals": true,
          "Next": "MarkCompleted"
        }
      ],
      "Default": "UpdateProgress"
    },
    "UpdateProgress": {
      "Type": "Task",
      "Resource": "${UpdateProgressFunctionArn}",
      "ResultPath": "$.progressResult",
      "Next": "ProcessBatch"
    },
    "MarkCompleted": {
      "Type": "Task",
      "Resource": "${MarkCompletedFunctionArn}",
      "End": true
    },
    "MarkFailed": {
      "Type": "Task",
      "Resource": "${MarkFailedFunctionArn}",
      "End": true
    }
  }
}
```

```typescript
// handlers/step-functions/process-batch.ts
interface BatchInput {
  taskId: string;
  userId: string;
  lastProcessedId?: string;
  batchSize: number;
}

interface BatchOutput {
  isComplete: boolean;
  processedCount: number;
  lastProcessedId: string;
}

export async function handler(input: BatchInput): Promise<BatchOutput> {
  const { taskId, lastProcessedId, batchSize } = input;

  // バッチを取得して処理
  const items = await getItemsBatch(taskId, lastProcessedId, batchSize);

  if (items.length === 0) {
    return {
      isComplete: true,
      processedCount: 0,
      lastProcessedId: lastProcessedId || '',
    };
  }

  let processedCount = 0;
  let lastId = lastProcessedId || '';

  for (const item of items) {
    await processItem(item);
    processedCount++;
    lastId = item.id;
  }

  return {
    isComplete: items.length < batchSize,
    processedCount,
    lastProcessedId: lastId,
  };
}
```

### Lambda Layerの活用

```typescript
// layers/common/nodejs/utils/index.ts
export * from './logger';
export * from './errors';
export * from './validation';

// layers/common/nodejs/utils/errors.ts
export class RetryableError extends Error {
  constructor(message: string, public readonly retryAfter?: number) {
    super(message);
    this.name = 'RetryableError';
  }
}

export class NonRetryableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NonRetryableError';
  }
}

export class ValidationError extends NonRetryableError {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}
```

---

## 継続可能な処理（Continuable Processing）

AWS Serverless環境では、Lambda の実行時間制限（最大15分）やスケーラビリティの観点から、長時間実行される処理を中断・再開可能にする仕組みが重要です。

### Step Functions Distributed Map

大規模なデータセットを並列処理し、各アイテムの処理を独立して管理できます。

```json
// step-functions/distributed-map.asl.json
{
  "Comment": "Large-scale parallel processing with Distributed Map",
  "StartAt": "ProcessItems",
  "States": {
    "ProcessItems": {
      "Type": "Map",
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "DISTRIBUTED",
          "ExecutionType": "STANDARD"
        },
        "StartAt": "ProcessSingleItem",
        "States": {
          "ProcessSingleItem": {
            "Type": "Task",
            "Resource": "${ProcessItemFunctionArn}",
            "Retry": [
              {
                "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
                "IntervalSeconds": 2,
                "MaxAttempts": 6,
                "BackoffRate": 2
              },
              {
                "ErrorEquals": ["RetryableError"],
                "IntervalSeconds": 5,
                "MaxAttempts": 3,
                "BackoffRate": 2
              }
            ],
            "End": true
          }
        }
      },
      "ItemReader": {
        "Resource": "arn:aws:states:::s3:getObject",
        "ReaderConfig": {
          "InputType": "JSON",
          "MaxItems": 1000000
        },
        "Parameters": {
          "Bucket.$": "$.inputBucket",
          "Key.$": "$.inputKey"
        }
      },
      "MaxConcurrency": 1000,
      "ResultWriter": {
        "Resource": "arn:aws:states:::s3:putObject",
        "Parameters": {
          "Bucket.$": "$.outputBucket",
          "Prefix": "results/"
        }
      },
      "ToleratedFailurePercentage": 5,
      "End": true
    }
  }
}
```

```typescript
// handlers/step-functions/process-single-item.ts
interface ItemInput {
  id: string;
  data: Record<string, unknown>;
}

interface ItemOutput {
  id: string;
  status: 'success' | 'failed';
  result?: Record<string, unknown>;
  error?: string;
}

export async function handler(input: ItemInput): Promise<ItemOutput> {
  const { id, data } = input;

  try {
    // 個別アイテムの処理（最大15分以内に完了する単位）
    const result = await processItem(data);

    return {
      id,
      status: 'success',
      result,
    };
  } catch (error) {
    // リトライ可能かどうかを判定
    if (isRetryableError(error)) {
      throw new RetryableError(`Retryable error for item ${id}: ${error.message}`);
    }

    // リトライ不可のエラーは結果として返す（処理全体を止めない）
    return {
      id,
      status: 'failed',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

function isRetryableError(error: unknown): boolean {
  if (error instanceof Error) {
    // ネットワークエラー、スロットリング等
    return error.message.includes('ECONNRESET') ||
           error.message.includes('TooManyRequests') ||
           error.message.includes('ServiceUnavailable');
  }
  return false;
}
```

### AWS Lambda Powertools Idempotency

Lambda Powertoolsの冪等性機能を使用して、チェックポイント・リプレイパターンを実装できます。

```typescript
// handlers/idempotent-processor.ts
import { makeIdempotent, IdempotencyConfig } from '@aws-lambda-powertools/idempotency';
import { DynamoDBPersistenceLayer } from '@aws-lambda-powertools/idempotency/dynamodb';
import { SQSEvent, SQSBatchResponse } from 'aws-lambda';

// 永続化レイヤーの設定
const persistenceStore = new DynamoDBPersistenceLayer({
  tableName: process.env.IDEMPOTENCY_TABLE!,
});

const idempotencyConfig = new IdempotencyConfig({
  persistenceStore,
  expiresAfterSeconds: 3600, // 1時間
  useLocalCache: true,
  maxLocalCacheSize: 1000,
  eventKeyJmesPath: 'taskId', // イベントからキーを抽出
});

interface TaskPayload {
  taskId: string;
  userId: string;
  items: Array<{ id: string; data: Record<string, unknown> }>;
}

interface TaskResult {
  processedCount: number;
  failedCount: number;
  results: Array<{ id: string; status: string }>;
}

// 冪等な処理関数
const processTaskIdempotent = makeIdempotent(
  async (payload: TaskPayload): Promise<TaskResult> => {
    const results: Array<{ id: string; status: string }> = [];
    let processedCount = 0;
    let failedCount = 0;

    for (const item of payload.items) {
      try {
        await processItem(item);
        results.push({ id: item.id, status: 'success' });
        processedCount++;
      } catch (error) {
        results.push({ id: item.id, status: 'failed' });
        failedCount++;
      }
    }

    return { processedCount, failedCount, results };
  },
  {
    persistenceStore,
    config: idempotencyConfig,
  }
);

export async function handler(event: SQSEvent): Promise<SQSBatchResponse> {
  const batchItemFailures: SQSBatchResponse['batchItemFailures'] = [];

  for (const record of event.Records) {
    try {
      const payload: TaskPayload = JSON.parse(record.body);

      // 冪等に処理（同じtaskIdで再実行されても同じ結果を返す）
      const result = await processTaskIdempotent(payload);

      console.log('Task completed', {
        taskId: payload.taskId,
        result,
      });
    } catch (error) {
      console.error('Failed to process record', {
        messageId: record.messageId,
        error,
      });
      batchItemFailures.push({ itemIdentifier: record.messageId });
    }
  }

  return { batchItemFailures };
}
```

### チェックポイント付きバッチ処理

長時間の処理を小さなバッチに分割し、チェックポイントを保存しながら処理を進めるパターンです。

```typescript
// services/checkpoint-manager.ts
import { DynamoDBDocumentClient, PutCommand, GetCommand } from '@aws-sdk/lib-dynamodb';

interface Checkpoint {
  taskId: string;
  lastProcessedId: string | null;
  processedCount: number;
  totalCount: number;
  phase: string;
  metadata: Record<string, unknown>;
  updatedAt: string;
  expiresAt: number;
}

export class CheckpointManager {
  constructor(
    private ddb: DynamoDBDocumentClient,
    private tableName: string
  ) {}

  async saveCheckpoint(checkpoint: Omit<Checkpoint, 'updatedAt' | 'expiresAt'>): Promise<void> {
    const ttl = Math.floor(Date.now() / 1000) + 7 * 24 * 60 * 60; // 7日間

    await this.ddb.send(new PutCommand({
      TableName: this.tableName,
      Item: {
        pk: `CHECKPOINT#${checkpoint.taskId}`,
        sk: `CHECKPOINT#${checkpoint.taskId}`,
        ...checkpoint,
        updatedAt: new Date().toISOString(),
        expiresAt: ttl,
      },
    }));
  }

  async getCheckpoint(taskId: string): Promise<Checkpoint | null> {
    const response = await this.ddb.send(new GetCommand({
      TableName: this.tableName,
      Key: {
        pk: `CHECKPOINT#${taskId}`,
        sk: `CHECKPOINT#${taskId}`,
      },
    }));

    return response.Item as Checkpoint | null;
  }

  async deleteCheckpoint(taskId: string): Promise<void> {
    await this.ddb.send(new DeleteCommand({
      TableName: this.tableName,
      Key: {
        pk: `CHECKPOINT#${taskId}`,
        sk: `CHECKPOINT#${taskId}`,
      },
    }));
  }
}
```

```typescript
// handlers/resumable-batch-processor.ts
import { SQSEvent } from 'aws-lambda';
import { CheckpointManager } from '../services/checkpoint-manager';

const checkpointManager = new CheckpointManager(ddbClient, process.env.TABLE_NAME!);

const BATCH_SIZE = 100;
const MAX_EXECUTION_TIME_MS = 14 * 60 * 1000; // 14分（15分制限の安全マージン）
const CHECKPOINT_INTERVAL = 50;

interface ResumableTaskMessage {
  taskId: string;
  userId: string;
  queryConditions: Record<string, unknown>;
}

export async function handler(event: SQSEvent): Promise<void> {
  for (const record of event.Records) {
    const message: ResumableTaskMessage = JSON.parse(record.body);
    await processResumableTask(message);
  }
}

async function processResumableTask(message: ResumableTaskMessage): Promise<void> {
  const { taskId, userId, queryConditions } = message;
  const startTime = Date.now();

  // 既存のチェックポイントを取得
  let checkpoint = await checkpointManager.getCheckpoint(taskId);
  let lastProcessedId = checkpoint?.lastProcessedId || null;
  let processedCount = checkpoint?.processedCount || 0;

  // 処理対象の総数を取得（初回のみ）
  const totalCount = checkpoint?.totalCount || await getTotalCount(queryConditions);

  console.log('Resuming task', {
    taskId,
    lastProcessedId,
    processedCount,
    totalCount,
  });

  // バッチ処理ループ
  while (true) {
    // タイムアウトチェック
    if (Date.now() - startTime > MAX_EXECUTION_TIME_MS) {
      console.log('Approaching timeout, saving checkpoint and re-queuing', {
        taskId,
        processedCount,
        totalCount,
      });

      // チェックポイントを保存
      await checkpointManager.saveCheckpoint({
        taskId,
        lastProcessedId,
        processedCount,
        totalCount,
        phase: 'processing',
        metadata: { queryConditions },
      });

      // 自分自身を再キューイング
      await requeue(message);
      return;
    }

    // バッチを取得
    const batch = await fetchBatch(queryConditions, lastProcessedId, BATCH_SIZE);

    if (batch.length === 0) {
      // 処理完了
      console.log('Task completed', { taskId, processedCount });
      await checkpointManager.deleteCheckpoint(taskId);
      await markTaskCompleted(taskId, { processedCount });
      return;
    }

    // バッチを処理
    for (const item of batch) {
      await processItem(item);
      lastProcessedId = item.id;
      processedCount++;

      // 定期的にチェックポイントを保存
      if (processedCount % CHECKPOINT_INTERVAL === 0) {
        await checkpointManager.saveCheckpoint({
          taskId,
          lastProcessedId,
          processedCount,
          totalCount,
          phase: 'processing',
          metadata: { queryConditions },
        });

        // 進捗通知
        await notifyProgress(userId, taskId, processedCount, totalCount);
      }
    }
  }
}

async function requeue(message: ResumableTaskMessage): Promise<void> {
  const sqs = new SQSClient({});
  await sqs.send(new SendMessageCommand({
    QueueUrl: process.env.QUEUE_URL!,
    MessageBody: JSON.stringify(message),
    DelaySeconds: 1, // 少し待ってから再処理
  }));
}
```

### Step Functions Express Workflow + Standard Workflow の組み合わせ

短時間の処理（Express）と長時間の処理（Standard）を組み合わせるパターンです。

```json
// step-functions/hybrid-workflow.asl.json
{
  "Comment": "Hybrid workflow combining Express and Standard executions",
  "StartAt": "PrepareData",
  "States": {
    "PrepareData": {
      "Type": "Task",
      "Resource": "${PrepareDataFunctionArn}",
      "ResultPath": "$.preparedData",
      "Next": "ProcessInBatches"
    },
    "ProcessInBatches": {
      "Type": "Map",
      "ItemsPath": "$.preparedData.batches",
      "MaxConcurrency": 10,
      "Iterator": {
        "StartAt": "ProcessBatchExpress",
        "States": {
          "ProcessBatchExpress": {
            "Type": "Task",
            "Resource": "arn:aws:states:::states:startExecution.sync:2",
            "Parameters": {
              "StateMachineArn": "${ExpressProcessorArn}",
              "Input.$": "$"
            },
            "Retry": [
              {
                "ErrorEquals": ["States.TaskFailed"],
                "IntervalSeconds": 5,
                "MaxAttempts": 3,
                "BackoffRate": 2
              }
            ],
            "End": true
          }
        }
      },
      "ResultPath": "$.batchResults",
      "Next": "AggregateResults"
    },
    "AggregateResults": {
      "Type": "Task",
      "Resource": "${AggregateResultsFunctionArn}",
      "End": true
    }
  }
}
```

### コールバックパターンによる一時停止と再開

外部システムとの連携や手動承認が必要な場合に、Step Functions のコールバックパターンを使用します。

```typescript
// handlers/step-functions/wait-for-approval.ts
import { SFNClient, SendTaskSuccessCommand, SendTaskFailureCommand } from '@aws-sdk/client-sfn';

const sfn = new SFNClient({});

interface ApprovalRequest {
  taskToken: string;
  taskId: string;
  userId: string;
  details: Record<string, unknown>;
}

// Step Functions から呼び出される Lambda
export async function requestApproval(event: ApprovalRequest): Promise<void> {
  const { taskToken, taskId, userId, details } = event;

  // 承認リクエストを保存
  await saveApprovalRequest({
    taskToken,
    taskId,
    userId,
    details,
    requestedAt: new Date().toISOString(),
    status: 'pending',
  });

  // ユーザーに通知（メール、Slack等）
  await sendApprovalNotification(userId, {
    taskId,
    details,
    approveUrl: `${process.env.APP_URL}/approvals/${taskId}/approve`,
    rejectUrl: `${process.env.APP_URL}/approvals/${taskId}/reject`,
  });

  // この関数は戻り、Step Functions は taskToken でコールバックを待つ
}

// 承認APIエンドポイント
export async function approveTask(taskId: string): Promise<void> {
  const request = await getApprovalRequest(taskId);

  if (!request || request.status !== 'pending') {
    throw new Error('Invalid or already processed approval request');
  }

  // Step Functions に成功を通知
  await sfn.send(new SendTaskSuccessCommand({
    taskToken: request.taskToken,
    output: JSON.stringify({
      approved: true,
      approvedAt: new Date().toISOString(),
    }),
  }));

  // ステータス更新
  await updateApprovalStatus(taskId, 'approved');
}

// 却下APIエンドポイント
export async function rejectTask(taskId: string, reason: string): Promise<void> {
  const request = await getApprovalRequest(taskId);

  if (!request || request.status !== 'pending') {
    throw new Error('Invalid or already processed approval request');
  }

  // Step Functions に失敗を通知
  await sfn.send(new SendTaskFailureCommand({
    taskToken: request.taskToken,
    error: 'ApprovalRejected',
    cause: reason,
  }));

  // ステータス更新
  await updateApprovalStatus(taskId, 'rejected');
}
```

```json
// Step Functions定義の該当部分
{
  "WaitForApproval": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
    "Parameters": {
      "FunctionName": "${RequestApprovalFunctionArn}",
      "Payload": {
        "taskToken.$": "$$.Task.Token",
        "taskId.$": "$.taskId",
        "userId.$": "$.userId",
        "details.$": "$.approvalDetails"
      }
    },
    "TimeoutSeconds": 604800,
    "Catch": [
      {
        "ErrorEquals": ["States.Timeout"],
        "ResultPath": "$.error",
        "Next": "HandleTimeout"
      },
      {
        "ErrorEquals": ["ApprovalRejected"],
        "ResultPath": "$.error",
        "Next": "HandleRejection"
      }
    ],
    "Next": "ContinueProcessing"
  }
}
```

### 手法の比較と選択ガイド

| 観点 | Distributed Map | Powertools Idempotency | チェックポイント+再キュー | コールバック |
|------|-----------------|------------------------|-------------------------|-------------|
| ユースケース | 大規模並列処理 | 冪等性が必要な処理 | 長時間の順次処理 | 外部連携・承認 |
| スケーラビリティ | 非常に高（〜10,000並列） | 中 | 低〜中 | 中 |
| 複雑さ | 中 | 低 | 中 | 中〜高 |
| コスト | 処理量に比例 | DynamoDB使用量 | SQS + DynamoDB | Step Functions実行 |
| 最大処理時間 | 実質無制限 | 15分/Lambda | 実質無制限 | 最大1年 |
| エラー回復 | 自動リトライ | キャッシュからリプレイ | チェックポイントから再開 | タスクトークンで再開 |

**選択ガイド:**

- **Distributed Map**: 数千〜数百万件のアイテムを並列処理する場合
- **Powertools Idempotency**: API呼び出しやイベント処理で重複実行を防ぎたい場合
- **チェックポイント+再キュー**: 順次処理が必要で、Lambda制限を超える可能性がある場合
- **コールバック**: 人間の承認や外部システムの応答を待つ必要がある場合

---

## テスト戦略

### Lambda関数のユニットテスト

```typescript
// __tests__/handlers/process-task.test.ts
import { SQSEvent, Context } from 'aws-lambda';
import { handler } from '../../handlers/process-task';
import { mockClient } from 'aws-sdk-client-mock';
import { DynamoDBDocumentClient, UpdateCommand } from '@aws-sdk/lib-dynamodb';

const ddbMock = mockClient(DynamoDBDocumentClient);

describe('ProcessTask Handler', () => {
  beforeEach(() => {
    ddbMock.reset();
  });

  const createSQSEvent = (body: Record<string, unknown>): SQSEvent => ({
    Records: [
      {
        messageId: 'test-message-id',
        receiptHandle: 'test-receipt-handle',
        body: JSON.stringify(body),
        attributes: {
          ApproximateReceiveCount: '1',
          SentTimestamp: '1234567890',
          SenderId: 'test-sender',
          ApproximateFirstReceiveTimestamp: '1234567890',
        },
        messageAttributes: {},
        md5OfBody: 'test-md5',
        eventSource: 'aws:sqs',
        eventSourceARN: 'arn:aws:sqs:us-east-1:123456789:test-queue',
        awsRegion: 'us-east-1',
      },
    ],
  });

  const mockContext: Context = {
    awsRequestId: 'test-request-id',
    functionName: 'test-function',
    functionVersion: '1',
    invokedFunctionArn: 'arn:aws:lambda:us-east-1:123456789:function:test',
    memoryLimitInMB: '128',
    logGroupName: '/aws/lambda/test',
    logStreamName: '2024/01/01/test',
    callbackWaitsForEmptyEventLoop: true,
    getRemainingTimeInMillis: () => 30000,
    done: () => {},
    fail: () => {},
    succeed: () => {},
  };

  it('should process valid message successfully', async () => {
    const event = createSQSEvent({
      taskId: 'test-task-id',
      taskType: 'export',
      userId: 'user-123',
      params: { operation: 'csv' },
      metadata: {
        requestedAt: new Date().toISOString(),
        requestId: 'req-123',
        traceId: 'trace-123',
      },
    });

    ddbMock.on(UpdateCommand).resolves({});

    const result = await handler(event, mockContext);

    expect(result.batchItemFailures).toHaveLength(0);
  });

  it('should report failure for invalid message', async () => {
    const event = createSQSEvent({
      // Missing required fields
      taskId: 'test-task-id',
    });

    const result = await handler(event, mockContext);

    expect(result.batchItemFailures).toHaveLength(1);
    expect(result.batchItemFailures[0].itemIdentifier).toBe('test-message-id');
  });
});
```

### ローカルテスト（LocalStack）

```typescript
// __tests__/integration/local-stack.test.ts
import { SQSClient, SendMessageCommand, ReceiveMessageCommand } from '@aws-sdk/client-sqs';
import { DynamoDBClient, CreateTableCommand } from '@aws-sdk/client-dynamodb';

describe('LocalStack Integration', () => {
  const sqsClient = new SQSClient({
    endpoint: 'http://localhost:4566',
    region: 'us-east-1',
    credentials: {
      accessKeyId: 'test',
      secretAccessKey: 'test',
    },
  });

  const queueUrl = 'http://localhost:4566/000000000000/test-queue';

  beforeAll(async () => {
    // LocalStackでリソースを作成
    // ...
  });

  it('should process message through SQS', async () => {
    // メッセージを送信
    await sqsClient.send(new SendMessageCommand({
      QueueUrl: queueUrl,
      MessageBody: JSON.stringify({
        taskId: 'test-task',
        taskType: 'export',
        userId: 'user-123',
      }),
    }));

    // メッセージを受信（Lambda関数をシミュレート）
    const response = await sqsClient.send(new ReceiveMessageCommand({
      QueueUrl: queueUrl,
      MaxNumberOfMessages: 1,
      WaitTimeSeconds: 5,
    }));

    expect(response.Messages).toHaveLength(1);
    const message = JSON.parse(response.Messages![0].Body!);
    expect(message.taskId).toBe('test-task');
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
    // 認証トークンを取得
    authToken = await getAuthToken();
  });

  it('should complete full task lifecycle', async () => {
    // 1. タスク作成
    const createResponse = await axios.post(
      `${API_URL}/tasks`,
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

    // 2. タスク完了を待つ
    const maxWait = 60000; // 60秒
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      const statusResponse = await axios.get(
        `${API_URL}/tasks/${taskId}/status`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
        }
      );

      if (statusResponse.data.status === 'completed') {
        expect(statusResponse.data.result).toBeDefined();
        return;
      }

      if (statusResponse.data.status === 'failed') {
        throw new Error(`Task failed: ${statusResponse.data.error}`);
      }

      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error('Task did not complete within timeout');
  });
});
```

---

## その他のベストプラクティス

### コールドスタート対策

```typescript
// handlers/process-task.ts
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';
import { S3Client } from '@aws-sdk/client-s3';

// クライアントをハンドラー外で初期化（コールドスタート時に一度だけ）
const ddbClient = DynamoDBDocumentClient.from(
  new DynamoDBClient({})
);
const s3Client = new S3Client({});

// 環境変数の読み込みも外で
const TABLE_NAME = process.env.TABLE_NAME!;
const BUCKET_NAME = process.env.BUCKET_NAME!;

export async function handler(event: SQSEvent): Promise<void> {
  // ここでは初期化済みのクライアントを使用
}
```

### メモリとタイムアウトの設定

```typescript
// infrastructure/lambda.ts (CDK)
import * as lambda from 'aws-cdk-lib/aws-lambda';

const processorFunction = new lambda.Function(this, 'ProcessorFunction', {
  runtime: lambda.Runtime.NODEJS_20_X,
  handler: 'handlers/process-task.handler',
  code: lambda.Code.fromAsset('dist'),
  memorySize: 1024, // メモリに応じてCPUも増加
  timeout: cdk.Duration.minutes(15), // 最大15分
  environment: {
    TABLE_NAME: table.tableName,
    BUCKET_NAME: bucket.bucketName,
  },
  tracing: lambda.Tracing.ACTIVE, // X-Ray有効化
  reservedConcurrentExecutions: 100, // 同時実行数制限
});
```

### メトリクスとダッシュボード

```typescript
// services/metrics.ts
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';

const cloudwatch = new CloudWatchClient({});

export async function recordMetric(
  metricName: string,
  value: number,
  unit: string,
  dimensions?: Record<string, string>
): Promise<void> {
  await cloudwatch.send(new PutMetricDataCommand({
    Namespace: 'AsyncTasks',
    MetricData: [
      {
        MetricName: metricName,
        Value: value,
        Unit: unit,
        Dimensions: dimensions
          ? Object.entries(dimensions).map(([Name, Value]) => ({ Name, Value }))
          : undefined,
        Timestamp: new Date(),
      },
    ],
  }));
}

// 使用例
await recordMetric('TaskDuration', duration, 'Milliseconds', {
  TaskType: taskType,
});
await recordMetric('TasksCompleted', 1, 'Count', {
  TaskType: taskType,
});
```

---

## 参照

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Amazon SQS Best Practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [AppSync Events Documentation](https://docs.aws.amazon.com/appsync/latest/devguide/events.html)
- [Step Functions Distributed Map](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-asl-use-map-state-distributed.html)
- [AWS Lambda Powertools for TypeScript - Idempotency](https://docs.powertools.aws.dev/lambda/typescript/latest/utilities/idempotency/)
- [Step Functions Callback Pattern](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html#connect-wait-token)
