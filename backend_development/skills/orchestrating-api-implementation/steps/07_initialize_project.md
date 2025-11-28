# ステップ7: プロジェクトを初期化する

## 目次

- [目的](#目的)
- [開発環境](#開発環境)
- [方式A: Docker環境でのセットアップ（推奨）](#方式a-docker環境でのセットアップ推奨)
  - [A.0 空のプロジェクトからのセットアップ](#a0-空のプロジェクトからのセットアップ)
  - [A.1 既存のRailsプロジェクトのセットアップ](#a1-既存のrailsプロジェクトのセットアップ)
  - [A.2 Gemを追加する](#a2-gemを追加する)
  - [A.3 データベースを設定する](#a3-データベースを設定する)
  - [A.4 API設定を行う](#a4-api設定を行う)
- [方式B: ローカル環境でのセットアップ](#方式b-ローカル環境でのセットアップ)
- [出力](#出力)

---

## 目的

Rails 8.1プロジェクトを作成し、必要な設定とGemをセットアップする。

## 開発環境

このスキルでは**Docker Compose環境**を標準として使用する。

> **重要**: ステップ2で作成したDockerfile/docker-compose.ymlを使用してプロジェクトを初期化する。

---

## 方式A: Docker環境でのセットアップ（推奨）

### A.0 空のプロジェクトからのセットアップ

**Gemfile/Gemfile.lockが存在しない新規プロジェクトの場合**、以下の手順で初期化する：

#### 1. 最小限のGemfileを作成する

```ruby
# Gemfile
source "https://rubygems.org"

gem "rails", "~> 8.1"
```

#### 2. 空のGemfile.lockを作成する

```bash
touch Gemfile.lock
```

#### 3. Dockerイメージをビルドする

```bash
docker compose build
```

#### 4. bundle installを実行する

```bash
docker compose run --rm web bundle install
```

#### 5. rails newを実行する

```bash
# 管理画面を含む場合（推奨）
docker compose run --rm web bundle exec rails new . \
  --database=postgresql \
  --skip-test \
  --css=tailwind \
  --force

# APIのみの場合
docker compose run --rm web bundle exec rails new . \
  --api \
  --database=postgresql \
  --skip-test \
  --force
```

#### 6. ファイル権限を修正する（必要な場合）

```bash
# rootで作成されたファイルの権限を修正
sudo chown -R $(id -u):$(id -g) .
```

#### 7. 再度bundle installを実行する

```bash
docker compose run --rm web bundle install
```

#### 8. データベースを作成する

```bash
docker compose run --rm web bundle exec rails db:create
```

---

### A.1 Dockerfile.devを作成する（推奨）

`vendor/bundle`をローカルに配置することで、ファイル権限問題を完全に回避する方式：

```dockerfile
# Dockerfile.dev
FROM ruby:3.4-slim

# 必要なパッケージをインストール
# 重要: libyaml-dev はpsychゲムのビルドに必須
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    build-essential \
    git \
    libpq-dev \
    libyaml-dev \
    pkg-config \
    nodejs \
    npm \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# yarnをインストール（Tailwind CSS等で必要）
RUN npm install -g yarn

# 作業ディレクトリを設定
WORKDIR /app

# bundlerの設定（ローカルvendor/bundleを使用）
# これにより、gemがプロジェクト内に保存され、権限問題を回避
ENV BUNDLE_PATH=/app/vendor/bundle
ENV BUNDLE_BIN=/app/vendor/bundle/bin
ENV PATH="${BUNDLE_BIN}:${PATH}"

EXPOSE 3000

CMD ["bash", "-c", "rm -f tmp/pids/server.pid && bundle exec rails server -b 0.0.0.0"]
```

**利点**:
- UID/GIDの設定が不要
- gemがプロジェクト内に保存され、ホストからも参照可能
- `.gitignore`に`vendor/bundle`を追加して管理

### A.2 docker-compose.ymlを作成する

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: app_development
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      # ポート5432が既に使用されている場合は5433等に変更
      - "${DB_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: bash -c "rm -f tmp/pids/server.pid && bundle exec rails server -b 0.0.0.0"
    volumes:
      - .:/app
    ports:
      - "3000:3000"
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://postgres:password@db:5432/app_development
      RAILS_ENV: development
    tty: true
    stdin_open: true

volumes:
  postgres_data:
```

### A.3 ポート衝突への対応

PostgreSQLのデフォルトポート5432が既に使用されている場合：

```bash
# .envファイルでポートを変更
echo "DB_PORT=5433" >> .env
```

または、docker-compose.ymlで直接指定：
```yaml
ports:
  - "5433:5432"
```

### A.4 .gitignoreの設定

```gitignore
# vendor/bundleをGit管理から除外
/vendor/bundle

# その他Docker関連
.env
```

### A.5 既存ファイルの権限を修正

既にrootで作成されたファイルがある場合：

```bash
# ホスト側で権限を変更
sudo chown -R $(id -u):$(id -g) .

# または、コンテナ内でrootとして実行
docker compose exec -u root web chown -R 1000:1000 /app
```

### A.4 Dockerでプロジェクトを作成する

```bash
# イメージをビルド
docker compose build

# Railsプロジェクトを生成（管理画面を含む場合）
docker compose run --rm web rails new . \
  --database=postgresql \
  --skip-test \
  --css=tailwind \
  --force

# APIのみの場合
docker compose run --rm web rails new . \
  --api \
  --database=postgresql \
  --skip-test \
  --force

# コンテナを起動
docker compose up -d

# DBを作成
docker compose exec web rails db:create
```

### A.5 Docker開発での注意点

| 項目 | コマンド |
|------|---------|
| railsコマンド実行 | `docker compose exec web rails ...` |
| bundleコマンド | `docker compose exec web bundle ...` |
| コンソール | `docker compose exec web rails console` |
| ログ確認 | `docker compose logs -f web` |
| コンテナ再起動 | `docker compose restart web` |

---

## 方式B: ローカル環境でのセットアップ

### B.1 Railsプロジェクトを作成する

```bash
rails new project_name \
  --api \
  --database=postgresql \
  --skip-test \
  --skip-action-mailbox \
  --skip-action-text \
  --skip-active-storage \
  --skip-action-cable
```

#### オプション説明

| オプション | 説明 |
|-----------|------|
| `--api` | APIモードで作成（View関連を除外） |
| `--database=postgresql` | PostgreSQLを使用 |
| `--skip-test` | デフォルトのテストをスキップ（RSpecを使用） |
| その他skip | 不要な機能を除外 |

#### 管理画面を含める場合（通常モード）

```bash
rails new project_name \
  --database=postgresql \
  --skip-test \
  --css=tailwind
```

**注意**: 通常モード（`--api`なし）で作成した場合、APIコントローラでCSRF保護を無効化する必要がある。詳細はステップ10参照。

---

## 共通設定（Docker/ローカル共通）

### 6.2 Gemfileを編集する

```ruby
# Gemfile

# API
gem 'alba'                  # JSONシリアライザ
gem 'kaminari'              # ページネーション
gem 'ransack'               # 検索・フィルタリング
gem 'rack-cors'             # CORS対応

# 管理画面（ActiveAdminを使用する場合）
gem 'activeadmin'
gem 'devise'
gem 'dartsass-rails'        # ActiveAdminがSassに依存

group :development, :test do
  gem 'rspec-rails'         # テストフレームワーク
  gem 'factory_bot_rails'   # テストデータ生成
  gem 'faker'               # ダミーデータ生成
  gem 'rubocop-rails-omakase', require: false  # Linter
end

group :development do
  gem 'annotate'            # モデルにスキーマ情報追加
end
```

**注意**: ActiveAdminはSassコンパイラを必要とするため、`dartsass-rails`を追加する。

### 6.3 Gemをインストールする

```bash
bundle install
```

### 6.4 RSpecをセットアップする

```bash
rails generate rspec:install
```

### 6.5 データベースを作成する

`config/database.yml` を確認し、必要に応じて編集：

```yaml
default: &default
  adapter: postgresql
  encoding: unicode
  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 5 } %>

development:
  <<: *default
  database: project_name_development

test:
  <<: *default
  database: project_name_test

production:
  <<: *default
  database: project_name_production
  username: project_name
  password: <%= ENV["PROJECT_NAME_DATABASE_PASSWORD"] %>
```

```bash
rails db:create
```

### 6.6 CORSを設定する（API利用時）

`config/initializers/cors.rb`:

```ruby
Rails.application.config.middleware.insert_before 0, Rack::Cors do
  allow do
    origins '*'  # 本番環境では適切に制限する

    resource '*',
      headers: :any,
      methods: [:get, :post, :put, :patch, :delete, :options, :head]
  end
end
```

### 6.7 ディレクトリ構成を確認する

```
app/
├── controllers/
│   └── api/
│       └── v1/           # APIバージョニング
├── models/
├── serializers/          # Alba用（作成）
└── views/                # 管理画面用（必要な場合）
config/
db/
spec/
```

APIバージョニング用のディレクトリを作成：

```bash
mkdir -p app/controllers/api/v1
mkdir -p app/serializers
```

### 6.8 ベースコントローラを作成する

`app/controllers/api/v1/base_controller.rb`:

```ruby
module Api
  module V1
    class BaseController < ApplicationController
      include Pagy::Backend

      rescue_from ActiveRecord::RecordNotFound, with: :not_found
      rescue_from ActiveRecord::RecordInvalid, with: :unprocessable_entity

      private

      def not_found
        render json: { error: 'Not Found' }, status: :not_found
      end

      def unprocessable_entity(exception)
        render json: { errors: exception.record.errors }, status: :unprocessable_entity
      end
    end
  end
end
```

### 6.9 ルーティングの基本設定

`config/routes.rb`:

```ruby
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      # リソースはここに追加
    end
  end
end
```

## 出力

- Railsプロジェクトが作成され、起動可能な状態
- `rails server` でサーバーが起動することを確認
