---
title: Ruby on Railsによる実装
---

## Ruby on Railsによる実装

非同期処理をRuby on Railsで利用する場合は以下のようなフレームワークおよびインフラ構成を採用します。

### ActiveJob + Solid Queue

アプリケーションのデータベースとして既にSqlite3、MySQLもしくはPostgreSQLが採用されていて、ユーザーのリクエスト数がそこまで多くなくデータベースのリソースに余裕がある状況なら、追加のリソースが必要ないSolidQueueを利用して実現します。
メリットとしてキューの管理やワーカーの実行のために新しくインフラを用意する必要がなく、既に利用しているRDBやpumaをそのまま利用することが出来ます。
RDBは既存のものを利用しつつ、ワーカーの実行のみWebと切り離すことも可能です。

### ActiveJob + Sidekiq

データベースのリソースに余裕がなかったり、アクセス数が多くて既存のインフラと分離して非同期処理を実現したい場合はSidekiqを利用して実現します。
キュー用のDBとしてはRedisを利用し、Sidekiq用にワーカープロセスを実行する環境を既存のRailsアプリケーション実行環境とは別に用意する必要があります。

## Solid QueueとSidekiqの採用基準

### Solid Queue を選ぶべきケース

- Rails 8以上で新規開発を始める
- インフラ構成をシンプルに保ちたい（Redisを管理したくない）
- ジョブの実行をDBトランザクションと同期させたい（例：ユーザー作成に失敗したら、歓迎メール送信ジョブも自動でキャンセルしたい）
- 数百万件/日 程度の一般的な負荷である

### Sidekiq を選ぶべきケース

- 既に Sidekiq Pro/Enterprise を契約している、またはその機能が必須である
- 既にキャッシュ用途などで Redis を運用しており、導入コストが低い
- 秒間数千件以上のジョブが走る、極めて高いスループットが求められる
- Sidekiq のリッチな Web UI や、長年のコミュニティ知見に頼りたい

## Solid Queueの実行環境の採用基準

### Webと統合する(pumaプラグインを利用)べきケース

- インフラのランニングコストや管理コストを抑えたい
- ジョブの負荷が低く、CPUを長時間占有しないジョブが中心
  - メール送信、簡易的なデータ更新など。重い画像処理や機械学習の推論、大量のデータ処理などをこの方式で行うとWebサイトのレスポンスが極端に遅くなったりタイムアウトするリスクがあります。

### Webと分離するべきケース

- ジョブの負荷が高かったり、処理時間が長いことが見込まれている
- Web側のリクエスト数が多く、Web側のサービスに影響が出ることを避けたい
- Web側とジョブ側でCPUやメモリの消費量が大きく異なることが想定される場合

## インフラ構成

AWSおよびGoogle Cloudにホスティングする場合は以下のような構成で実現します。

- AWS
  - ワーカー: Fargateを利用
    - Web用とジョブ用のDocker imageはWeb用とWorker用で同一のものを利用
    - Solid Queueをpumaプラグインを利用する場合はWeb用のサービスにジョブを実行させる
    - ジョブ用のワーカーを別に設定する場合は、ジョブ用のタスク定義を設定し異なるサービスとして実行させる
  - キューDB
    - Solid Queueの場合はWeb用のRDB(RDS/Aurora)を利用する
    - Sidekiqの場合はElasticacheを利用してRedisもしくはValkeyを利用する
      - 既にRedisを利用している場合は相乗りを検討し、新規に作る場合はValkeyの採用を検討する
- Google Cloud
  - ワーカー: Cloud Runを利用
    - Web用とジョブ用のDocker imageはWeb用とWorker用で同一のものを利用
    - Solid Queueをpumaプラグインを利用する場合はWeb用のサービスにジョブを実行させる
      - min-instances: 1以上に設定しないとジョブが実行されない点に注意
    - ジョブ用のワーカーを別に設定する場合、Web用とは別のサービスを実行させる
      - この場合もmin-instances: 1以上に設定する必要がある
    - ワーカー用のサービスが停止したときのことを考慮する
      - ワーカー用のプロセスにSIGTERMが送られた際にGraceful Shutdownが正しく動くようにする必要がある
  - キューDB
    - Solid Queueの場合はWeb用のCloud SQLを利用する
    - Sidekiqの場合はCloud Memorystore for Redisを利用する

### Dockerfile

Rails 8のベストプラクティスに基づいた、軽量かつセキュアなDockerfileのサンプルです。事前にインストールするライブラリ(libpq-dev等)はGemfileに応じて調整してください。

```
# syntax = docker/dockerfile:1
ARG RUBY_VERSION=3.3.0
FROM ruby:$RUBY_VERSION-slim AS base

WORKDIR /rails
ENV RAILS_ENV="production" \
    BUNDLE_DEPLOYMENT="1" \
    BUNDLE_PATH="/usr/local/bundle" \
    BUNDLE_WITHOUT="development test"

# --- Build stage ---
FROM base AS build
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y build-essential git libpq-dev pkg-config
COPY Gemfile Gemfile.lock ./
RUN bundle install && \
    rm -rf ~/.bundle/ "${BUNDLE_PATH}"/ruby/*/cache "${BUNDLE_PATH}"/ruby/*/bundler/gems/*/.git
COPY . .
RUN bundle exec bootsnap precompile --gemfile app/ lib/
# Asset precompilation (SECRET_KEY_BASEはダミーでOK)
RUN SECRET_KEY_BASE_DUMMY=1 ./bin/rails assets:precompile

# --- Final stage ---
FROM base
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y curl libpq5 && \
    rm -rf /var/lib/apt/lists /var/cache/apt/archives
COPY --from=build /usr/local/bundle /usr/local/bundle
COPY --from=build /rails /rails

# 非特権ユーザーで実行
RUN useradd rails --create-home --shell /bin/bash && \
    chown -R rails:rails db log storage tmp
USER rails:rails

ENTRYPOINT ["/rails/bin/docker-entrypoint"]
EXPOSE 3000
CMD ["./bin/rails", "server"]
```

### AWS: Terraform (ECS Fargate)

WebとWorkerを同一イメージ、別サービスで定義する構成のサンプルです。

```
# ECS Task Definition (Shared)
resource "aws_ecs_task_definition" "app" {
  family                   = "rails-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "rails-container"
    image = "${aws_ecr_repository.app.repository_url}:latest"
    portMappings = [{ containerPort = 3000 }]
    environment = [
      { name = "DATABASE_URL", value = "postgres://..." },
      { name = "RAILS_ENV",    value = "production" },
      { name = "SOLID_QUEUE_IN_PUMA", value = "true" } # 統合型の場合
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/rails-app"
        "awslogs-region"        = "ap-northeast-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ECS Service (Web)
resource "aws_ecs_service" "web" {
  name            = "web-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "rails-container"
    container_port   = 3000
  }
}
```

### Google Cloud: Terraform (Cloud Run v2)

Direct VPC Egressを利用したモダンなCloud Run構成です。

```
# Cloud Run Service (Unified Web & Worker)
resource "google_cloud_run_v2_service" "app" {
  name     = "rails-app"
  location = "asia-northeast1"

  template {
    containers {
      image = "asia-northeast1-docker.pkg.dev/project/repo/image:latest"

      env {
        name  = "DATABASE_URL"
        value = "postgres://user:pass@10.x.x.x:5432/dbname"
      }
      env {
        name  = "SOLID_QUEUE_IN_PUMA"
        value = "true"
      }

      ports {
        container_port = 3000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }

    # Direct VPC Egress 設定
    vpc_access {
      network_interfaces {
        network    = "default"
        subnets    = "default"
      }
      egress = "ALL_TRAFFIC"
    }

    scaling {
      min_instance_count = 1 # Solid Queueのポーリングを維持するため
      max_instance_count = 10
    }
  }
}
```

## フロントエンドへの状態通知（ActionCable）

非同期ジョブの進捗や完了状態をフロントエンドにリアルタイムで通知するには、ActionCableを使用します。

### ActionCable Channel

```ruby
# app/channels/job_status_channel.rb
class JobStatusChannel < ApplicationCable::Channel
  def subscribed
    job_id = params[:job_id]
    stream_from "job_status_#{job_id}"
  end

  def unsubscribed
    # クリーンアップ処理（必要に応じて）
  end
end
```

### ジョブからの通知

```ruby
# app/jobs/example_job.rb
class ExampleJob < ApplicationJob
  queue_as :default

  def perform(job_record_id)
    job_record = JobRecord.find(job_record_id)

    # 処理開始を通知
    broadcast_status(job_record, 'processing', 0)

    # 実際の処理
    result = process_task(job_record) do |progress|
      broadcast_status(job_record, 'processing', progress)
    end

    # 完了を通知
    job_record.update!(status: 'completed', result: result)
    broadcast_status(job_record, 'completed', 100, result)
  rescue StandardError => e
    job_record.update!(status: 'failed', error_message: e.message)
    broadcast_status(job_record, 'failed', nil, nil, e.message)
    raise
  end

  private

  def broadcast_status(job_record, status, progress, result = nil, error = nil)
    ActionCable.server.broadcast(
      "job_status_#{job_record.id}",
      {
        job_id: job_record.id,
        status: status,
        progress: progress,
        result: result,
        error: error,
        updated_at: Time.current.iso8601
      }
    )
  end

  def process_task(job_record)
    # 進捗を報告しながら処理を実行
    total_steps = 10
    total_steps.times do |i|
      # 実際の処理...
      sleep 1
      yield ((i + 1) * 100 / total_steps) if block_given?
    end
    { message: 'Task completed successfully' }
  end
end
```

### フロントエンド（JavaScript）

```javascript
// app/javascript/channels/job_status_channel.js
import consumer from "./consumer"

export function subscribeToJobStatus(jobId, callbacks) {
  return consumer.subscriptions.create(
    { channel: "JobStatusChannel", job_id: jobId },
    {
      received(data) {
        switch (data.status) {
          case 'processing':
            callbacks.onProgress?.(data.progress)
            break
          case 'completed':
            callbacks.onComplete?.(data.result)
            break
          case 'failed':
            callbacks.onError?.(data.error)
            break
        }
      },

      connected() {
        callbacks.onConnected?.()
      },

      disconnected() {
        callbacks.onDisconnected?.()
      }
    }
  )
}
```

### React Hook（Hotwire/Stimulus以外の場合）

```typescript
// frontend/src/hooks/useJobStatus.ts
import { useEffect, useState, useCallback } from 'react';
import { createConsumer } from '@rails/actioncable';

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

const consumer = createConsumer('/cable');

export function useJobStatus(jobId: string | null) {
  const [status, setStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const subscription = consumer.subscriptions.create(
      { channel: 'JobStatusChannel', job_id: jobId },
      {
        received(data: JobStatus) {
          setStatus(data);
        },
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [jobId]);

  return status;
}
```

### Hotwire/Turbo Streams（Rails 7+推奨）

```ruby
# app/jobs/example_job.rb（Turbo Streams版）
class ExampleJob < ApplicationJob
  def perform(job_record_id)
    job_record = JobRecord.find(job_record_id)

    job_record.update!(status: 'processing')
    broadcast_turbo_stream(job_record)

    # 処理実行...

    job_record.update!(status: 'completed', result: result)
    broadcast_turbo_stream(job_record)
  end

  private

  def broadcast_turbo_stream(job_record)
    Turbo::StreamsChannel.broadcast_replace_to(
      "job_#{job_record.id}",
      target: "job_status_#{job_record.id}",
      partial: "job_records/status",
      locals: { job_record: job_record }
    )
  end
end
```

```erb
<!-- app/views/job_records/_status.html.erb -->
<div id="job_status_<%= job_record.id %>">
  <p>Status: <%= job_record.status %></p>
  <% if job_record.processing? %>
    <progress value="<%= job_record.progress %>" max="100"></progress>
  <% end %>
  <% if job_record.completed? %>
    <p>Result: <%= job_record.result %></p>
  <% end %>
  <% if job_record.failed? %>
    <p class="error">Error: <%= job_record.error_message %></p>
  <% end %>
</div>
```

```erb
<!-- View側でのsubscribe -->
<%= turbo_stream_from "job_#{@job_record.id}" %>
<%= render 'job_records/status', job_record: @job_record %>
```

### インフラ設定の注意点

#### AWS (ALB + ECS)

ActionCableのWebSocket接続を維持するため、ALBのスティッキーセッションとアイドルタイムアウトを設定します。

```hcl
resource "aws_lb_target_group" "app" {
  # ... 既存の設定 ...

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }
}

resource "aws_lb_listener" "https" {
  # ... 既存の設定 ...

  # WebSocket用にアイドルタイムアウトを延長
  idle_timeout = 3600
}
```

#### Google Cloud (Cloud Run)

Cloud RunではWebSocket接続は最大60分まで維持されます。長時間のジョブには再接続ロジックを実装してください。

```hcl
resource "google_cloud_run_v2_service" "app" {
  template {
    # ... 既存の設定 ...

    # セッションアフィニティを有効化
    session_affinity = true
  }
}
```

## 外部フロントエンド（Next.js等）との連携

RailsをAPIサーバーとして使用し、フロントエンドをNext.js等で別途構築する場合のベストプラクティスです。

### 通知方法の選択

| 方法 | 特徴 | 推奨ケース |
|------|------|-----------|
| ActionCable（スタンドアロン） | Rails標準、双方向通信 | リアルタイム性が重要、双方向通信が必要 |
| Server-Sent Events（SSE） | シンプル、軽量、HTTP標準 | 単方向通知で十分、シンプルな実装を好む |
| ポーリング | 最もシンプル、インフラ制約なし | 更新頻度が低い、WebSocket非対応環境 |

### CORS設定

```ruby
# config/initializers/cors.rb
Rails.application.config.middleware.insert_before 0, Rack::Cors do
  allow do
    origins ENV.fetch('FRONTEND_URL', 'http://localhost:3000')

    resource '*',
      headers: :any,
      methods: [:get, :post, :put, :patch, :delete, :options, :head],
      credentials: true

    # ActionCable用のWebSocket接続を許可
    resource '/cable',
      headers: :any,
      methods: [:get, :post, :options],
      credentials: true
  end
end
```

### 認証（JWT）

外部フロントエンドとの連携では、セッションベースではなくJWT認証を使用することが一般的です。

```ruby
# Gemfile
gem 'jwt'
```

```ruby
# app/services/jwt_service.rb
class JwtService
  SECRET_KEY = Rails.application.credentials.secret_key_base

  def self.encode(payload, exp = 24.hours.from_now)
    payload[:exp] = exp.to_i
    JWT.encode(payload, SECRET_KEY, 'HS256')
  end

  def self.decode(token)
    decoded = JWT.decode(token, SECRET_KEY, true, algorithm: 'HS256')
    HashWithIndifferentAccess.new(decoded.first)
  rescue JWT::DecodeError, JWT::ExpiredSignature
    nil
  end
end
```

### ActionCable + JWT認証

```ruby
# app/channels/application_cable/connection.rb
module ApplicationCable
  class Connection < ActionCable::Connection::Base
    identified_by :current_user

    def connect
      self.current_user = find_verified_user
    end

    private

    def find_verified_user
      # クエリパラメータからトークンを取得
      token = request.params[:token]
      return reject_unauthorized_connection unless token

      payload = JwtService.decode(token)
      return reject_unauthorized_connection unless payload

      user = User.find_by(id: payload[:user_id])
      return reject_unauthorized_connection unless user

      user
    end
  end
end
```

```ruby
# config/initializers/action_cable.rb
Rails.application.config.action_cable.allowed_request_origins = [
  ENV.fetch('FRONTEND_URL', 'http://localhost:3000'),
  /https?:\/\/localhost:\d+/
]

# 本番環境ではURLを明示的に指定
if Rails.env.production?
  Rails.application.config.action_cable.allowed_request_origins = [
    ENV.fetch('FRONTEND_URL')
  ]
end
```

### Next.js フロントエンド実装（ActionCable）

```typescript
// lib/actionCable.ts
import { createConsumer, Consumer, Subscription } from '@rails/actioncable';

let consumer: Consumer | null = null;

export const getConsumer = (token: string): Consumer => {
  if (!consumer) {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/cable?token=${token}`;
    consumer = createConsumer(wsUrl);
  }
  return consumer;
};

export const disconnectConsumer = (): void => {
  if (consumer) {
    consumer.disconnect();
    consumer = null;
  }
};
```

```typescript
// hooks/useJobStatus.ts
import { useEffect, useState, useRef } from 'react';
import { getConsumer } from '../lib/actionCable';
import { Subscription } from '@rails/actioncable';
import { useAuth } from './useAuth'; // JWT認証フック

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

export const useJobStatus = (jobId: string | null) => {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const subscriptionRef = useRef<Subscription | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    if (!jobId || !token) return;

    const consumer = getConsumer(token);

    subscriptionRef.current = consumer.subscriptions.create(
      { channel: 'JobStatusChannel', job_id: jobId },
      {
        connected() {
          setConnected(true);
        },
        disconnected() {
          setConnected(false);
        },
        received(data: JobStatus) {
          setStatus(data);
        },
      }
    );

    return () => {
      subscriptionRef.current?.unsubscribe();
      subscriptionRef.current = null;
    };
  }, [jobId, token]);

  return { status, connected };
};
```

### Server-Sent Events（SSE）による実装

ActionCableより軽量なSSEを使用する場合の実装です。

```ruby
# app/controllers/api/v1/job_streams_controller.rb
module Api
  module V1
    class JobStreamsController < ApplicationController
      include ActionController::Live

      before_action :authenticate_user!
      before_action :set_job

      def show
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Accel-Buffering'] = 'no' # nginx用

        sse = SSE.new(response.stream, retry: 3000, event: 'job-status')

        begin
          # 初期状態を送信
          sse.write(job_status_data)

          # Redis Pub/Subで更新を購読
          redis = Redis.new(url: ENV['REDIS_URL'])
          redis.subscribe("job_status_#{@job.id}") do |on|
            on.message do |_channel, message|
              data = JSON.parse(message)
              sse.write(data)

              # 完了または失敗で終了
              break if %w[completed failed].include?(data['status'])
            end
          end
        rescue ActionController::Live::ClientDisconnected
          # クライアント切断
        ensure
          redis&.close
          sse.close
        end
      end

      private

      def set_job
        @job = current_user.jobs.find(params[:id])
      end

      def job_status_data
        {
          job_id: @job.id,
          status: @job.status,
          progress: @job.progress,
          result: @job.result,
          error: @job.error_message
        }
      end
    end
  end
end
```

```ruby
# SSEヘルパークラス
# lib/sse.rb
class SSE
  def initialize(stream, options = {})
    @stream = stream
    @options = options
  end

  def write(data, options = {})
    options = @options.merge(options)

    options.each do |key, value|
      @stream.write("#{key}: #{value}\n")
    end

    @stream.write("data: #{data.to_json}\n\n")
  end

  def close
    @stream.close
  end
end
```

```ruby
# ジョブから通知を送信
# app/jobs/example_job.rb
class ExampleJob < ApplicationJob
  def perform(job_record_id)
    job_record = JobRecord.find(job_record_id)
    redis = Redis.new(url: ENV['REDIS_URL'])

    begin
      publish_status(redis, job_record, 'processing', 0)

      result = process_task(job_record) do |progress|
        publish_status(redis, job_record, 'processing', progress)
      end

      job_record.update!(status: 'completed', result: result)
      publish_status(redis, job_record, 'completed', 100, result)
    rescue StandardError => e
      job_record.update!(status: 'failed', error_message: e.message)
      publish_status(redis, job_record, 'failed', nil, nil, e.message)
      raise
    ensure
      redis.close
    end
  end

  private

  def publish_status(redis, job_record, status, progress, result = nil, error = nil)
    data = {
      job_id: job_record.id,
      status: status,
      progress: progress,
      result: result,
      error: error,
      updated_at: Time.current.iso8601
    }

    redis.publish("job_status_#{job_record.id}", data.to_json)

    # ActionCableにも通知（両方使う場合）
    ActionCable.server.broadcast("job_status_#{job_record.id}", data)
  end
end
```

### Next.js フロントエンド実装（SSE）

```typescript
// hooks/useJobStatusSSE.ts
import { useState, useEffect, useRef } from 'react';
import { useAuth } from './useAuth';

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

export const useJobStatusSSE = (jobId: string | null) => {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    if (!jobId || !token) return;

    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/jobs/${jobId}/stream`;

    // SSEはヘッダーを送れないため、クエリパラメータでトークンを渡す
    const eventSource = new EventSource(`${url}?token=${token}`, {
      withCredentials: true,
    });

    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setConnected(true);
      setError(null);
    };

    eventSource.addEventListener('job-status', (event) => {
      const data = JSON.parse(event.data);
      setStatus({
        status: data.status,
        progress: data.progress,
        result: data.result,
        error: data.error,
      });

      // 完了/失敗で接続を閉じる
      if (['completed', 'failed'].includes(data.status)) {
        eventSource.close();
        setConnected(false);
      }
    });

    eventSource.onerror = () => {
      setError('接続エラーが発生しました');
      setConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [jobId, token]);

  return { status, connected, error };
};
```

### ポーリングによる実装

WebSocketやSSEが使用できない環境向けのフォールバック実装です。

```ruby
# app/controllers/api/v1/jobs_controller.rb
module Api
  module V1
    class JobsController < ApplicationController
      before_action :authenticate_user!

      def show
        job = current_user.jobs.find(params[:id])

        render json: {
          id: job.id,
          status: job.status,
          progress: job.progress,
          result: job.result,
          error: job.error_message,
          updated_at: job.updated_at.iso8601
        }
      end
    end
  end
end
```

```typescript
// hooks/useJobStatusPolling.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

interface UseJobStatusPollingOptions {
  interval?: number; // ポーリング間隔（ミリ秒）
  enabled?: boolean;
}

export const useJobStatusPolling = (
  jobId: string | null,
  options: UseJobStatusPollingOptions = {}
) => {
  const { interval = 2000, enabled = true } = options;
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!jobId || !token) return;

    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/jobs/${jobId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }

      const data = await response.json();
      setStatus({
        status: data.status,
        progress: data.progress,
        result: data.result,
        error: data.error,
      });
      setError(null);

      // 完了/失敗でポーリング停止
      if (['completed', 'failed'].includes(data.status)) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [jobId, token]);

  useEffect(() => {
    if (!jobId || !token || !enabled) return;

    // 初回fetch
    fetchStatus();

    // ポーリング開始
    intervalRef.current = setInterval(fetchStatus, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobId, token, enabled, interval, fetchStatus]);

  return { status, loading, error, refetch: fetchStatus };
};
```

### 統合フック（フォールバック付き）

WebSocket → SSE → ポーリングの順でフォールバックする統合フックです。

```typescript
// hooks/useJobStatusWithFallback.ts
import { useState, useEffect } from 'react';
import { useJobStatus } from './useJobStatus'; // ActionCable
import { useJobStatusSSE } from './useJobStatusSSE';
import { useJobStatusPolling } from './useJobStatusPolling';

type TransportType = 'websocket' | 'sse' | 'polling';

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: Record<string, unknown>;
  error?: string;
}

export const useJobStatusWithFallback = (jobId: string | null) => {
  const [transport, setTransport] = useState<TransportType>('websocket');

  // WebSocket（ActionCable）
  const {
    status: wsStatus,
    connected: wsConnected,
  } = useJobStatus(transport === 'websocket' ? jobId : null);

  // SSE
  const {
    status: sseStatus,
    connected: sseConnected,
    error: sseError,
  } = useJobStatusSSE(transport === 'sse' ? jobId : null);

  // ポーリング
  const {
    status: pollingStatus,
  } = useJobStatusPolling(transport === 'polling' ? jobId : null);

  // フォールバックロジック
  useEffect(() => {
    if (transport === 'websocket' && !wsConnected) {
      // WebSocket接続失敗 → SSEにフォールバック
      const timeout = setTimeout(() => {
        if (!wsConnected) {
          console.log('Falling back to SSE');
          setTransport('sse');
        }
      }, 5000);
      return () => clearTimeout(timeout);
    }
  }, [transport, wsConnected]);

  useEffect(() => {
    if (transport === 'sse' && sseError) {
      // SSE接続失敗 → ポーリングにフォールバック
      console.log('Falling back to polling');
      setTransport('polling');
    }
  }, [transport, sseError]);

  // 現在のトランスポートに応じたステータスを返す
  const status = transport === 'websocket'
    ? wsStatus
    : transport === 'sse'
      ? sseStatus
      : pollingStatus;

  return { status, transport };
};
```

### API設計のベストプラクティス

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :jobs, only: [:create, :show] do
        member do
          get :stream # SSE用
        end
      end
    end
  end

  # ActionCable
  mount ActionCable.server => '/cable'
end
```

```ruby
# app/controllers/api/v1/jobs_controller.rb
module Api
  module V1
    class JobsController < ApplicationController
      before_action :authenticate_user!

      # POST /api/v1/jobs
      def create
        job = current_user.jobs.create!(
          job_type: params[:type],
          payload: params[:payload],
          status: 'pending'
        )

        # ジョブをキューに投入
        ProcessJobWorker.perform_async(job.id)

        render json: {
          id: job.id,
          status: job.status,
          # リアルタイム更新用のエンドポイント情報
          _links: {
            self: api_v1_job_url(job),
            stream: stream_api_v1_job_url(job),
            websocket: "#{websocket_url}/cable?token=#{current_token}"
          }
        }, status: :accepted
      end
    end
  end
end
```

### 環境変数設定例

```bash
# .env.production (Rails)
FRONTEND_URL=https://app.example.com
REDIS_URL=redis://localhost:6379/1

# .env.production (Next.js)
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_WS_URL=wss://api.example.com
```
