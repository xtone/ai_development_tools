# トラブルシューティングガイド

Solid Queue + ActionCable/Solid Cableを使用した非同期処理で発生しやすい問題と解決方法をまとめます。

## 目次

1. [ジョブが実行されない](#ジョブが実行されない)
2. [ステータスが更新されない](#ステータスが更新されない)
3. [WebSocket接続の問題](#websocket接続の問題)
4. [本番環境固有の問題](#本番環境固有の問題)
5. [パフォーマンス問題](#パフォーマンス問題)
6. [デバッグ方法](#デバッグ方法)

---

## ジョブが実行されない

### 症状

- ステータスが「準備中」のまま動かない
- ジョブがキューに入ったが処理されない

### 確認ポイントと解決策

#### 1. Solid Queueワーカーが起動しているか確認

```bash
# ローカル環境
bin/rails solid_queue:start

# ワーカープロセスの確認
ps aux | grep solid_queue
```

**Pumaプラグイン使用時:**

```ruby
# config/puma.rb
plugin :solid_queue

# 環境変数で有効化されているか確認
# SOLID_QUEUE_IN_PUMA=true
```

#### 2. キュー名が一致しているか確認

```ruby
# ジョブで指定したキュー名
class MyJob < ApplicationJob
  queue_as :default  # または環境プレフィックス付き
end

# solid_queue.ymlで処理するキュー名
workers:
  - queues:
      - default  # ここが一致している必要がある
```

**環境プレフィックスを使用している場合:**

```yaml
# config/solid_queue.yml
production:
  workers:
    - queues:
        - production_default  # QUEUE_PREFIX=production の場合
```

```ruby
# app/jobs/application_job.rb
class ApplicationJob < ActiveJob::Base
  queue_as do
    prefix = ENV.fetch('QUEUE_PREFIX', Rails.env)
    "#{prefix}_default"
  end
end
```

#### 3. データベースのジョブレコードを確認

```ruby
# Rails consoleで確認
SolidQueue::Job.where(finished_at: nil).order(created_at: :desc).limit(10)

# ready状態のジョブ
SolidQueue::ReadyExecution.count

# scheduled状態のジョブ（将来実行予定）
SolidQueue::ScheduledExecution.count

# claimed状態のジョブ（処理中）
SolidQueue::ClaimedExecution.count
```

#### 4. エラーで失敗しているか確認

```ruby
# 失敗したジョブ
SolidQueue::FailedExecution.order(created_at: :desc).limit(10).each do |fe|
  puts "Job: #{fe.job.class_name}"
  puts "Error: #{fe.error['message']}"
  puts "---"
end
```

#### 5. ActiveJobアダプターの設定確認

```ruby
# Rails consoleで確認
Rails.application.config.active_job.queue_adapter
# => :solid_queue であること
```

```ruby
# config/application.rb または config/environments/production.rb
config.active_job.queue_adapter = :solid_queue
```

---

## ステータスが更新されない

### 症状

- ステータスが「処理中: 0 / X 件」のまま動かない
- プログレスバーが更新されない

### 確認ポイントと解決策

#### 1. ActionCable/Solid Cable接続の確認

**ブラウザのDevTools:**

```
Network → WS → cable
```

- 接続状態が「101 Switching Protocols」であること
- Messagesタブでping/pongが定期的に送受信されていること

#### 2. チャンネルのサブスクリプション確認

```javascript
// ブラウザコンソールで確認
App.cable.subscriptions.subscriptions
// 接続中のサブスクリプション一覧が表示される
```

#### 3. ジョブ内でのブロードキャスト確認

```ruby
# app/jobs/my_job.rb
def perform(task_id)
  @task = AsyncTask.find(task_id)

  # 明示的にログ出力してデバッグ
  Rails.logger.info "Broadcasting to task #{@task.id}"

  @task.update!(status: :processing)
  broadcast_status  # この呼び出しが実行されているか

  # ...
end

def broadcast_status
  Rails.logger.info "TaskStatusChannel.broadcast_to called"

  TaskStatusChannel.broadcast_to(
    @task,
    {
      status: @task.status,
      progress: @task.progress_percentage,
      processed_items: @task.progress,
      total_items: @task.total_items
    }
  )
end
```

#### 4. Solid Cableのメッセージ確認

```ruby
# Rails consoleでメッセージを確認
SolidCable::Message.order(created_at: :desc).limit(10).each do |m|
  puts "Channel: #{m.channel}"
  puts "Payload: #{m.payload}"
  puts "Created: #{m.created_at}"
  puts "---"
end
```

#### 5. チャンネルのstream_for設定確認

```ruby
# app/channels/task_status_channel.rb
class TaskStatusChannel < ApplicationCable::Channel
  def subscribed
    task = AsyncTask.find(params[:task_id])

    # stream_forの引数がbroadcast_toの引数と一致していること
    stream_for task

    # デバッグ用ログ
    Rails.logger.info "Subscribed to task #{task.id}"
  end
end
```

---

## WebSocket接続の問題

### 症状

- 接続が確立されない
- 頻繁に切断される
- 認証エラー

### 確認ポイントと解決策

#### 1. 認証設定の確認

```ruby
# app/channels/application_cable/connection.rb
module ApplicationCable
  class Connection < ActionCable::Connection::Base
    identified_by :current_user

    def connect
      self.current_user = find_verified_user
      Rails.logger.info "ActionCable connected: user_id=#{current_user&.id}"
    rescue => e
      Rails.logger.error "ActionCable connection error: #{e.message}"
      reject_unauthorized_connection
    end

    private

    def find_verified_user
      # Deviseを使用している場合
      if (user = env['warden'].user)
        user
      # Cookieベースの認証
      elsif (user_id = cookies.encrypted[:user_id])
        User.find_by(id: user_id)
      else
        nil
      end
    end
  end
end
```

#### 2. CORS設定の確認（異なるドメインの場合）

```ruby
# config/environments/production.rb
config.action_cable.allowed_request_origins = [
  'https://example.com',
  'https://www.example.com'
]

# または全て許可（本番では非推奨）
config.action_cable.disable_request_forgery_protection = true
```

#### 3. Nginx/ALBの設定確認

**Nginx:**

```nginx
location /cable {
    proxy_pass http://rails_app;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # タイムアウト設定
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
}
```

**AWS ALB:**

- ターゲットグループのStickinessを有効化
- IdleTimeoutを適切に設定（デフォルト60秒は短い場合がある）

#### 4. クライアント側の再接続処理

```javascript
// app/javascript/channels/consumer.js
import { createConsumer } from "@rails/actioncable"

const consumer = createConsumer()

// 接続状態の監視
consumer.connection.events.open = () => {
  console.log('WebSocket connected')
}

consumer.connection.events.close = () => {
  console.log('WebSocket disconnected')
  // 自動再接続は ActionCable が行う
}

consumer.connection.events.error = (error) => {
  console.error('WebSocket error:', error)
}

export default consumer
```

---

## 本番環境固有の問題

### ECS/Fargateでジョブが実行されない

#### 1. Pumaプラグインの有効化確認

```bash
# ECSタスク定義の環境変数
SOLID_QUEUE_IN_PUMA=true
```

#### 2. ECSログの確認

```bash
# AWS CLIでログを確認
aws logs tail /ecs/my-app --follow

# 特定のログストリーム
aws logs get-log-events \
  --log-group-name /ecs/my-app \
  --log-stream-name ecs/rails/xxxxx \
  --limit 100
```

#### 3. コンテナの起動順序確認

```bash
# ECSタスクの状態確認
aws ecs describe-tasks \
  --cluster my-cluster \
  --tasks arn:aws:ecs:region:account:task/cluster/task-id

# コンテナのステータス
aws ecs describe-tasks \
  --cluster my-cluster \
  --tasks task-id \
  --query 'tasks[0].containers[*].{name:name,status:lastStatus,reason:reason}'
```

### ステージング/本番でジョブが混在する

#### 原因

同じDBを共有しているが、キュー名が分離されていない

#### 解決策

```yaml
# config/solid_queue.yml
staging:
  workers:
    - queues:
        - staging_default
        - staging_critical

production:
  workers:
    - queues:
        - production_default
        - production_critical
```

```bash
# 環境変数
# staging
QUEUE_PREFIX=staging

# production
QUEUE_PREFIX=production
```

### DBコネクションエラー

#### 症状

```
ActiveRecord::ConnectionNotEstablished
PG::ConnectionBad: could not connect to server
```

#### 解決策

1. **プール数の確認**

```yaml
# config/database.yml
production:
  pool: <%= ENV.fetch("DATABASE_POOL") { 25 } %>
```

2. **RDSのmax_connections確認**

```bash
aws rds describe-db-parameters \
  --db-parameter-group-name my-param-group \
  --query "Parameters[?ParameterName=='max_connections']"
```

3. **接続数の監視**

```sql
-- PostgreSQL
SELECT count(*) FROM pg_stat_activity;

-- MySQL
SHOW STATUS LIKE 'Threads_connected';
```

---

## パフォーマンス問題

### ジョブの処理が遅い

#### 1. N+1クエリの確認

```ruby
# ジョブ内でのクエリ最適化
def perform(task_id)
  @task = AsyncTask.find(task_id)

  # 悪い例
  users.each do |user|
    user.reports.each { |r| process(r) }  # N+1
  end

  # 良い例
  users.includes(:reports).each do |user|
    user.reports.each { |r| process(r) }
  end
end
```

#### 2. バッチ処理の最適化

```ruby
# 悪い例: 1件ずつ更新
users.each do |user|
  user.update!(processed: true)
end

# 良い例: バルク更新
User.where(id: users.map(&:id)).update_all(processed: true)
```

#### 3. 進捗更新頻度の調整

```ruby
PROGRESS_UPDATE_INTERVAL = 100  # 100件ごとに更新

def process_items
  items.find_each.with_index do |item, index|
    process_item(item)

    # 頻繁すぎる更新は避ける
    if (index % PROGRESS_UPDATE_INTERVAL).zero?
      update_progress(index)
    end
  end
end
```

### WebSocket接続数が多い

#### 1. 接続数の監視

```ruby
# ActionCableの接続数（Redis使用時）
ActionCable.server.pubsub.redis_connection_for_subscriptions.info['connected_clients']

# Solid Cable使用時は DBセッション数を確認
```

#### 2. 不要な接続の切断

```javascript
// ページ離脱時に切断
window.addEventListener('beforeunload', () => {
  if (subscription) {
    subscription.unsubscribe()
  }
})
```

---

## デバッグ方法

### ローカル環境でのデバッグ

#### 1. ログレベルの設定

```ruby
# config/environments/development.rb
config.log_level = :debug

# ActionCableのログ
config.action_cable.logger = Logger.new(STDOUT)
```

#### 2. Rails consoleでのテスト

```ruby
# ジョブの直接実行
MyJob.perform_now(task_id)

# ジョブのエンキュー
MyJob.perform_later(task_id)

# ブロードキャストのテスト
TaskStatusChannel.broadcast_to(
  AsyncTask.find(1),
  { test: true }
)
```

#### 3. Solid Queueの状態確認

```ruby
# ジョブ一覧
SolidQueue::Job.all

# 実行待ちジョブ
SolidQueue::ReadyExecution.includes(:job).each do |e|
  puts "#{e.job.class_name}: #{e.job.arguments}"
end

# 失敗したジョブの詳細
SolidQueue::FailedExecution.last.error
```

### 本番環境でのデバッグ

#### 1. 構造化ログの活用

```ruby
# app/jobs/application_job.rb
class ApplicationJob < ActiveJob::Base
  around_perform do |job, block|
    Rails.logger.info({
      event: 'job_started',
      job_class: job.class.name,
      job_id: job.job_id,
      arguments: job.arguments.first(3)  # 最初の3引数のみ
    }.to_json)

    block.call

    Rails.logger.info({
      event: 'job_completed',
      job_class: job.class.name,
      job_id: job.job_id
    }.to_json)
  rescue => e
    Rails.logger.error({
      event: 'job_failed',
      job_class: job.class.name,
      job_id: job.job_id,
      error: e.message,
      backtrace: e.backtrace.first(5)
    }.to_json)
    raise
  end
end
```

#### 2. AWS CloudWatch Logsでの検索

```bash
# エラーログの検索
aws logs filter-log-events \
  --log-group-name /ecs/my-app \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# 特定のジョブのログ
aws logs filter-log-events \
  --log-group-name /ecs/my-app \
  --filter-pattern "MyJob"
```

#### 3. Rails consoleへの接続（ECS Exec）

```bash
# ECS Execを使用してコンテナに接続
aws ecs execute-command \
  --cluster my-cluster \
  --task task-id \
  --container rails \
  --interactive \
  --command "/bin/bash"

# コンテナ内でRails console
bundle exec rails console
```

### 問題の切り分けフロー

```
1. ジョブがキューに入っているか？
   └── No → ジョブのエンキュー処理を確認
   └── Yes ↓

2. ワーカーが動作しているか？
   └── No → Solid Queueの起動設定を確認
   └── Yes ↓

3. ジョブが処理されているか？
   └── No → キュー名の一致、エラーログを確認
   └── Yes ↓

4. ブロードキャストが実行されているか？
   └── No → ジョブ内のbroadcast呼び出しを確認
   └── Yes ↓

5. WebSocket接続が確立されているか？
   └── No → 認証、CORS、Proxy設定を確認
   └── Yes ↓

6. クライアントでメッセージを受信しているか？
   └── No → チャンネルのsubscribed、stream_forを確認
   └── Yes → UIの更新処理を確認
```

---

## 参照

- [Solid Queue Troubleshooting](https://github.com/rails/solid_queue#troubleshooting)
- [ActionCable Overview](https://guides.rubyonrails.org/action_cable_overview.html)
- [AWS ECS Troubleshooting](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/troubleshooting.html)
