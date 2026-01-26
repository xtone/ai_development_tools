---
title: AWS SQS + AppSync Events + DynamoDBによる実装
---

## AWS SQS + AppSync Events + DynamoDBによる実装

AWSのマネージドサービスを組み合わせて、完全なサーバーレスアーキテクチャで非同期処理を実現します。SQSでタスクキューイング、Lambdaでジョブ実行、AppSync Eventsでリアルタイム通知、DynamoDBで状態管理を行います。

### アーキテクチャの特徴

- **フルマネージド**: インフラ管理が不要、スケーリングも自動
- **従量課金**: 実行した分だけの課金で、アイドル時のコストが低い
- **高い耐障害性**: AWSのマネージドサービスによるSLA保証
- **リアルタイム通知**: AppSync EventsによるWebSocket通信でフロントエンドにプッシュ通知

### 採用基準

#### この構成を選ぶべきケース

- サーバーレスアーキテクチャを採用している
- インフラ管理の負担を最小化したい
- 負荷の変動が大きく、オートスケーリングが必要
- ジョブの実行頻度が不定期で、アイドル時のコストを抑えたい
- AWSに集約したインフラ構成を維持したい

#### 他の選択肢を検討すべきケース

- 処理時間が15分を超える場合 → Step Functions + ECS/Fargate
- 低レイテンシが必要な場合 → BullMQ/Sidekiq
- 複雑なジョブ依存関係がある場合 → Step Functions
- マルチクラウド/ベンダーロックイン回避が必要 → BullMQ

## アーキテクチャ

### 全体構成

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  API Gateway │────▶│    Lambda    │────▶│     SQS      │
│  (REST/HTTP) │     │  (Producer)  │     │   (Queue)    │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client     │◀────│   AppSync    │◀────│    Lambda    │
│  (Frontend)  │ WS  │   Events     │     │   (Worker)   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   DynamoDB   │
                                          │ (状態管理)    │
                                          └──────────────┘
```

### コンポーネントの役割

- **API Gateway**: リクエストの受付、認証
- **Producer Lambda**: ジョブの登録、SQSへのメッセージ送信
- **SQS**: メッセージキュー、リトライ、DLQ
- **Worker Lambda**: SQSトリガーでジョブを処理
- **DynamoDB**: ジョブの状態管理、メタデータ保存
- **AppSync Events**: フロントエンドへのリアルタイム通知

## 実装サンプル

### プロジェクト構成

```
src/
├── functions/
│   ├── enqueue/           # ジョブ投入Lambda
│   │   └── handler.ts
│   ├── worker/            # ワーカーLambda
│   │   └── handler.ts
│   └── status/            # 状態確認Lambda
│       └── handler.ts
├── lib/
│   ├── dynamodb.ts        # DynamoDB操作
│   ├── sqs.ts             # SQS操作
│   └── appsync.ts         # AppSync操作
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
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface EnqueueRequest {
  type: string;
  payload: Record<string, unknown>;
}

export interface JobStatusEvent {
  jobId: string;
  status: Job['status'];
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}
```

### DynamoDB操作

```typescript
// src/lib/dynamodb.ts
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import {
  DynamoDBDocumentClient,
  PutCommand,
  GetCommand,
  UpdateCommand,
} from '@aws-sdk/lib-dynamodb';
import { Job } from '../types/job';

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);
const TABLE_NAME = process.env.JOBS_TABLE_NAME!;

export const createJob = async (job: Job): Promise<void> => {
  await docClient.send(
    new PutCommand({
      TableName: TABLE_NAME,
      Item: job,
    })
  );
};

export const getJob = async (jobId: string): Promise<Job | null> => {
  const result = await docClient.send(
    new GetCommand({
      TableName: TABLE_NAME,
      Key: { jobId },
    })
  );
  return (result.Item as Job) || null;
};

export const updateJobStatus = async (
  jobId: string,
  status: Job['status'],
  updates?: Partial<Pick<Job, 'result' | 'error' | 'completedAt'>>
): Promise<void> => {
  const updateExpressions: string[] = [
    '#status = :status',
    'updatedAt = :updatedAt',
  ];
  const expressionAttributeNames: Record<string, string> = {
    '#status': 'status',
  };
  const expressionAttributeValues: Record<string, unknown> = {
    ':status': status,
    ':updatedAt': new Date().toISOString(),
  };

  if (updates?.result) {
    updateExpressions.push('#result = :result');
    expressionAttributeNames['#result'] = 'result';
    expressionAttributeValues[':result'] = updates.result;
  }

  if (updates?.error) {
    updateExpressions.push('#error = :error');
    expressionAttributeNames['#error'] = 'error';
    expressionAttributeValues[':error'] = updates.error;
  }

  if (updates?.completedAt) {
    updateExpressions.push('completedAt = :completedAt');
    expressionAttributeValues[':completedAt'] = updates.completedAt;
  }

  await docClient.send(
    new UpdateCommand({
      TableName: TABLE_NAME,
      Key: { jobId },
      UpdateExpression: `SET ${updateExpressions.join(', ')}`,
      ExpressionAttributeNames: expressionAttributeNames,
      ExpressionAttributeValues: expressionAttributeValues,
    })
  );
};
```

### SQS操作

```typescript
// src/lib/sqs.ts
import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';

const client = new SQSClient({});
const QUEUE_URL = process.env.QUEUE_URL!;

export interface QueueMessage {
  jobId: string;
  type: string;
  payload: Record<string, unknown>;
}

export const sendMessage = async (message: QueueMessage): Promise<void> => {
  await client.send(
    new SendMessageCommand({
      QueueUrl: QUEUE_URL,
      MessageBody: JSON.stringify(message),
      MessageAttributes: {
        jobType: {
          DataType: 'String',
          StringValue: message.type,
        },
      },
    })
  );
};
```

### AppSync Events操作

```typescript
// src/lib/appsync.ts
import { SignatureV4 } from '@smithy/signature-v4';
import { Sha256 } from '@aws-crypto/sha256-js';
import { defaultProvider } from '@aws-sdk/credential-provider-node';
import { HttpRequest } from '@smithy/protocol-http';
import { JobStatusEvent } from '../types/job';

const APPSYNC_ENDPOINT = process.env.APPSYNC_HTTP_ENDPOINT!;
const APPSYNC_REGION = process.env.AWS_REGION!;

export const publishJobStatus = async (event: JobStatusEvent): Promise<void> => {
  const url = new URL(APPSYNC_ENDPOINT);

  const request = new HttpRequest({
    method: 'POST',
    hostname: url.hostname,
    path: url.pathname,
    headers: {
      'Content-Type': 'application/json',
      host: url.hostname,
    },
    body: JSON.stringify({
      channel: `job/${event.jobId}`,
      events: [JSON.stringify(event)],
    }),
  });

  const signer = new SignatureV4({
    credentials: defaultProvider(),
    region: APPSYNC_REGION,
    service: 'appsync',
    sha256: Sha256,
  });

  const signedRequest = await signer.sign(request);

  const response = await fetch(APPSYNC_ENDPOINT, {
    method: signedRequest.method,
    headers: signedRequest.headers as HeadersInit,
    body: signedRequest.body,
  });

  if (!response.ok) {
    throw new Error(`Failed to publish event: ${response.statusText}`);
  }
};
```

### Producer Lambda

```typescript
// src/functions/enqueue/handler.ts
import { APIGatewayProxyHandler } from 'aws-lambda';
import { randomUUID } from 'crypto';
import { createJob } from '../../lib/dynamodb';
import { sendMessage } from '../../lib/sqs';
import { EnqueueRequest, Job } from '../../types/job';

export const handler: APIGatewayProxyHandler = async (event) => {
  try {
    const body: EnqueueRequest = JSON.parse(event.body || '{}');

    if (!body.type || !body.payload) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'type and payload are required' }),
      };
    }

    const jobId = randomUUID();
    const now = new Date().toISOString();

    const job: Job = {
      jobId,
      type: body.type,
      status: 'pending',
      payload: body.payload,
      createdAt: now,
      updatedAt: now,
    };

    // DynamoDBにジョブを作成
    await createJob(job);

    // SQSにメッセージを送信
    await sendMessage({
      jobId,
      type: body.type,
      payload: body.payload,
    });

    return {
      statusCode: 202,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jobId,
        status: 'pending',
      }),
    };
  } catch (error) {
    console.error('Error enqueueing job:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' }),
    };
  }
};
```

### Worker Lambda

```typescript
// src/functions/worker/handler.ts
import { SQSHandler, SQSRecord } from 'aws-lambda';
import { updateJobStatus, getJob } from '../../lib/dynamodb';
import { publishJobStatus } from '../../lib/appsync';
import { QueueMessage } from '../../lib/sqs';

// ジョブタイプごとの処理関数
const jobProcessors: Record<string, (payload: Record<string, unknown>) => Promise<Record<string, unknown>>> = {
  'send-email': async (payload) => {
    // メール送信ロジック
    const { to, subject, body } = payload as { to: string; subject: string; body: string };
    // 実際のメール送信処理...
    return { messageId: `msg-${Date.now()}`, sentAt: new Date().toISOString() };
  },
  'process-image': async (payload) => {
    // 画像処理ロジック
    const { imageUrl } = payload as { imageUrl: string };
    // 実際の画像処理...
    return { processedUrl: `${imageUrl}-processed` };
  },
};

const processRecord = async (record: SQSRecord): Promise<void> => {
  const message: QueueMessage = JSON.parse(record.body);
  const { jobId, type, payload } = message;

  console.log(`Processing job ${jobId} of type ${type}`);

  try {
    // 状態を processing に更新
    await updateJobStatus(jobId, 'processing');
    await publishJobStatus({ jobId, status: 'processing', progress: 0 });

    // ジョブタイプに応じた処理を実行
    const processor = jobProcessors[type];
    if (!processor) {
      throw new Error(`Unknown job type: ${type}`);
    }

    const result = await processor(payload);

    // 状態を completed に更新
    await updateJobStatus(jobId, 'completed', {
      result,
      completedAt: new Date().toISOString(),
    });
    await publishJobStatus({ jobId, status: 'completed', progress: 100, result });

    console.log(`Job ${jobId} completed successfully`);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`Job ${jobId} failed:`, errorMessage);

    // 状態を failed に更新
    await updateJobStatus(jobId, 'failed', { error: errorMessage });
    await publishJobStatus({ jobId, status: 'failed', error: errorMessage });

    // エラーを再スローしてSQSにリトライさせる
    throw error;
  }
};

export const handler: SQSHandler = async (event) => {
  const results = await Promise.allSettled(
    event.Records.map(processRecord)
  );

  // 失敗したレコードを報告（部分的なバッチ失敗）
  const failedRecords = results
    .map((result, index) => (result.status === 'rejected' ? event.Records[index] : null))
    .filter((record): record is SQSRecord => record !== null);

  if (failedRecords.length > 0) {
    return {
      batchItemFailures: failedRecords.map((record) => ({
        itemIdentifier: record.messageId,
      })),
    };
  }
};
```

### Status Lambda

```typescript
// src/functions/status/handler.ts
import { APIGatewayProxyHandler } from 'aws-lambda';
import { getJob } from '../../lib/dynamodb';

export const handler: APIGatewayProxyHandler = async (event) => {
  const jobId = event.pathParameters?.jobId;

  if (!jobId) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'jobId is required' }),
    };
  }

  const job = await getJob(jobId);

  if (!job) {
    return {
      statusCode: 404,
      body: JSON.stringify({ error: 'Job not found' }),
    };
  }

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(job),
  };
};
```

## Terraform

```hcl
# Variables
variable "environment" {
  default = "production"
}

variable "region" {
  default = "ap-northeast-1"
}

# DynamoDB Table
resource "aws_dynamodb_table" "jobs" {
  name         = "${var.environment}-async-jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "jobId"

  attribute {
    name = "jobId"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Environment = var.environment
  }
}

# SQS Queue
resource "aws_sqs_queue" "jobs" {
  name                       = "${var.environment}-async-jobs"
  visibility_timeout_seconds = 300  # Lambda timeout + buffer
  message_retention_seconds  = 1209600  # 14 days
  receive_wait_time_seconds  = 20  # Long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jobs_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Environment = var.environment
  }
}

# Dead Letter Queue
resource "aws_sqs_queue" "jobs_dlq" {
  name                      = "${var.environment}-async-jobs-dlq"
  message_retention_seconds = 1209600

  tags = {
    Environment = var.environment
  }
}

# AppSync Events API
# 注意: aws_appsync_api リソースは Event API 専用です（api_type パラメータは不要）
resource "aws_appsync_api" "events" {
  name = "${var.environment}-job-events"

  event_config {
    auth_provider {
      auth_type = "AWS_IAM"
    }
    connection_auth_mode {
      auth_type = "AWS_IAM"
    }
    default_publish_auth_mode {
      auth_type = "AWS_IAM"
    }
    default_subscribe_auth_mode {
      auth_type = "AWS_IAM"
    }
  }
}

resource "aws_appsync_channel_namespace" "jobs" {
  api_id = aws_appsync_api.events.id
  name   = "job"

  publish_auth_modes {
    auth_type = "AWS_IAM"
  }

  subscribe_auth_modes {
    auth_type = "AWS_IAM"
  }
}

# Lambda IAM Role
resource "aws_iam_role" "lambda" {
  name = "${var.environment}-async-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  name = "${var.environment}-async-lambda-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.jobs.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.jobs.arn
      },
      {
        Effect = "Allow"
        Action = [
          "appsync:EventPublish"
        ]
        Resource = "${aws_appsync_api.events.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda Functions
resource "aws_lambda_function" "enqueue" {
  function_name = "${var.environment}-async-enqueue"
  runtime       = "nodejs20.x"
  handler       = "handler.handler"
  role          = aws_iam_role.lambda.arn
  timeout       = 30
  memory_size   = 256

  filename         = "dist/enqueue.zip"
  source_code_hash = filebase64sha256("dist/enqueue.zip")

  environment {
    variables = {
      JOBS_TABLE_NAME       = aws_dynamodb_table.jobs.name
      QUEUE_URL             = aws_sqs_queue.jobs.url
      APPSYNC_HTTP_ENDPOINT = "https://${aws_appsync_api.events.id}.appsync-api.${var.region}.amazonaws.com/event"
    }
  }
}

resource "aws_lambda_function" "worker" {
  function_name = "${var.environment}-async-worker"
  runtime       = "nodejs20.x"
  handler       = "handler.handler"
  role          = aws_iam_role.lambda.arn
  timeout       = 300  # 5 minutes max
  memory_size   = 512

  filename         = "dist/worker.zip"
  source_code_hash = filebase64sha256("dist/worker.zip")

  environment {
    variables = {
      JOBS_TABLE_NAME       = aws_dynamodb_table.jobs.name
      APPSYNC_HTTP_ENDPOINT = "https://${aws_appsync_api.events.id}.appsync-api.${var.region}.amazonaws.com/event"
    }
  }
}

resource "aws_lambda_function" "status" {
  function_name = "${var.environment}-async-status"
  runtime       = "nodejs20.x"
  handler       = "handler.handler"
  role          = aws_iam_role.lambda.arn
  timeout       = 30
  memory_size   = 256

  filename         = "dist/status.zip"
  source_code_hash = filebase64sha256("dist/status.zip")

  environment {
    variables = {
      JOBS_TABLE_NAME = aws_dynamodb_table.jobs.name
    }
  }
}

# SQS Event Source Mapping
resource "aws_lambda_event_source_mapping" "worker_sqs" {
  event_source_arn                   = aws_sqs_queue.jobs.arn
  function_name                      = aws_lambda_function.worker.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  function_response_types            = ["ReportBatchItemFailures"]
}

# API Gateway
resource "aws_apigatewayv2_api" "api" {
  name          = "${var.environment}-async-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "api" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "enqueue" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.enqueue.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "status" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.status.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "enqueue" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /jobs"
  target    = "integrations/${aws_apigatewayv2_integration.enqueue.id}"
}

resource "aws_apigatewayv2_route" "status" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /jobs/{jobId}"
  target    = "integrations/${aws_apigatewayv2_integration.status.id}"
}

resource "aws_lambda_permission" "enqueue" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.enqueue.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "status" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.status.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# Outputs
output "api_endpoint" {
  value = aws_apigatewayv2_api.api.api_endpoint
}

output "appsync_realtime_endpoint" {
  value = aws_appsync_api.events.realtime_uris["REALTIME"]
}

output "appsync_http_endpoint" {
  value = "https://${aws_appsync_api.events.id}.appsync-api.${var.region}.amazonaws.com/event"
}
```

## フロントエンド連携（AppSync Events）

```typescript
// frontend/src/lib/jobSubscription.ts
import { Amplify } from 'aws-amplify';
import { events } from 'aws-amplify/data';

// Amplify設定
Amplify.configure({
  API: {
    Events: {
      endpoint: process.env.NEXT_PUBLIC_APPSYNC_ENDPOINT!,
      region: process.env.NEXT_PUBLIC_AWS_REGION!,
      defaultAuthMode: 'iam',
    },
  },
});

interface JobStatusEvent {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

export const subscribeToJobStatus = (
  jobId: string,
  onStatusChange: (event: JobStatusEvent) => void
) => {
  const channel = events.connect(`job/${jobId}`);

  channel.subscribe({
    next: (event) => {
      const data = JSON.parse(event.data as string) as JobStatusEvent;
      onStatusChange(data);
    },
    error: (error) => {
      console.error('Subscription error:', error);
    },
  });

  return () => {
    channel.close();
  };
};
```

### React Hook

```typescript
// frontend/src/hooks/useJobStatus.ts
import { useState, useEffect, useCallback } from 'react';
import { subscribeToJobStatus } from '../lib/jobSubscription';

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

export const useJobStatus = (jobId: string | null) => {
  const [status, setStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const unsubscribe = subscribeToJobStatus(jobId, (event) => {
      setStatus({
        status: event.status,
        progress: event.progress,
        result: event.result,
        error: event.error,
      });
    });

    return unsubscribe;
  }, [jobId]);

  return status;
};
```

## 監視とアラート

```hcl
# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.environment}-async-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "DLQ has messages - jobs are failing"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = aws_sqs_queue.jobs_dlq.name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.environment}-worker-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Worker Lambda is having errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.worker.function_name
  }
}
```

## 制限事項と注意点

### Lambda制限

- **最大実行時間**: 15分（長時間処理にはStep Functionsを検討）
- **メモリ**: 最大10GB
- **同時実行数**: デフォルト1000（引き上げ可能）

### SQS制限

- **メッセージサイズ**: 最大1MiB（2025年8月にAWSにより256KBから1MiBに拡張されました。大きなデータはS3に保存してURLを渡すことを推奨）
- **メッセージ保持期間**: 最大14日

### DynamoDB制限

- **アイテムサイズ**: 最大400KB（属性名と値の合計）
- **書き込みスループット**: オンデマンドモードでは自動スケーリング

### コスト最適化

- Lambda: メモリと実行時間を最適化
- DynamoDB: TTLでデータを自動削除
- SQS: Long pollingで無駄なポーリングを削減
