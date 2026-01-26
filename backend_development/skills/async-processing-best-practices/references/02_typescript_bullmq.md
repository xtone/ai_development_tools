---
title: TypeScript BullMQによる実装
---

## TypeScript BullMQによる実装

非同期処理をTypeScript/Node.jsで実装する場合は、BullMQを採用します。BullMQはRedisをバックエンドとした高性能なジョブキューライブラリで、堅牢なリトライ機能、優先度付きキュー、レート制限など豊富な機能を提供します。

### BullMQの特徴

- **高いパフォーマンス**: Redisベースで秒間数千ジョブの処理が可能
- **型安全**: TypeScriptファーストで設計されており、ジョブのペイロードやリターン値の型定義が可能
- **豊富な機能**: 遅延ジョブ、繰り返しジョブ、優先度付きキュー、レート制限
- **可観測性**: Bull Boardなどの管理UIが利用可能
- **スケーラビリティ**: ワーカーを水平スケールして負荷分散が可能

### 採用基準

#### BullMQ を選ぶべきケース

- Node.js/TypeScriptでバックエンドを構築している
- Redisを既に利用している、または導入に抵抗がない
- 複雑なジョブフロー（依存関係、子ジョブ）が必要
- 秒間数百〜数千ジョブの高スループットが求められる
- ジョブの優先度制御やレート制限が必要

#### 他の選択肢を検討すべきケース

- サーバーレス環境でコールドスタートを避けたい場合 → AWS SQS + Lambda
- Redisの運用を避けたい場合 → Cloud Tasks/SQS
- シンプルなバッチ処理のみの場合 → シンプルなcronジョブ

## アーキテクチャ

### 基本構成

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  API Server │────▶│    Redis    │◀────│   Worker    │
│  (Producer) │     │  (Queue)    │     │  (Consumer) │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       │         ┌─────────────┐              │
       └────────▶│  Database   │◀─────────────┘
                 │ (状態管理)   │
                 └─────────────┘
```

### コンポーネント

- **Producer**: APIサーバーがジョブをキューに投入
- **Queue**: Redisがジョブの永続化と配信を担当
- **Worker**: 別プロセス/コンテナでジョブを処理
- **Database**: ジョブの状態やビジネスデータを永続化

## インフラ構成

### AWS構成

- **API Server**: ECS Fargate または App Runner
- **Worker**: ECS Fargate（別タスク定義）
- **Redis**: ElastiCache for Redis または MemoryDB for Redis
- **Database**: RDS PostgreSQL または Aurora

### Google Cloud構成

- **API Server**: Cloud Run
- **Worker**: Cloud Run Jobs または Compute Engine
- **Redis**: Memorystore for Redis
- **Database**: Cloud SQL

## 実装サンプル

### パッケージインストール

```bash
# ioredis v5+はTypeScript型定義を内蔵しているため、@types/ioredisは不要
npm install bullmq ioredis
```

### キューの定義

```typescript
// src/queues/types.ts
export interface EmailJobData {
  to: string;
  subject: string;
  body: string;
  templateId?: string;
}

export interface EmailJobResult {
  messageId: string;
  sentAt: Date;
}

export const EMAIL_QUEUE_NAME = 'email-queue';
```

```typescript
// src/queues/connection.ts
import { Redis } from 'ioredis';

const redisConfig = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  maxRetriesPerRequest: null, // BullMQの要件
};

export const createRedisConnection = () => new Redis(redisConfig);
```

### Producer（ジョブ投入側）

```typescript
// src/queues/emailQueue.ts
import { Queue } from 'bullmq';
import { createRedisConnection } from './connection';
import { EmailJobData, EmailJobResult, EMAIL_QUEUE_NAME } from './types';

export const emailQueue = new Queue<EmailJobData, EmailJobResult>(
  EMAIL_QUEUE_NAME,
  {
    connection: createRedisConnection(),
    defaultJobOptions: {
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 1000,
      },
      removeOnComplete: {
        age: 24 * 3600, // 24時間後に完了ジョブを削除
        count: 1000,    // 最大1000件保持
      },
      removeOnFail: {
        age: 7 * 24 * 3600, // 7日後に失敗ジョブを削除
      },
    },
  }
);

// ジョブ投入ヘルパー
export const enqueueEmail = async (data: EmailJobData, options?: {
  delay?: number;
  priority?: number;
}) => {
  const job = await emailQueue.add('send-email', data, {
    delay: options?.delay,
    priority: options?.priority,
  });
  return job.id;
};
```

### Worker（ジョブ処理側）

```typescript
// src/workers/emailWorker.ts
import { Worker, Job } from 'bullmq';
import { createRedisConnection } from '../queues/connection';
import { EmailJobData, EmailJobResult, EMAIL_QUEUE_NAME } from '../queues/types';
import { sendEmail } from '../services/emailService';
import { logger } from '../utils/logger';

const processEmail = async (
  job: Job<EmailJobData, EmailJobResult>
): Promise<EmailJobResult> => {
  const { to, subject, body, templateId } = job.data;

  logger.info(`Processing email job ${job.id}`, { to, subject });

  // 進捗更新
  await job.updateProgress(10);

  try {
    const result = await sendEmail({ to, subject, body, templateId });

    await job.updateProgress(100);

    return {
      messageId: result.messageId,
      sentAt: new Date(),
    };
  } catch (error) {
    logger.error(`Failed to send email`, { jobId: job.id, error });
    throw error; // リトライのために再スロー
  }
};

export const createEmailWorker = () => {
  const worker = new Worker<EmailJobData, EmailJobResult>(
    EMAIL_QUEUE_NAME,
    processEmail,
    {
      connection: createRedisConnection(),
      concurrency: 10, // 同時処理数
      limiter: {
        max: 100,      // 最大100ジョブ
        duration: 1000, // 1秒あたり
      },
    }
  );

  worker.on('completed', (job, result) => {
    logger.info(`Job ${job.id} completed`, { result });
  });

  worker.on('failed', (job, error) => {
    logger.error(`Job ${job?.id} failed`, { error: error.message });
  });

  worker.on('error', (error) => {
    logger.error('Worker error', { error });
  });

  return worker;
};
```

### ワーカーの起動スクリプト

```typescript
// src/worker.ts
import { createEmailWorker } from './workers/emailWorker';
import { logger } from './utils/logger';

const workers = [
  createEmailWorker(),
];

// Graceful shutdown
const shutdown = async () => {
  logger.info('Shutting down workers...');
  await Promise.all(workers.map(w => w.close()));
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

logger.info('Workers started');
```

### APIエンドポイント例

```typescript
// src/routes/email.ts
import { Router } from 'express';
import { enqueueEmail } from '../queues/emailQueue';
import { emailQueue } from '../queues/emailQueue';

const router = Router();

// メール送信リクエスト
router.post('/send', async (req, res) => {
  const { to, subject, body } = req.body;

  const jobId = await enqueueEmail({ to, subject, body });

  res.status(202).json({
    status: 'queued',
    jobId,
  });
});

// ジョブ状態確認
router.get('/status/:jobId', async (req, res) => {
  const job = await emailQueue.getJob(req.params.jobId);

  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }

  const state = await job.getState();
  const progress = job.progress;

  res.json({
    jobId: job.id,
    state,
    progress,
    data: job.data,
    result: job.returnvalue,
    failedReason: job.failedReason,
  });
});

export default router;
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

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### ワーカー用起動コマンド

```bash
# ワーカーとして起動する場合
CMD ["node", "dist/worker.js"]
```

## AWS: Terraform (ECS Fargate)

```hcl
# Variables
variable "environment" {
  default = "production"
}

variable "redis_node_type" {
  default = "cache.t3.micro"
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.environment}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.environment}-bullmq-redis"
  description                = "Redis for BullMQ"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 2
  port                       = 6379
  parameter_group_name       = "default.redis7"
  automatic_failover_enabled = true
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

# Security Group for Redis
resource "aws_security_group" "redis" {
  name        = "${var.environment}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

# ECS Task Definition (API)
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.environment}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "api"
    image = "${aws_ecr_repository.app.repository_url}:latest"

    portMappings = [{ containerPort = 3000 }]

    environment = [
      { name = "NODE_ENV", value = "production" },
      { name = "REDIS_HOST", value = aws_elasticache_replication_group.redis.primary_endpoint_address },
      { name = "REDIS_PORT", value = "6379" },
      { name = "DATABASE_URL", value = "postgres://..." }
    ]

    command = ["node", "dist/server.js"]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.environment}/api"
        "awslogs-region"        = "ap-northeast-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

# ECS Task Definition (Worker)
resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.environment}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "worker"
    image = "${aws_ecr_repository.app.repository_url}:latest"

    environment = [
      { name = "NODE_ENV", value = "production" },
      { name = "REDIS_HOST", value = aws_elasticache_replication_group.redis.primary_endpoint_address },
      { name = "REDIS_PORT", value = "6379" },
      { name = "DATABASE_URL", value = "postgres://..." }
    ]

    command = ["node", "dist/worker.js"]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.environment}/worker"
        "awslogs-region"        = "ap-northeast-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ECS Service (API)
resource "aws_ecs_service" "api" {
  name            = "api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 3000
  }
}

# ECS Service (Worker)
resource "aws_ecs_service" "worker" {
  name            = "worker-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
  }
}

# Auto Scaling for Worker
resource "aws_appautoscaling_target" "worker" {
  max_capacity       = 10
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "worker_cpu" {
  name               = "worker-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker.resource_id
  scalable_dimension = aws_appautoscaling_target.worker.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

## Google Cloud: Terraform (Cloud Run)

```hcl
# Variables
variable "project_id" {
  description = "GCP Project ID"
}

variable "region" {
  default = "asia-northeast1"
}

# Memorystore Redis
resource "google_redis_instance" "bullmq" {
  name           = "bullmq-redis"
  tier           = "STANDARD_HA"
  memory_size_gb = 1
  region         = var.region

  authorized_network = google_compute_network.main.id

  redis_version = "REDIS_7_0"
  display_name  = "BullMQ Redis Instance"

  transit_encryption_mode = "SERVER_AUTHENTICATION"
}

# Cloud Run Service (API)
resource "google_cloud_run_v2_service" "api" {
  name     = "api"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/app/api:latest"

      env {
        name  = "NODE_ENV"
        value = "production"
      }
      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.bullmq.host
      }
      env {
        name  = "REDIS_PORT"
        value = tostring(google_redis_instance.bullmq.port)
      }

      ports {
        container_port = 3000
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
          port = 3000
        }
        initial_delay_seconds = 10
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 3000
        }
        period_seconds = 30
      }
    }

    vpc_access {
      network_interfaces {
        network    = google_compute_network.main.name
        subnetwork = google_compute_subnetwork.main.name
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# Cloud Run Service (Worker)
resource "google_cloud_run_v2_service" "worker" {
  name     = "worker"
  location = var.region

  template {
    containers {
      image   = "${var.region}-docker.pkg.dev/${var.project_id}/app/api:latest"
      command = ["node", "dist/worker.js"]

      env {
        name  = "NODE_ENV"
        value = "production"
      }
      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.bullmq.host
      }
      env {
        name  = "REDIS_PORT"
        value = tostring(google_redis_instance.bullmq.port)
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = false # ワーカーは常時起動
      }
    }

    vpc_access {
      network_interfaces {
        network    = google_compute_network.main.name
        subnetwork = google_compute_subnetwork.main.name
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = 1 # ワーカーは常時1台以上
      max_instance_count = 5
    }
  }

  # ワーカーは外部からのアクセス不要
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"
}

# IAM for Cloud Run
resource "google_cloud_run_service_iam_member" "api_invoker" {
  location = google_cloud_run_v2_service.api.location
  service  = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

## Bull Board（管理UI）の追加

```typescript
// src/admin/bullBoard.ts
import { createBullBoard } from '@bull-board/api';
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter';
import { ExpressAdapter } from '@bull-board/express';
import { emailQueue } from '../queues/emailQueue';

export const setupBullBoard = (app: Express) => {
  const serverAdapter = new ExpressAdapter();
  serverAdapter.setBasePath('/admin/queues');

  createBullBoard({
    queues: [new BullMQAdapter(emailQueue)],
    serverAdapter,
  });

  // Basic認証などで保護することを推奨
  app.use('/admin/queues', serverAdapter.getRouter());
};
```

## フロントエンドへの状態通知（Socket.io）

非同期ジョブの進捗や完了状態をフロントエンドにリアルタイムで通知するには、Socket.ioを使用します。

### パッケージインストール

```bash
npm install socket.io
npm install -D @types/socket.io
```

### Socket.ioサーバーの設定

```typescript
// src/socket/server.ts
import { Server as HttpServer } from 'http';
import { Server, Socket } from 'socket.io';
import { logger } from '../utils/logger';

let io: Server;

export const initSocketServer = (httpServer: HttpServer): Server => {
  io = new Server(httpServer, {
    cors: {
      origin: process.env.FRONTEND_URL || 'http://localhost:3000',
      methods: ['GET', 'POST'],
    },
    path: '/socket.io',
  });

  io.on('connection', (socket: Socket) => {
    logger.info(`Client connected: ${socket.id}`);

    // ジョブ状態のサブスクリプション
    socket.on('subscribe:job', (jobId: string) => {
      socket.join(`job:${jobId}`);
      logger.info(`Socket ${socket.id} subscribed to job:${jobId}`);
    });

    socket.on('unsubscribe:job', (jobId: string) => {
      socket.leave(`job:${jobId}`);
      logger.info(`Socket ${socket.id} unsubscribed from job:${jobId}`);
    });

    socket.on('disconnect', () => {
      logger.info(`Client disconnected: ${socket.id}`);
    });
  });

  return io;
};

export const getSocketServer = (): Server => {
  if (!io) {
    throw new Error('Socket.io server not initialized');
  }
  return io;
};
```

### ジョブ状態の通知ヘルパー

```typescript
// src/socket/jobNotifier.ts
import { getSocketServer } from './server';

export interface JobStatusEvent {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
  updatedAt: string;
}

export const notifyJobStatus = (event: JobStatusEvent): void => {
  const io = getSocketServer();
  io.to(`job:${event.jobId}`).emit('job:status', event);
};
```

### Worker での通知

```typescript
// src/workers/emailWorker.ts
import { Worker, Job } from 'bullmq';
import { createRedisConnection } from '../queues/connection';
import { EmailJobData, EmailJobResult, EMAIL_QUEUE_NAME } from '../queues/types';
import { notifyJobStatus } from '../socket/jobNotifier';
import { sendEmail } from '../services/emailService';
import { logger } from '../utils/logger';

const processEmail = async (
  job: Job<EmailJobData, EmailJobResult>
): Promise<EmailJobResult> => {
  const { to, subject, body, templateId } = job.data;

  logger.info(`Processing email job ${job.id}`, { to, subject });

  // 処理開始を通知
  notifyJobStatus({
    jobId: job.id!,
    status: 'processing',
    progress: 0,
    updatedAt: new Date().toISOString(),
  });

  try {
    // 進捗更新
    await job.updateProgress(10);
    notifyJobStatus({
      jobId: job.id!,
      status: 'processing',
      progress: 10,
      updatedAt: new Date().toISOString(),
    });

    const result = await sendEmail({ to, subject, body, templateId });

    await job.updateProgress(100);

    const jobResult = {
      messageId: result.messageId,
      sentAt: new Date(),
    };

    // 完了を通知
    notifyJobStatus({
      jobId: job.id!,
      status: 'completed',
      progress: 100,
      result: jobResult,
      updatedAt: new Date().toISOString(),
    });

    return jobResult;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    logger.error(`Failed to send email`, { jobId: job.id, error });

    // エラーを通知
    notifyJobStatus({
      jobId: job.id!,
      status: 'failed',
      error: errorMessage,
      updatedAt: new Date().toISOString(),
    });

    throw error;
  }
};

export const createEmailWorker = () => {
  const worker = new Worker<EmailJobData, EmailJobResult>(
    EMAIL_QUEUE_NAME,
    processEmail,
    {
      connection: createRedisConnection(),
      concurrency: 10,
    }
  );

  return worker;
};
```

### Express サーバーへの統合

```typescript
// src/server.ts
import express from 'express';
import { createServer } from 'http';
import { initSocketServer } from './socket/server';

const app = express();
const httpServer = createServer(app);

// Socket.io初期化
initSocketServer(httpServer);

// ... 既存のルート設定 ...

const PORT = process.env.PORT || 3000;
httpServer.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
```

### フロントエンド（React）

```typescript
// frontend/src/lib/socket.ts
import { io, Socket } from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

let socket: Socket | null = null;

export const getSocket = (): Socket => {
  if (!socket) {
    socket = io(SOCKET_URL, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
    });
  }
  return socket;
};

export const disconnectSocket = (): void => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};
```

### React Hook

```typescript
// frontend/src/hooks/useJobStatus.ts
import { useState, useEffect, useCallback } from 'react';
import { getSocket } from '../lib/socket';

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

    const socket = getSocket();

    // ジョブにサブスクライブ
    socket.emit('subscribe:job', jobId);

    // 状態更新を受信
    const handleStatus = (event: JobStatus & { jobId: string }) => {
      if (event.jobId === jobId) {
        setStatus({
          status: event.status,
          progress: event.progress,
          result: event.result,
          error: event.error,
        });
      }
    };

    socket.on('job:status', handleStatus);

    return () => {
      socket.emit('unsubscribe:job', jobId);
      socket.off('job:status', handleStatus);
    };
  }, [jobId]);

  return status;
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
  const status = useJobStatus(jobId);

  useEffect(() => {
    if (status?.status === 'completed' && status.result) {
      onComplete?.(status.result);
    }
    if (status?.status === 'failed' && status.error) {
      onError?.(status.error);
    }
  }, [status, onComplete, onError]);

  if (!status) {
    return <div>接続中...</div>;
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

### Server-Sent Events（SSE）による代替実装

Socket.ioより軽量なSSEを使用する場合の実装例です。

```typescript
// src/routes/sse.ts
import { Router, Request, Response } from 'express';
import { emailQueue } from '../queues/emailQueue';
import { QueueEvents } from 'bullmq';
import { createRedisConnection } from '../queues/connection';

const router = Router();

// SSEエンドポイント
router.get('/jobs/:jobId/stream', async (req: Request, res: Response) => {
  const { jobId } = req.params;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no'); // nginx用

  const queueEvents = new QueueEvents(emailQueue.name, {
    connection: createRedisConnection(),
  });

  const sendEvent = (data: object) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  // 進捗イベント
  queueEvents.on('progress', ({ jobId: eventJobId, data }) => {
    if (eventJobId === jobId) {
      sendEvent({ type: 'progress', progress: data });
    }
  });

  // 完了イベント
  queueEvents.on('completed', ({ jobId: eventJobId, returnvalue }) => {
    if (eventJobId === jobId) {
      sendEvent({ type: 'completed', result: returnvalue });
      cleanup();
    }
  });

  // 失敗イベント
  queueEvents.on('failed', ({ jobId: eventJobId, failedReason }) => {
    if (eventJobId === jobId) {
      sendEvent({ type: 'failed', error: failedReason });
      cleanup();
    }
  });

  const cleanup = () => {
    queueEvents.close();
    res.end();
  };

  // クライアント切断時のクリーンアップ
  req.on('close', cleanup);
});

export default router;
```

```typescript
// frontend/src/hooks/useJobStatusSSE.ts
import { useState, useEffect } from 'react';

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

export const useJobStatusSSE = (jobId: string | null) => {
  const [status, setStatus] = useState<JobStatus>({ status: 'pending' });

  useEffect(() => {
    if (!jobId) return;

    const eventSource = new EventSource(
      `${process.env.NEXT_PUBLIC_API_URL}/jobs/${jobId}/stream`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'progress':
          setStatus((prev) => ({
            ...prev,
            status: 'processing',
            progress: data.progress,
          }));
          break;
        case 'completed':
          setStatus({
            status: 'completed',
            progress: 100,
            result: data.result,
          });
          eventSource.close();
          break;
        case 'failed':
          setStatus({
            status: 'failed',
            error: data.error,
          });
          eventSource.close();
          break;
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  return status;
};
```

### インフラ設定の注意点

#### AWS (ALB + ECS)

WebSocket/SSE接続を維持するため、ALBのアイドルタイムアウトを設定します。

```hcl
resource "aws_lb" "api" {
  # ... 既存の設定 ...

  # WebSocket/SSE用にアイドルタイムアウトを延長
  idle_timeout = 3600
}

resource "aws_lb_target_group" "api" {
  # ... 既存の設定 ...

  # スティッキーセッション（Socket.io polling fallback用）
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }
}
```

#### Google Cloud (Cloud Run)

Cloud RunではWebSocket接続は最大60分まで維持されます。

```hcl
resource "google_cloud_run_v2_service" "api" {
  template {
    # ... 既存の設定 ...

    # セッションアフィニティを有効化
    session_affinity = true
  }
}
```

## 監視とアラート

### CloudWatch メトリクス（AWS）

```hcl
resource "aws_cloudwatch_metric_alarm" "worker_cpu_high" {
  alarm_name          = "worker-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Worker CPU utilization is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.worker.name
  }
}
```

### アプリケーションメトリクス

```typescript
// src/metrics/queueMetrics.ts
import { emailQueue } from '../queues/emailQueue';

export const getQueueMetrics = async () => {
  const [waiting, active, completed, failed, delayed] = await Promise.all([
    emailQueue.getWaitingCount(),
    emailQueue.getActiveCount(),
    emailQueue.getCompletedCount(),
    emailQueue.getFailedCount(),
    emailQueue.getDelayedCount(),
  ]);

  return {
    waiting,
    active,
    completed,
    failed,
    delayed,
  };
};
```
