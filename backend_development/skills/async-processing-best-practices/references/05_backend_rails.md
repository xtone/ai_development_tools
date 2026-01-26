# Rails (ActiveJob) バックエンド実装ベストプラクティス

Ruby on RailsのActiveJobを使用した非同期処理のバックエンド実装におけるベストプラクティスをまとめます。

## 目次

1. [パラメータの受け取り方](#パラメータの受け取り方)
2. [エラー発生時の処理と通知](#エラー発生時の処理と通知)
3. [進捗の状態管理](#進捗の状態管理)
4. [ジョブの設計パターン](#ジョブの設計パターン)
5. [継続可能なジョブ（Continuable Jobs）](#継続可能なジョブcontinuable-jobs)
6. [テスト戦略](#テスト戦略)

---

## パラメータの受け取り方

### 基本原則

ActiveJobのパラメータはシリアライズされてキューに保存されるため、以下の点に注意が必要です。

```ruby
# ❌ 悪い例: ActiveRecordオブジェクトを直接渡す（非推奨だが動作する）
# GlobalIDによりシリアライズされるが、ジョブ実行時にレコードが削除されている可能性がある
class ProcessOrderJob < ApplicationJob
  def perform(order)
    order.process! # orderが存在しない場合に例外発生
  end
end

# ✅ 良い例: IDを渡して、ジョブ内でレコードを取得
class ProcessOrderJob < ApplicationJob
  def perform(order_id)
    order = Order.find_by(id: order_id)
    return if order.nil? # レコードが存在しない場合は早期リターン

    order.process!
  end
end
```

### パラメータサイズの制限

キューバックエンドによってパラメータサイズに制限があります。

| バックエンド | 最大サイズ | 推奨対応 |
|-------------|-----------|---------|
| Sidekiq (Redis) | 約512MB（Redis文字列制限） | 実用上は数KB以下を推奨 |
| Solid Queue (DB) | TEXT型の制限（MySQL: 64KB, PostgreSQL: 1GB） | 数KB以下を推奨 |

### 大きなパラメータの処理

```ruby
# ❌ 悪い例: 大きなデータを直接パラメータとして渡す
class BulkImportJob < ApplicationJob
  def perform(csv_content) # 数MB〜数百MBのCSVデータ
    # ...
  end
end

# ✅ 良い例: ファイルストレージを使用
class BulkImportJob < ApplicationJob
  def perform(import_id)
    import = Import.find(import_id)

    # Active Storageからファイルを取得
    import.file.open do |file|
      CSV.foreach(file, headers: true) do |row|
        # 行ごとに処理
      end
    end
  end
end
```

### 大量のIDリストを処理する場合

```ruby
# ❌ 悪い例: 大量のIDをパラメータとして渡す
class BulkNotifyJob < ApplicationJob
  def perform(user_ids) # 数万件のID配列
    User.where(id: user_ids).find_each do |user|
      user.notify!
    end
  end
end

# ✅ 良い例: バッチジョブを作成するか、条件を渡す
class BulkNotifyJob < ApplicationJob
  BATCH_SIZE = 1000

  def perform(query_params)
    users = User.where(query_params)

    users.find_in_batches(batch_size: BATCH_SIZE) do |batch|
      batch.each do |user|
        # 個別のジョブをエンキュー
        NotifyUserJob.perform_later(user.id)
      end
    end
  end
end

# または、バッチ処理用のレコードを作成
class BulkNotifyJob < ApplicationJob
  def perform(bulk_notification_id)
    bulk = BulkNotification.find(bulk_notification_id)

    # 対象ユーザーはbulk_notificationに紐づくスコープで取得
    bulk.target_users.find_each do |user|
      NotifyUserJob.perform_later(user.id)
    end

    bulk.update!(status: :completed)
  end
end
```

### パラメータのバリデーション

```ruby
class ProcessDataJob < ApplicationJob
  class InvalidParameterError < StandardError; end

  def perform(params)
    validate_params!(params)

    # 処理実行
  end

  private

  def validate_params!(params)
    raise InvalidParameterError, "data_type is required" unless params[:data_type].present?
    raise InvalidParameterError, "target_id is required" unless params[:target_id].present?

    unless %w[csv json xml].include?(params[:data_type])
      raise InvalidParameterError, "Invalid data_type: #{params[:data_type]}"
    end
  end
end
```

---

## エラー発生時の処理と通知

### リトライ設定

```ruby
class ExternalApiJob < ApplicationJob
  # リトライ回数と待機時間の設定
  retry_on Net::OpenTimeout, wait: :polynomially_longer, attempts: 5
  retry_on Timeout::Error, wait: 5.seconds, attempts: 3

  # 特定のエラーはリトライしない
  discard_on ActiveRecord::RecordNotFound
  discard_on ArgumentError

  # すべてのリトライ失敗後の処理
  after_discard do |job, error|
    ErrorNotifier.notify(
      error: error,
      job_class: job.class.name,
      job_id: job.job_id,
      arguments: job.arguments
    )
  end

  def perform(api_request_id)
    request = ApiRequest.find(api_request_id)
    request.execute!
  end
end
```

### 詳細なエラーハンドリング

```ruby
class DataProcessingJob < ApplicationJob
  class ProcessingError < StandardError; end
  class RetryableError < StandardError; end
  class FatalError < StandardError; end

  retry_on RetryableError, wait: :polynomially_longer, attempts: 5
  discard_on FatalError

  def perform(task_id)
    task = AsyncTask.find(task_id)

    begin
      task.update!(status: :processing, started_at: Time.current)

      result = process_data(task)

      task.update!(
        status: :completed,
        completed_at: Time.current,
        result: result
      )

      notify_completion(task)

    rescue RetryableError => e
      task.update!(
        status: :retrying,
        last_error: e.message,
        retry_count: task.retry_count + 1
      )
      raise # リトライのために再raise

    rescue FatalError => e
      task.update!(
        status: :failed,
        completed_at: Time.current,
        last_error: e.message
      )
      notify_failure(task, e)
      raise # discard_onで処理される

    rescue StandardError => e
      task.update!(
        status: :failed,
        completed_at: Time.current,
        last_error: "#{e.class}: #{e.message}"
      )
      notify_failure(task, e)
      raise # デフォルトのリトライ動作
    end
  end

  private

  def process_data(task)
    # 実際の処理
  end

  def notify_completion(task)
    # ActionCable経由で通知
    TaskChannel.broadcast_to(
      task.user,
      { type: 'completed', task_id: task.id, result: task.result }
    )
  end

  def notify_failure(task, error)
    # ActionCable経由でエラー通知
    TaskChannel.broadcast_to(
      task.user,
      { type: 'failed', task_id: task.id, error: error.message }
    )

    # 管理者への通知（Slack等）
    AdminNotifier.job_failed(task, error)
  end
end
```

### エラー通知サービスの実装

```ruby
# app/services/error_notifier.rb
class ErrorNotifier
  class << self
    def notify(error:, job_class:, job_id:, arguments:, **context)
      # 構造化ログ出力
      Rails.logger.error({
        event: 'job_error',
        job_class: job_class,
        job_id: job_id,
        error_class: error.class.name,
        error_message: error.message,
        backtrace: error.backtrace&.first(10),
        arguments: sanitize_arguments(arguments),
        **context
      }.to_json)

      # 外部サービスへの通知（Sentry, Bugsnag等）
      if defined?(Sentry)
        Sentry.capture_exception(error, extra: {
          job_class: job_class,
          job_id: job_id,
          arguments: sanitize_arguments(arguments)
        })
      end

      # 重大なエラーの場合はSlack通知
      if critical_error?(error)
        SlackNotifier.notify_critical_error(
          error: error,
          job_class: job_class,
          job_id: job_id
        )
      end
    end

    private

    def sanitize_arguments(arguments)
      # センシティブな情報をマスク
      arguments.map do |arg|
        case arg
        when Hash
          arg.transform_values { |v| sensitive_key?(v) ? '[FILTERED]' : v }
        else
          arg
        end
      end
    end

    def sensitive_key?(key)
      %w[password token secret api_key].any? { |s| key.to_s.include?(s) }
    end

    def critical_error?(error)
      [
        ActiveRecord::ConnectionNotEstablished,
        Redis::CannotConnectError
      ].any? { |klass| error.is_a?(klass) }
    end
  end
end
```

### Dead Letter Queue（DLQ）パターン

```ruby
# config/initializers/sidekiq.rb（Sidekiq使用時）
Sidekiq.configure_server do |config|
  config.death_handlers << ->(job, ex) do
    # すべてのリトライが失敗したジョブを記録
    DeadJob.create!(
      job_class: job['class'],
      job_id: job['jid'],
      arguments: job['args'],
      error_class: ex.class.name,
      error_message: ex.message,
      failed_at: Time.current
    )
  end
end

# app/models/dead_job.rb
class DeadJob < ApplicationRecord
  scope :recent, -> { where('failed_at > ?', 7.days.ago) }
  scope :by_class, ->(klass) { where(job_class: klass) }

  def retry!
    job_class.constantize.perform_later(*arguments)
    update!(retried_at: Time.current)
  end
end
```

---

## 進捗の状態管理

### 状態管理用モデルの設計

```ruby
# db/migrate/xxx_create_async_tasks.rb
class CreateAsyncTasks < ActiveRecord::Migration[7.1]
  def change
    create_table :async_tasks do |t|
      t.references :user, null: false, foreign_key: true
      t.string :task_type, null: false
      t.string :status, null: false, default: 'pending'
      t.integer :progress, default: 0
      t.integer :total_items
      t.jsonb :params, default: {}
      t.jsonb :result, default: {}
      t.text :last_error
      t.integer :retry_count, default: 0
      t.datetime :started_at
      t.datetime :completed_at

      t.timestamps

      t.index [:user_id, :status]
      t.index [:task_type, :status]
      t.index :created_at
    end
  end
end

# app/models/async_task.rb
class AsyncTask < ApplicationRecord
  belongs_to :user

  # ステータス定義
  STATUSES = {
    pending: 'pending',
    queued: 'queued',
    processing: 'processing',
    completed: 'completed',
    failed: 'failed',
    cancelled: 'cancelled'
  }.freeze

  enum :status, STATUSES

  validates :task_type, presence: true
  validates :status, presence: true, inclusion: { in: STATUSES.values }
  validates :progress, numericality: {
    greater_than_or_equal_to: 0,
    less_than_or_equal_to: 100
  }

  # 進捗率の計算
  def progress_percentage
    return 0 if total_items.nil? || total_items.zero?
    [(progress.to_f / total_items * 100).round, 100].min
  end

  # 残り時間の推定
  def estimated_remaining_time
    return nil unless processing? && progress.positive?

    elapsed = Time.current - started_at
    rate = progress.to_f / elapsed
    remaining_items = total_items - progress

    (remaining_items / rate).seconds
  end

  # キャンセル可能かどうか
  def cancellable?
    pending? || queued? || processing?
  end

  def cancel!
    return false unless cancellable?

    update!(status: :cancelled, completed_at: Time.current)
    broadcast_status_change
    true
  end

  def broadcast_status_change
    TaskChannel.broadcast_to(user, status_payload)
  end

  def status_payload
    {
      type: 'status_update',
      task_id: id,
      status: status,
      progress: progress_percentage,
      estimated_remaining: estimated_remaining_time&.to_i,
      result: completed? ? result : nil,
      error: failed? ? last_error : nil
    }
  end
end
```

### 進捗更新を含むジョブ実装

```ruby
class BulkProcessingJob < ApplicationJob
  PROGRESS_UPDATE_INTERVAL = 10 # 10件ごとに進捗更新

  def perform(task_id)
    @task = AsyncTask.find(task_id)

    return if @task.cancelled?

    @task.update!(
      status: :processing,
      started_at: Time.current,
      total_items: calculate_total_items
    )

    process_items

    @task.update!(
      status: :completed,
      completed_at: Time.current,
      progress: @task.total_items
    )
    @task.broadcast_status_change

  rescue StandardError => e
    handle_error(e)
    raise
  end

  private

  def calculate_total_items
    # 処理対象の総数を計算
    target_scope.count
  end

  def target_scope
    # パラメータに基づいてスコープを構築
    User.where(@task.params['conditions'] || {})
  end

  def process_items
    processed = 0

    target_scope.find_each do |item|
      # キャンセルチェック
      if should_check_cancellation?(processed)
        @task.reload
        break if @task.cancelled?
      end

      process_single_item(item)
      processed += 1

      update_progress(processed) if should_update_progress?(processed)
    end
  end

  def process_single_item(item)
    # 個別アイテムの処理
    item.do_something!
  end

  def should_check_cancellation?(processed)
    (processed % 100).zero?
  end

  def should_update_progress?(processed)
    (processed % PROGRESS_UPDATE_INTERVAL).zero?
  end

  def update_progress(processed)
    @task.update!(progress: processed)
    @task.broadcast_status_change
  end

  def handle_error(error)
    @task.update!(
      status: :failed,
      completed_at: Time.current,
      last_error: "#{error.class}: #{error.message}"
    )
    @task.broadcast_status_change
  end
end
```

### ActionCableによるリアルタイム通知

```ruby
# app/channels/task_channel.rb
class TaskChannel < ApplicationCable::Channel
  def subscribed
    stream_for current_user
  end

  def unsubscribed
    stop_all_streams
  end

  # クライアントからの進捗確認リクエスト
  def request_status(data)
    task = current_user.async_tasks.find_by(id: data['task_id'])
    return unless task

    transmit(task.status_payload)
  end
end

# app/channels/application_cable/connection.rb
module ApplicationCable
  class Connection < ActionCable::Connection::Base
    identified_by :current_user

    def connect
      self.current_user = find_verified_user
    end

    private

    def find_verified_user
      if (user = User.find_by(id: cookies.encrypted[:user_id]))
        user
      else
        reject_unauthorized_connection
      end
    end
  end
end
```

### ポーリングAPIの実装（ActionCable代替）

```ruby
# app/controllers/api/v1/tasks_controller.rb
module Api
  module V1
    class TasksController < ApplicationController
      before_action :authenticate_user!

      # GET /api/v1/tasks/:id/status
      def status
        task = current_user.async_tasks.find(params[:id])

        render json: {
          id: task.id,
          status: task.status,
          progress: task.progress_percentage,
          estimated_remaining_seconds: task.estimated_remaining_time&.to_i,
          result: task.completed? ? task.result : nil,
          error: task.failed? ? task.last_error : nil,
          started_at: task.started_at&.iso8601,
          completed_at: task.completed_at&.iso8601
        }
      end

      # GET /api/v1/tasks/:id/status/stream (SSE)
      def stream
        task = current_user.async_tasks.find(params[:id])

        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Accel-Buffering'] = 'no'

        sse = SSE.new(response.stream)

        begin
          loop do
            task.reload
            sse.write(task.status_payload, event: 'status')

            break if task.completed? || task.failed? || task.cancelled?

            sleep 1
          end
        rescue ActionController::Live::ClientDisconnected
          # クライアント切断
        ensure
          sse.close
        end
      end
    end
  end
end
```

---

## ジョブの設計パターン

### 冪等性の確保

```ruby
class SendEmailJob < ApplicationJob
  def perform(notification_id)
    notification = Notification.find(notification_id)

    # 冪等性チェック: 既に送信済みなら何もしない
    return if notification.sent?

    # 楽観的ロックで重複実行を防止
    notification.with_lock do
      return if notification.sent?

      EmailService.send(notification)
      notification.update!(sent_at: Time.current)
    end
  end
end

# より堅牢な冪等性の実装
class IdempotentJob < ApplicationJob
  def perform(idempotency_key, **params)
    # 冪等性キーで既に処理済みかチェック
    return if JobExecution.exists?(idempotency_key: idempotency_key)

    ActiveRecord::Base.transaction do
      # ユニーク制約で重複を防止
      execution = JobExecution.create!(
        idempotency_key: idempotency_key,
        job_class: self.class.name,
        started_at: Time.current
      )

      result = execute_job(params)

      execution.update!(
        completed_at: Time.current,
        result: result
      )
    end
  rescue ActiveRecord::RecordNotUnique
    # 既に処理中または処理済み
    Rails.logger.info "Job already executed: #{idempotency_key}"
  end

  private

  def execute_job(params)
    raise NotImplementedError
  end
end
```

### ジョブの分割とチェーン

```ruby
# 大きな処理を小さなジョブに分割
class DataExportCoordinatorJob < ApplicationJob
  def perform(export_id)
    export = DataExport.find(export_id)

    # フェーズ1: データ収集ジョブをエンキュー
    CollectDataJob.perform_later(export_id)
  end
end

class CollectDataJob < ApplicationJob
  def perform(export_id)
    export = DataExport.find(export_id)

    # データ収集処理
    data = collect_data(export)
    export.update!(collected_data: data, phase: :collected)

    # フェーズ2: 変換ジョブをエンキュー
    TransformDataJob.perform_later(export_id)
  end
end

class TransformDataJob < ApplicationJob
  def perform(export_id)
    export = DataExport.find(export_id)

    # データ変換処理
    transformed = transform_data(export.collected_data)
    export.update!(transformed_data: transformed, phase: :transformed)

    # フェーズ3: 出力ジョブをエンキュー
    GenerateOutputJob.perform_later(export_id)
  end
end

class GenerateOutputJob < ApplicationJob
  def perform(export_id)
    export = DataExport.find(export_id)

    # ファイル生成
    file = generate_file(export.transformed_data)
    export.file.attach(io: file, filename: export.filename)
    export.update!(status: :completed, phase: :completed)

    # 完了通知
    ExportNotificationJob.perform_later(export_id)
  end
end
```

### タイムアウト対策

```ruby
class LongRunningJob < ApplicationJob
  # Sidekiq使用時のタイムアウト設定
  sidekiq_options timeout: 30.minutes

  # ジョブ内でのタイムアウト処理
  PROCESSING_TIMEOUT = 25.minutes

  def perform(task_id)
    @task = AsyncTask.find(task_id)
    @start_time = Time.current

    process_with_timeout
  end

  private

  def process_with_timeout
    items_to_process.find_each do |item|
      if timeout_approaching?
        # タイムアウト前に中断し、続きは新しいジョブで処理
        schedule_continuation
        return
      end

      process_item(item)
    end

    complete_task
  end

  def timeout_approaching?
    Time.current - @start_time > PROCESSING_TIMEOUT
  end

  def schedule_continuation
    @task.update!(
      status: :pending,
      last_processed_id: @last_processed_id
    )

    # 続きを処理するジョブをスケジュール
    self.class.perform_later(@task.id)
  end

  def items_to_process
    scope = Item.where(task_id: @task.id)

    if @task.last_processed_id.present?
      scope = scope.where('id > ?', @task.last_processed_id)
    end

    scope.order(:id)
  end

  def process_item(item)
    item.process!
    @last_processed_id = item.id
    @task.increment!(:progress)
  end
end
```

---

## 継続可能なジョブ（Continuable Jobs）

長時間実行されるジョブを途中で中断し、後から続きを再開できる機能について説明します。

### 実現方法の選択

| 方法 | 対応バージョン | 特徴 |
|------|---------------|------|
| ActiveJob::Continuable | Rails 8.1+ | Rails標準機能、stepベースの進捗管理 |
| job-iteration gem | Rails 7.0+ | Shopify製、イテレーションベース、豊富なEnumerator |

### ActiveJob::Continuable（Rails 8.1+）

Rails 8.1で導入された`ActiveJob::Continuable`モジュールは、ジョブの進捗を追跡し、中断後に続きから再開する機能を提供します。

#### 基本的な使い方

```ruby
class DataExportJob < ApplicationJob
  include ActiveJob::Continuable

  def perform(export_id)
    export = Export.find(export_id)

    # ステップ1: データ収集
    step :collect_data do
      export.collect_data!
    end

    # ステップ2: データ変換
    step :transform_data do
      export.transform_data!
    end

    # ステップ3: ファイル生成
    step :generate_file do
      export.generate_file!
    end

    export.mark_completed!
  end
end
```

#### カーソルを使用したイテレーション

大量のレコードを処理する場合、カーソルを使用して進捗を追跡できます。

```ruby
class BulkNotificationJob < ApplicationJob
  include ActiveJob::Continuable

  def perform(notification_batch_id)
    batch = NotificationBatch.find(notification_batch_id)

    # カーソルを使用したステップ
    # 中断時にカーソル位置が保存され、再開時にその位置から処理を継続
    # 注意: オプション名は `start:` （`cursor:` ではない）
    step :send_notifications, start: nil do |cursor|
      users = batch.users.where('id > ?', cursor || 0).order(:id)

      users.find_each do |user|
        send_notification(user)

        # チェックポイント: ここで中断可能
        # queue_adapter.stopping? が true の場合、
        # ActiveJob::Continuation::Interrupt が発生
        # 注意: メソッド名は `checkpoint!` （bang付き）
        checkpoint!(user.id)
      end
    end

    batch.mark_completed!
  end

  private

  def send_notification(user)
    UserMailer.notification(user).deliver_later
  end
end
```

#### 複数のカーソルステップ

```ruby
class DataMigrationJob < ApplicationJob
  include ActiveJob::Continuable

  def perform(migration_id)
    migration = DataMigration.find(migration_id)

    # フェーズ1: ユーザーデータの移行
    step :migrate_users, start: nil do |cursor|
      User.where('id > ?', cursor || 0).find_each do |user|
        migrate_user(user)
        checkpoint!(user.id)
      end
    end

    # フェーズ2: 注文データの移行
    step :migrate_orders, start: nil do |cursor|
      Order.where('id > ?', cursor || 0).find_each do |order|
        migrate_order(order)
        checkpoint!(order.id)
      end
    end

    # フェーズ3: クリーンアップ
    step :cleanup do
      migration.cleanup_legacy_data!
    end
  end
end
```

#### メソッド参照によるステップ定義

```ruby
class ComplexProcessingJob < ApplicationJob
  include ActiveJob::Continuable

  def perform(task_id)
    @task = Task.find(task_id)

    # メソッド名でステップを定義
    step :validate_input
    step :process_data, start: nil
    step :finalize
  end

  private

  def validate_input
    @task.validate_input!
  end

  # カーソルを受け取るメソッド
  def process_data(cursor)
    @task.items.where('id > ?', cursor || 0).find_each do |item|
      item.process!
      checkpoint!(item.id)
    end
  end

  def finalize
    @task.finalize!
  end
end
```

#### キューアダプターの対応状況

`ActiveJob::Continuable`は、キューアダプターの`stopping?`メソッドを呼び出して中断タイミングを判断します。

| アダプター | 対応状況 |
|-----------|---------|
| Sidekiq | ✅ 対応済み |
| Solid Queue | ✅ 対応済み |
| Test | ✅ 対応済み |
| その他 | デフォルトで`false`を返す（要カスタム実装） |

### job-iteration gem

Shopifyが開発した[job-iteration](https://github.com/Shopify/job-iteration)は、Rails 7.0以降で利用可能な成熟したライブラリです。

#### インストール

```ruby
# Gemfile
gem 'job-iteration'
```

#### 基本的な使い方

```ruby
class NotifyUsersJob < ApplicationJob
  include JobIteration::Iteration

  # イテレート対象のEnumeratorを構築
  def build_enumerator(cursor:)
    enumerator_builder.active_record_on_records(
      User.all,
      cursor: cursor
    )
  end

  # 各イテレーションで実行される処理
  def each_iteration(user)
    user.notify_about_something
  end
end
```

#### 利用可能なEnumerator

```ruby
class BatchProcessingJob < ApplicationJob
  include JobIteration::Iteration

  # 1. 個別レコードのイテレーション
  def build_enumerator(cursor:)
    enumerator_builder.active_record_on_records(
      Product.where(status: :pending),
      cursor: cursor
    )
  end

  # 2. バッチ（配列）でのイテレーション
  def build_enumerator(cursor:)
    enumerator_builder.active_record_on_batches(
      Comment.where(spam: nil),
      cursor: cursor,
      batch_size: 100
    )
  end

  # 3. バッチ（Relation）でのイテレーション
  # update_all などの一括操作に便利
  def build_enumerator(cursor:)
    enumerator_builder.active_record_on_batch_relations(
      User.inactive,
      cursor: cursor,
      batch_size: 500
    )
  end

  # 4. 配列のイテレーション
  def build_enumerator(cursor:)
    enumerator_builder.array(
      ['task1', 'task2', 'task3'],
      cursor: cursor
    )
  end

  # 5. CSVファイルのイテレーション
  def build_enumerator(import, cursor:)
    enumerator_builder.csv(
      import.csv_file,
      cursor: cursor
    )
  end
end
```

#### 引数付きジョブ

```ruby
class ProcessCommentsJob < ApplicationJob
  include JobIteration::Iteration

  # performの引数がbuild_enumeratorとeach_iterationの両方に渡される
  def build_enumerator(product_id, cursor:)
    enumerator_builder.active_record_on_batches(
      Comment.where(product_id: product_id),
      cursor: cursor,
      batch_size: 100
    )
  end

  def each_iteration(batch, product_id)
    # batchは配列として渡される
    CommentProcessor.process_batch(batch.map(&:id), product_id)
  end
end

# 使用方法
ProcessCommentsJob.perform_later(product.id)
```

#### ネストしたイテレーション

```ruby
class ProcessCategoriesJob < ApplicationJob
  include JobIteration::Iteration

  def build_enumerator(cursor:)
    enumerator_builder.nested(
      # 外側: カテゴリのイテレーション
      -> (cursor) {
        enumerator_builder.active_record_on_records(
          Category.all,
          cursor: cursor
        )
      },
      # 内側: 各カテゴリの商品のイテレーション
      -> (category, cursor) {
        enumerator_builder.active_record_on_records(
          category.products,
          cursor: cursor
        )
      }
    )
  end

  def each_iteration(product)
    product.reindex!
  end
end
```

#### スロットリングとタイムアウト

```ruby
# config/initializers/job_iteration.rb

# 最大実行時間（この時間を超えると中断してリエンキュー）
JobIteration.max_job_runtime = 5.minutes

# 中断チェックの間隔
JobIteration.interruption_check_interval = 1.second

# カスタム中断条件
JobIteration.interruption = -> {
  # メモリ使用量が高い場合に中断
  memory_usage > 500.megabytes
}
```

#### コールバック

```ruby
class ImportJob < ApplicationJob
  include JobIteration::Iteration

  # ジョブ開始時
  def on_start
    @import = Import.find(arguments.first)
    @import.update!(status: :processing, started_at: Time.current)
  end

  # 各イテレーション完了時
  def on_iteration
    @import.increment!(:processed_count)
  end

  # ジョブ中断時（リエンキュー前）
  def on_shutdown
    @import.update!(status: :paused)
  end

  # ジョブ完了時
  def on_complete
    @import.update!(status: :completed, completed_at: Time.current)
  end

  def build_enumerator(import_id, cursor:)
    enumerator_builder.active_record_on_records(
      ImportRow.where(import_id: import_id),
      cursor: cursor
    )
  end

  def each_iteration(row)
    row.process!
  end
end
```

#### Sidekiqの設定

```ruby
# config/sidekiq.yml
# job-iterationを使用する場合、タイムアウトを長めに設定
:timeout: 30  # デフォルトの8秒から30秒に変更
```

### ActiveJob::Continuable vs job-iteration の比較

| 観点 | ActiveJob::Continuable | job-iteration |
|------|----------------------|---------------|
| 対応Rails | 8.1+ | 7.0+ |
| アプローチ | ステップベース | イテレーションベース |
| カーソル管理 | 手動（checkpoint呼び出し） | 自動（Enumerator） |
| 中断タイミング | checkpoint時 | 各イテレーション終了時 |
| Enumerator | なし | 豊富（AR, CSV, Array等） |
| ネスト対応 | 手動実装 | 組み込みサポート |
| 成熟度 | 新機能 | 本番実績多数（Shopify） |

### 選択の指針

```ruby
# ActiveJob::Continuable が適している場合:
# - Rails 8.1以降を使用している
# - フェーズ（ステップ）が明確に分かれている処理
# - 外部依存を最小限にしたい

# job-iteration が適している場合:
# - Rails 7.x を使用している
# - 大量レコードのイテレーション処理
# - CSVインポートなど、様々なデータソースを扱う
# - 成熟したライブラリを使いたい
```

---

## テスト戦略

### ジョブのユニットテスト

```ruby
# spec/jobs/process_order_job_spec.rb
require 'rails_helper'

RSpec.describe ProcessOrderJob, type: :job do
  describe '#perform' do
    let(:order) { create(:order, status: :pending) }

    context '正常系' do
      it 'オーダーを処理する' do
        expect {
          described_class.perform_now(order.id)
        }.to change { order.reload.status }.from('pending').to('processed')
      end

      it 'ジョブがキューに追加される' do
        expect {
          described_class.perform_later(order.id)
        }.to have_enqueued_job(described_class).with(order.id)
      end
    end

    context 'オーダーが存在しない場合' do
      it '例外を発生させずに終了する' do
        expect {
          described_class.perform_now(-1)
        }.not_to raise_error
      end
    end

    context 'リトライ可能なエラーが発生した場合' do
      before do
        allow_any_instance_of(Order).to receive(:process!).and_raise(Net::OpenTimeout)
      end

      it 'リトライが設定される' do
        expect {
          described_class.perform_now(order.id)
        }.to raise_error(Net::OpenTimeout)

        # リトライ設定の確認
        expect(described_class.new.retry_on?(Net::OpenTimeout.new)).to be true
      end
    end
  end
end
```

### 進捗更新のテスト

```ruby
# spec/jobs/bulk_processing_job_spec.rb
require 'rails_helper'

RSpec.describe BulkProcessingJob, type: :job do
  let(:user) { create(:user) }
  let(:task) { create(:async_task, user: user, task_type: 'bulk_process') }

  describe '進捗更新' do
    before do
      create_list(:item, 25, task: task)
    end

    it '進捗が更新される' do
      expect {
        described_class.perform_now(task.id)
      }.to change { task.reload.progress }.from(0).to(25)
    end

    it 'ActionCableでブロードキャストされる' do
      expect(TaskChannel).to receive(:broadcast_to).at_least(:once)

      described_class.perform_now(task.id)
    end
  end

  describe 'キャンセル処理' do
    before do
      create_list(:item, 100, task: task)
    end

    it 'キャンセルされた場合は処理を中断する' do
      # 処理中にキャンセル
      allow_any_instance_of(AsyncTask).to receive(:cancelled?).and_return(false, false, true)

      described_class.perform_now(task.id)

      # 全件処理されていないことを確認
      expect(task.reload.progress).to be < 100
    end
  end
end
```

### 統合テスト

```ruby
# spec/features/async_task_spec.rb
require 'rails_helper'

RSpec.describe 'AsyncTask', type: :feature do
  include ActiveJob::TestHelper

  let(:user) { create(:user) }

  before do
    sign_in user
  end

  describe 'タスクの作成から完了まで' do
    it 'タスクが正常に完了する', :js do
      visit new_task_path

      fill_in 'Task name', with: 'Test Task'
      click_button 'Start'

      # ジョブが実行されるのを待つ
      perform_enqueued_jobs

      # 完了を確認
      expect(page).to have_content('Completed')
    end
  end
end
```

---

## その他のベストプラクティス

### ログ出力

```ruby
class LoggedJob < ApplicationJob
  around_perform do |job, block|
    job_info = {
      job_class: job.class.name,
      job_id: job.job_id,
      arguments: sanitize_arguments(job.arguments),
      queue: job.queue_name
    }

    Rails.logger.info({ event: 'job_started', **job_info }.to_json)
    start_time = Time.current

    begin
      block.call

      Rails.logger.info({
        event: 'job_completed',
        duration_ms: ((Time.current - start_time) * 1000).round,
        **job_info
      }.to_json)

    rescue StandardError => e
      Rails.logger.error({
        event: 'job_failed',
        error_class: e.class.name,
        error_message: e.message,
        duration_ms: ((Time.current - start_time) * 1000).round,
        **job_info
      }.to_json)

      raise
    end
  end

  private

  def sanitize_arguments(arguments)
    # センシティブ情報をフィルタリング
    arguments.map do |arg|
      case arg
      when Hash
        arg.except(:password, :token, :secret)
      else
        arg
      end
    end
  end
end
```

### メトリクス収集

```ruby
# app/jobs/concerns/metrics_tracking.rb
module MetricsTracking
  extend ActiveSupport::Concern

  included do
    around_perform :track_metrics
  end

  private

  def track_metrics
    start_time = Process.clock_gettime(Process::CLOCK_MONOTONIC)

    yield

    duration = Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time

    # メトリクス送信（Datadog, Prometheus等）
    StatsD.measure("jobs.#{self.class.name.underscore}.duration", duration)
    StatsD.increment("jobs.#{self.class.name.underscore}.success")

  rescue StandardError => e
    StatsD.increment("jobs.#{self.class.name.underscore}.failure")
    raise
  end
end

# 使用方法
class MyJob < ApplicationJob
  include MetricsTracking

  def perform(...)
    # ...
  end
end
```

### キューの優先度設定

```ruby
# app/jobs/application_job.rb
class ApplicationJob < ActiveJob::Base
  # デフォルトキュー
  queue_as :default
end

# 優先度の高いジョブ
class UrgentNotificationJob < ApplicationJob
  queue_as :critical
end

# バックグラウンドで実行する重い処理
class DataExportJob < ApplicationJob
  queue_as :low_priority
end

# config/sidekiq.yml
:queues:
  - [critical, 10]
  - [default, 5]
  - [low_priority, 1]
```

### スロットリング

```ruby
class RateLimitedJob < ApplicationJob
  RATE_LIMIT_KEY = 'api_calls'
  RATE_LIMIT = 100 # 1分あたり100回

  def perform(request_id)
    wait_for_rate_limit

    # API呼び出し
    make_api_call(request_id)
  end

  private

  def wait_for_rate_limit
    loop do
      current_count = Redis.current.get(RATE_LIMIT_KEY).to_i

      if current_count < RATE_LIMIT
        Redis.current.multi do |r|
          r.incr(RATE_LIMIT_KEY)
          r.expire(RATE_LIMIT_KEY, 60)
        end
        return
      end

      # レート制限に達している場合は待機
      sleep 1
    end
  end
end
```

---

## 参照

- [Active Job Basics - Rails Guides](https://guides.rubyonrails.org/active_job_basics.html)
- [ActiveJob::Continuable - Rails Edge API](https://edgeapi.rubyonrails.org/classes/ActiveJob/Continuable.html)
- [Rails 8.1 Release Notes](https://rubyonrails.org/2025/10/22/rails-8-1)
- [job-iteration - GitHub](https://github.com/Shopify/job-iteration)
- [job-iteration Best Practices](https://github.com/Shopify/job-iteration/blob/main/guides/best-practices.md)
- [Sidekiq Best Practices](https://github.com/sidekiq/sidekiq/wiki/Best-Practices)
- [Solid Queue](https://github.com/rails/solid_queue)
