# Solid Cable リファレンス

Solid Cableは、Rails 8で導入されたActionCableのデータベースバックエンドです。Redisなしでリアルタイム通信を実現できます。

## 目次

1. [概要と特徴](#概要と特徴)
2. [セットアップ](#セットアップ)
3. [ActionCableとの違い](#actioncableとの違い)
4. [設定オプション](#設定オプション)
5. [環境分離](#環境分離)
6. [パフォーマンス最適化](#パフォーマンス最適化)
7. [トラブルシューティング](#トラブルシューティング)

---

## 概要と特徴

### Solid Cableとは

Solid Cableは、ActionCableのメッセージをRedisの代わりにデータベース（MySQL/PostgreSQL/SQLite）に保存してポーリングで配信する仕組みです。

### メリット

- **追加インフラ不要**: Redisサーバーが不要
- **シンプルな運用**: データベースのみで完結
- **コスト削減**: 小〜中規模アプリでのインフラコスト削減
- **Rails 8標準**: デフォルトで利用可能

### デメリット

- **レイテンシー**: Redisより若干遅い（ポーリング間隔依存）
- **スケーラビリティ**: 大規模な場合はRedisが推奨
- **DBへの負荷**: メッセージ量が多いとDBに負荷

### 推奨ユースケース

| ユースケース | Solid Cable | Redis |
|-------------|-------------|-------|
| 小〜中規模アプリ | ✅ 推奨 | ◯ |
| 進捗通知（低頻度） | ✅ 推奨 | ◯ |
| チャット（高頻度） | △ | ✅ 推奨 |
| 大規模（1000+同時接続） | △ | ✅ 推奨 |
| インフラ簡素化優先 | ✅ 推奨 | - |

---

## セットアップ

### 1. Gemのインストール

```ruby
# Gemfile
gem 'solid_cable'
```

```bash
bundle install
```

### 2. マイグレーションの生成と実行

```bash
# マイグレーションファイルの生成
bin/rails solid_cable:install:migrations

# マイグレーション実行
bin/rails db:migrate
```

生成されるテーブル:

```ruby
# db/migrate/xxx_create_solid_cable_messages.rb
class CreateSolidCableMessages < ActiveRecord::Migration[7.1]
  def change
    create_table :solid_cable_messages do |t|
      t.text :channel, null: false
      t.text :payload, null: false, limit: 536870912  # 512MB
      t.datetime :created_at, null: false

      t.index :channel
      t.index :created_at
    end
  end
end
```

### 3. cable.ymlの設定

```yaml
# config/cable.yml
development:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.day

test:
  adapter: test

production:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour
```

### 4. 既存のActionCableコードはそのまま使用可能

```ruby
# app/channels/task_status_channel.rb
class TaskStatusChannel < ApplicationCable::Channel
  def subscribed
    task = AsyncTask.find(params[:task_id])
    stream_for task
  end

  def unsubscribed
    stop_all_streams
  end
end

# ブロードキャスト（変更なし）
TaskStatusChannel.broadcast_to(task, {
  status: 'processing',
  progress: 50
})
```

---

## ActionCableとの違い

### アーキテクチャの違い

| 項目 | ActionCable (Redis) | Solid Cable |
|------|---------------------|-------------|
| メッセージ保存 | Redis Pub/Sub | データベーステーブル |
| 配信方式 | Pub/Sub（プッシュ） | ポーリング |
| 接続維持 | WebSocket | WebSocket + ポーリング |
| スケールアウト | Redis経由で共有 | DB経由で共有 |

### コードの違い

**ActionCable（Redis）の場合:**

```yaml
# config/cable.yml
production:
  adapter: redis
  url: <%= ENV.fetch("REDIS_URL") { "redis://localhost:6379/1" } %>
  channel_prefix: my_app_production
```

**Solid Cableの場合:**

```yaml
# config/cable.yml
production:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour
```

### チャンネル実装（共通）

ActionCableとSolid Cableでチャンネルの実装は変わりません:

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
      if (user = User.find_by(id: cookies.encrypted[:user_id]))
        user
      else
        reject_unauthorized_connection
      end
    end
  end
end

# app/channels/task_status_channel.rb
class TaskStatusChannel < ApplicationCable::Channel
  def subscribed
    task = current_user.async_tasks.find_by(id: params[:task_id])

    if task
      stream_for task
    else
      reject
    end
  end

  def unsubscribed
    stop_all_streams
  end
end
```

---

## 設定オプション

### cable.ymlの全オプション

```yaml
# config/cable.yml
production:
  adapter: solid_cable

  # ポーリング間隔（デフォルト: 0.1秒）
  # 小さいほどリアルタイム性が高いが、DBへの負荷増加
  polling_interval: 0.1.seconds

  # メッセージ保持期間（デフォルト: 1日）
  # 古いメッセージは自動削除される
  message_retention: 1.hour

  # チャンネルプレフィックス（環境分離用）
  channel_prefix: production

  # 接続設定（DB分離時）
  connects_to:
    database:
      writing: cable
      reading: cable
```

### 別データベースを使用する場合

```yaml
# config/database.yml
production:
  primary:
    <<: *default
    database: my_app_production

  cable:
    <<: *default
    database: my_app_cable_production
    migrations_paths: db/cable_migrate

# config/cable.yml
production:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour
  connects_to:
    database:
      writing: cable
```

---

## 環境分離

### ステージング/本番でDBを共有する場合

同じデータベースをステージング環境と本番環境で共有している場合、channel_prefixを使用して環境を分離します。

```yaml
# config/cable.yml
staging:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour
  channel_prefix: <%= ENV.fetch('CABLE_PREFIX', 'staging') %>

production:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour
  channel_prefix: <%= ENV.fetch('CABLE_PREFIX', 'production') %>
```

```bash
# 環境変数
# staging
CABLE_PREFIX=staging

# production
CABLE_PREFIX=production
```

### channel_prefixの動作

channel_prefixを設定すると、実際のチャンネル名にプレフィックスが付加されます:

```ruby
# channel_prefix: production の場合

# ブロードキャスト時
TaskStatusChannel.broadcast_to(task, data)
# → 実際のチャンネル: "production:task_status_channel:Z2lkOi8v..."

# stream_for時
stream_for task
# → "production:task_status_channel:Z2lkOi8v..." をリッスン
```

これにより、同じDBを参照していても環境間でメッセージが混在しません。

---

## パフォーマンス最適化

### ポーリング間隔の調整

用途に応じてポーリング間隔を調整します:

```yaml
# 高いリアルタイム性が必要な場合
polling_interval: 0.05.seconds  # 50ms

# 通常の進捗通知
polling_interval: 0.1.seconds   # 100ms（推奨）

# 低頻度の通知
polling_interval: 0.5.seconds   # 500ms
```

### メッセージ保持期間の最適化

```yaml
# 短期間のみ必要な場合（進捗通知など）
message_retention: 1.hour

# ある程度の再接続に対応
message_retention: 6.hours

# 長期保持（チャット履歴など）
message_retention: 7.days
```

### インデックスの追加

大量のメッセージがある場合、追加のインデックスが有効な場合があります:

```ruby
# db/migrate/xxx_add_index_to_solid_cable_messages.rb
class AddIndexToSolidCableMessages < ActiveRecord::Migration[7.1]
  def change
    # チャンネルと作成日時の複合インデックス
    add_index :solid_cable_messages, [:channel, :created_at]
  end
end
```

### 古いメッセージの手動削除

デフォルトでは自動削除されますが、手動で削除することも可能です:

```ruby
# lib/tasks/solid_cable.rake
namespace :solid_cable do
  desc "Clean up old messages"
  task cleanup: :environment do
    retention = ENV.fetch('MESSAGE_RETENTION', '1').to_i.hours
    deleted = SolidCable::Message.where('created_at < ?', retention.ago).delete_all
    puts "Deleted #{deleted} old messages"
  end
end
```

---

## トラブルシューティング

### メッセージが届かない場合

1. **cable.ymlの設定確認**

```bash
# Rails consoleで確認
Rails.application.config.action_cable.cable
# => {"adapter"=>"solid_cable", "polling_interval"=>0.1, ...}
```

2. **テーブルの存在確認**

```bash
bin/rails db:migrate:status | grep solid_cable
```

3. **メッセージの確認**

```ruby
# Rails consoleでメッセージを確認
SolidCable::Message.order(created_at: :desc).limit(10)
```

4. **ブロードキャストのテスト**

```ruby
# Rails consoleでテスト送信
TaskStatusChannel.broadcast_to(
  AsyncTask.first,
  { test: true, timestamp: Time.current }
)

# メッセージが保存されたか確認
SolidCable::Message.last
```

### 接続が不安定な場合

1. **ポーリング間隔の確認**

```yaml
# 間隔が長すぎると不安定に感じる
polling_interval: 0.1.seconds  # 推奨
```

2. **WebSocket接続の確認**

ブラウザのDevToolsでWebSocket接続を確認:

```
Network → WS → cable → Messages
```

3. **サーバーログの確認**

```bash
# ActionCableの接続ログ
tail -f log/production.log | grep -i cable
```

### DBへの負荷が高い場合

1. **メッセージ保持期間を短くする**

```yaml
message_retention: 30.minutes
```

2. **ポーリング間隔を長くする**

```yaml
polling_interval: 0.5.seconds
```

3. **別DBへの分離を検討**

```yaml
# config/database.yml
production:
  cable:
    <<: *default
    database: my_app_cable_production
```

4. **Redisへの移行を検討**

負荷が高い場合は、Redisバックエンドへの移行を検討してください。

### ActionCableからの移行

1. **Gemfileの更新**

```ruby
# 追加
gem 'solid_cable'

# 削除可能（Solid Cableのみ使用する場合）
# gem 'redis'
```

2. **cable.ymlの更新**

```yaml
# Before (Redis)
production:
  adapter: redis
  url: <%= ENV.fetch("REDIS_URL") %>

# After (Solid Cable)
production:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.hour
```

3. **マイグレーションの実行**

```bash
bin/rails solid_cable:install:migrations
bin/rails db:migrate
```

4. **チャンネルコードは変更不要**

既存のチャンネル実装はそのまま動作します。

---

## 参照

- [Solid Cable GitHub](https://github.com/rails/solid_cable)
- [Rails ActionCable Guide](https://guides.rubyonrails.org/action_cable_overview.html)
- [Rails 8 Release Notes](https://rubyonrails.org/blog/2024/11/07/rails-8-0-available-today)
