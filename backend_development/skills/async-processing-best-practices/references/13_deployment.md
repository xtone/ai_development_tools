# 本番環境デプロイガイド

Solid Queue + ActionCable/Solid Cableを使用した非同期処理アプリケーションの本番環境デプロイに関するベストプラクティスです。

## 目次

1. [Pumaプラグイン設定](#pumaプラグイン設定)
2. [ECS/Fargate環境](#ecsfargate環境)
3. [Kubernetes環境](#kubernetes環境)
4. [環境分離設定](#環境分離設定)
5. [DBコネクションプール設計](#dbコネクションプール設計)
6. [ヘルスチェック](#ヘルスチェック)
7. [CI/CD設定](#cicd設定)

---

## Pumaプラグイン設定

### Solid Queueをpumaプロセス内で実行

本番環境では、別プロセスでワーカーを起動する代わりに、Pumaプラグインを使用してワーカーを同一プロセス内で実行できます。これにより運用が簡素化されます。

```ruby
# config/puma.rb

# Solid Queue プラグインを有効化
plugin :solid_queue if ENV.fetch("SOLID_QUEUE_IN_PUMA", "false") == "true"

# ワーカー数（マルチプロセス構成の場合）
workers ENV.fetch("WEB_CONCURRENCY") { 2 }

# スレッド数
max_threads_count = ENV.fetch("RAILS_MAX_THREADS") { 5 }
min_threads_count = ENV.fetch("RAILS_MIN_THREADS") { max_threads_count }
threads min_threads_count, max_threads_count

# ポート設定
port ENV.fetch("PORT") { 3000 }

# 環境設定
environment ENV.fetch("RAILS_ENV") { "development" }

# プリロード（メモリ効率化）
preload_app!

# フォーク前の処理
on_worker_boot do
  ActiveRecord::Base.establish_connection if defined?(ActiveRecord)
end

# シャットダウン時の処理
on_worker_shutdown do
  # Solid Queueのgraceful shutdown
  SolidQueue.supervisor&.stop if defined?(SolidQueue)
end
```

### 環境変数の設定

```bash
# 本番環境用 .env.production
SOLID_QUEUE_IN_PUMA=true
RAILS_MAX_THREADS=5
WEB_CONCURRENCY=2
```

---

## ECS/Fargate環境

### エントリーポイントスクリプト

```bash
#!/bin/bash
# docker/rails/entrypoint-ecs.sh

set -e

echo "Starting entrypoint script..."

# 環境変数の検証
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${RAILS_ENV:?RAILS_ENV is required}"

# データベース接続待機
wait_for_db() {
  echo "Waiting for database connection..."
  local max_attempts=30
  local attempt=1

  while [ $attempt -le $max_attempts ]; do
    if bundle exec rails db:version > /dev/null 2>&1; then
      echo "Database is ready!"
      return 0
    fi
    echo "Attempt $attempt/$max_attempts: Database not ready, waiting..."
    sleep 2
    attempt=$((attempt + 1))
  done

  echo "ERROR: Could not connect to database after $max_attempts attempts"
  exit 1
}

# マイグレーション実行
run_migrations() {
  echo "Running database migrations..."

  # メインDB
  bundle exec rails db:migrate

  # Solid Queue用のマイグレーション（DB分離している場合）
  if [ "${SOLID_QUEUE_SEPARATE_DB:-false}" = "true" ]; then
    echo "Running Solid Queue migrations..."
    bundle exec rails solid_queue:install:migrations
    bundle exec rails db:migrate:queue
  fi

  # Solid Cable用のマイグレーション（DB分離している場合）
  if [ "${SOLID_CABLE_SEPARATE_DB:-false}" = "true" ]; then
    echo "Running Solid Cable migrations..."
    bundle exec rails solid_cable:install:migrations
    bundle exec rails db:migrate:cable
  fi

  echo "Migrations completed!"
}

# メイン処理
main() {
  wait_for_db

  # マイグレーション実行（指定された場合）
  if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    run_migrations
  fi

  # アセットプリコンパイル（必要な場合）
  if [ "${PRECOMPILE_ASSETS:-false}" = "true" ]; then
    echo "Precompiling assets..."
    bundle exec rails assets:precompile
  fi

  echo "Starting application..."
  exec "$@"
}

main "$@"
```

### Dockerfile

```dockerfile
# Dockerfile
FROM ruby:3.3-slim AS base

# 必要なパッケージのインストール
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    curl \
    libpq-dev \
    default-mysql-client \
    nodejs \
    npm && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Gemのインストール
COPY Gemfile Gemfile.lock ./
RUN bundle install --jobs 4 --retry 3

# アプリケーションコードのコピー
COPY . .

# エントリーポイントの設定
COPY docker/rails/entrypoint-ecs.sh /usr/bin/
RUN chmod +x /usr/bin/entrypoint-ecs.sh

ENTRYPOINT ["entrypoint-ecs.sh"]

# デフォルトコマンド
CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]
```

### ECSタスク定義

```json
{
  "family": "my-app-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "rails",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/my-app:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "RAILS_ENV", "value": "production"},
        {"name": "SOLID_QUEUE_IN_PUMA", "value": "true"},
        {"name": "RUN_MIGRATIONS", "value": "true"},
        {"name": "RAILS_MAX_THREADS", "value": "5"},
        {"name": "WEB_CONCURRENCY", "value": "2"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:my-app/database-url"
        },
        {
          "name": "SECRET_KEY_BASE",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:my-app/secret-key-base"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/my-app",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### CodeBuildのbuildspec.yml

```yaml
# buildspec.yml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}

  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $REPOSITORY_URI:latest .
      - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG

  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $REPOSITORY_URI:latest
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '[{"name":"rails","imageUri":"%s"}]' $REPOSITORY_URI:$IMAGE_TAG > imagedefinitions.json

artifacts:
  files:
    - imagedefinitions.json
```

---

## Kubernetes環境

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: rails
          image: my-registry/my-app:latest
          ports:
            - containerPort: 3000
          env:
            - name: RAILS_ENV
              value: "production"
            - name: SOLID_QUEUE_IN_PUMA
              value: "true"
            - name: RAILS_MAX_THREADS
              value: "5"
            - name: WEB_CONCURRENCY
              value: "2"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: my-app-secrets
                  key: database-url
            - name: SECRET_KEY_BASE
              valueFrom:
                secretKeyRef:
                  name: my-app-secrets
                  key: secret-key-base
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 10"]
      terminationGracePeriodSeconds: 60
```

### マイグレーションJob

```yaml
# k8s/migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: my-app-migration
  annotations:
    "helm.sh/hook": pre-upgrade
    "helm.sh/hook-weight": "-1"
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migration
          image: my-registry/my-app:latest
          command: ["bundle", "exec", "rails", "db:migrate"]
          env:
            - name: RAILS_ENV
              value: "production"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: my-app-secrets
                  key: database-url
  backoffLimit: 3
```

---

## 環境分離設定

### ステージング/本番でDBを共有する場合

ステージング環境と本番環境で同じデータベースを共有している場合、各環境のジョブが正しい環境で実行されるようにキュー名を分離する必要があります。

#### Solid Queue設定

```yaml
# config/solid_queue.yml
default: &default
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - queues: "*"
      threads: 3
      processes: 1
      polling_interval: 0.1

development:
  <<: *default

test:
  <<: *default

staging:
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    # 環境プレフィックス付きのキュー名のみ処理
    - queues:
        - <%= ENV.fetch('QUEUE_PREFIX', 'staging') %>_default
        - <%= ENV.fetch('QUEUE_PREFIX', 'staging') %>_critical
        - <%= ENV.fetch('QUEUE_PREFIX', 'staging') %>_low_priority
      threads: 3
      processes: 1
      polling_interval: 0.1

production:
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    # 環境プレフィックス付きのキュー名のみ処理
    - queues:
        - <%= ENV.fetch('QUEUE_PREFIX', 'production') %>_default
        - <%= ENV.fetch('QUEUE_PREFIX', 'production') %>_critical
        - <%= ENV.fetch('QUEUE_PREFIX', 'production') %>_low_priority
      threads: 5
      processes: 2
      polling_interval: 0.1
```

#### ジョブでのキュー名設定

```ruby
# app/jobs/application_job.rb
class ApplicationJob < ActiveJob::Base
  # 環境プレフィックス付きのキュー名を使用
  queue_as do
    prefix = ENV.fetch('QUEUE_PREFIX', Rails.env)
    "#{prefix}_#{self.class.queue_name_without_prefix}"
  end

  class << self
    def queue_name_without_prefix
      @queue_name_without_prefix || 'default'
    end

    def queue_as_without_prefix(queue_name)
      @queue_name_without_prefix = queue_name.to_s
    end
  end
end

# app/jobs/critical_job.rb
class CriticalJob < ApplicationJob
  queue_as_without_prefix :critical

  def perform(...)
    # ...
  end
end
```

#### 環境変数の設定

```bash
# staging環境
QUEUE_PREFIX=staging

# production環境
QUEUE_PREFIX=production
```

### Solid Cableの環境分離

```yaml
# config/cable.yml
development:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour

staging:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour
  # 環境プレフィックスを使用してチャンネル名を分離
  channel_prefix: <%= ENV.fetch('CABLE_PREFIX', 'staging') %>

production:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour
  channel_prefix: <%= ENV.fetch('CABLE_PREFIX', 'production') %>
```

---

## DBコネクションプール設計

### プール数の計算

Solid Queue + Solid Cable + Pumaを同一プロセスで実行する場合、必要なコネクション数は以下のように計算します。

```
必要コネクション数 =
  (Pumaワーカー数 × Pumaスレッド数) +  # Webリクエスト用
  (Solid Queueワーカープロセス数 × スレッド数) +  # ジョブ処理用
  (Solid Cableポーリング用) +  # WebSocket用
  (余裕分)
```

#### 設定例

```yaml
# config/database.yml
default: &default
  adapter: mysql2
  encoding: utf8mb4
  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 5 } %>
  username: <%= ENV.fetch("DATABASE_USERNAME") { "root" } %>
  password: <%= ENV.fetch("DATABASE_PASSWORD") { "" } %>

development:
  <<: *default
  database: my_app_development

production:
  <<: *default
  database: my_app_production
  # プール数の計算:
  # Puma: 2ワーカー × 5スレッド = 10
  # Solid Queue: 2プロセス × 5スレッド = 10
  # Solid Cable: 2
  # 余裕: 3
  # 合計: 25
  pool: <%= ENV.fetch("DATABASE_POOL") { 25 } %>

  # キューDB（分離する場合）
  queue:
    <<: *default
    database: my_app_queue_production
    pool: <%= ENV.fetch("QUEUE_DATABASE_POOL") { 15 } %>
    migrations_paths: db/queue_migrate

  # CableDB（分離する場合）
  cable:
    <<: *default
    database: my_app_cable_production
    pool: <%= ENV.fetch("CABLE_DATABASE_POOL") { 5 } %>
    migrations_paths: db/cable_migrate
```

### RDS/Auroraの設定確認

```bash
# AWS CLIでRDSのmax_connectionsを確認
aws rds describe-db-instances \
  --db-instance-identifier my-db-instance \
  --query 'DBInstances[0].DBParameterGroups[0].DBParameterGroupName'

aws rds describe-db-parameters \
  --db-parameter-group-name my-parameter-group \
  --query "Parameters[?ParameterName=='max_connections'].ParameterValue"
```

### コネクション数の監視

```ruby
# lib/tasks/db_connections.rake
namespace :db do
  desc "Show current database connection stats"
  task connections: :environment do
    result = ActiveRecord::Base.connection.execute(<<~SQL)
      SELECT
        COUNT(*) as total_connections,
        SUM(IF(command != 'Sleep', 1, 0)) as active_connections,
        SUM(IF(command = 'Sleep', 1, 0)) as idle_connections
      FROM information_schema.processlist
      WHERE db = DATABASE()
    SQL

    stats = result.first
    puts "Total Connections: #{stats[0]}"
    puts "Active Connections: #{stats[1]}"
    puts "Idle Connections: #{stats[2]}"
    puts "Pool Size: #{ActiveRecord::Base.connection_pool.size}"
    puts "Pool Connections: #{ActiveRecord::Base.connection_pool.connections.size}"
  end
end
```

---

## ヘルスチェック

### ヘルスチェックエンドポイント

```ruby
# app/controllers/health_controller.rb
class HealthController < ApplicationController
  skip_before_action :authenticate_user!, if: -> { respond_to?(:authenticate_user!) }

  def show
    checks = {
      database: check_database,
      solid_queue: check_solid_queue,
      redis: check_redis
    }

    status = checks.values.all? { |c| c[:status] == 'ok' } ? :ok : :service_unavailable

    render json: {
      status: status == :ok ? 'healthy' : 'unhealthy',
      checks: checks,
      timestamp: Time.current.iso8601
    }, status: status
  end

  private

  def check_database
    ActiveRecord::Base.connection.execute('SELECT 1')
    { status: 'ok' }
  rescue StandardError => e
    { status: 'error', message: e.message }
  end

  def check_solid_queue
    # Solid Queueのプロセスが動作しているか確認
    if defined?(SolidQueue) && SolidQueue.supervisor&.alive?
      { status: 'ok' }
    else
      { status: 'ok', message: 'Supervisor not running in this process' }
    end
  rescue StandardError => e
    { status: 'error', message: e.message }
  end

  def check_redis
    return { status: 'skipped', message: 'Redis not configured' } unless defined?(Redis)

    Redis.current.ping
    { status: 'ok' }
  rescue StandardError => e
    { status: 'error', message: e.message }
  end
end

# config/routes.rb
Rails.application.routes.draw do
  get '/health', to: 'health#show'
end
```

### Solid Queueのヘルスチェック

```ruby
# app/controllers/health_controller.rb（追加）
def check_solid_queue_detailed
  return { status: 'skipped' } unless defined?(SolidQueue)

  # 最近のジョブ実行状況を確認
  recent_jobs = SolidQueue::Job.where('created_at > ?', 5.minutes.ago)
  stuck_jobs = SolidQueue::Job.where(
    'scheduled_at < ? AND finished_at IS NULL',
    10.minutes.ago
  )

  {
    status: stuck_jobs.count.zero? ? 'ok' : 'warning',
    recent_jobs_count: recent_jobs.count,
    stuck_jobs_count: stuck_jobs.count
  }
rescue StandardError => e
  { status: 'error', message: e.message }
end
```

---

## CI/CD設定

### GitHub Actionsワークフロー

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

env:
  AWS_REGION: ap-northeast-1
  ECR_REPOSITORY: my-app
  ECS_SERVICE: my-app-service
  ECS_CLUSTER: my-app-cluster

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: password
          MYSQL_DATABASE: test
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
      - uses: actions/checkout@v4

      - name: Set up Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.3'
          bundler-cache: true

      - name: Run tests
        env:
          DATABASE_URL: mysql2://root:password@127.0.0.1:3306/test
          RAILS_ENV: test
        run: |
          bundle exec rails db:setup
          bundle exec rspec

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image to Amazon ECR
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

      - name: Run database migrations
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          aws ecs run-task \
            --cluster $ECS_CLUSTER \
            --task-definition my-app-migration \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}" \
            --overrides "{\"containerOverrides\":[{\"name\":\"migration\",\"image\":\"$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG\"}]}"

      - name: Deploy to Amazon ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ecs-task-definition.json
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true
```

---

## 参照

- [Solid Queue GitHub](https://github.com/rails/solid_queue)
- [Solid Cable GitHub](https://github.com/rails/solid_cable)
- [Puma Documentation](https://puma.io/)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
