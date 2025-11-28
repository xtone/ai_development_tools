# ステップ2: 技術スタックを決定する

## 目次

- [技術スタック（固定）](#技術スタック固定)
  - [バックエンド](#バックエンド)
  - [データベース](#データベース)
  - [開発環境](#開発環境)
  - [管理画面](#管理画面)
- [手順](#手順)
  - [2.1 Docker Compose環境を構築する](#21-docker-compose環境を構築する)
  - [2.2 Docker環境を起動・確認する](#22-docker環境を起動確認する)
  - [2.3 よく使うDockerコマンド](#23-よく使うdockerコマンド)
  - [2.4 Docker環境のトラブルシューティング](#24-docker環境のトラブルシューティング)
  - [2.5 管理画面の方式を決定する](#25-管理画面の方式を決定する)
  - [2.6 追加Gemを検討する](#26-追加gemを検討する)
- [出力](#出力)

---

## 技術スタック（固定）

このスキルでは以下の技術スタックを使用する。

### バックエンド

| 項目 | 技術 |
|------|------|
| 言語 | Ruby 3.4 |
| フレームワーク | Ruby on Rails 8.1 |
| APIモード | Rails API mode |

### データベース

| 項目 | 技術 |
|------|------|
| RDBMS | PostgreSQL 18 |
| マイグレーション | Active Record Migrations |
| ORM | Active Record |

### 開発環境

| 項目 | 技術 |
|------|------|
| コンテナ | Docker + Docker Compose |
| Ruby環境 | Dockerコンテナ内 |
| DB環境 | PostgreSQLコンテナ |

### 管理画面

| 項目 | 技術 |
|------|------|
| 方式 | Rails一体型 または 別アプリ |
| UIライブラリ | ユーザーの希望に応じて選定 |

## 手順

### 2.1 Docker Compose環境を構築する

#### 2.1.1 Dockerfileを作成する

`Dockerfile`:

```dockerfile
FROM ruby:3.4-slim

# 必要なパッケージをインストール
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# Bundlerの設定
ENV BUNDLE_PATH=/usr/local/bundle
ENV BUNDLE_JOBS=4

# GemfileとGemfile.lockをコピー
COPY Gemfile Gemfile.lock ./

# Gemをインストール
RUN bundle install

# アプリケーションのソースをコピー
COPY . .

# ポートを公開
EXPOSE 3000

# デフォルトのコマンド
CMD ["rails", "server", "-b", "0.0.0.0"]
```

#### 2.1.2 docker-compose.ymlを作成する

`docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app_development
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: bash -c "rm -f tmp/pids/server.pid && bundle exec rails server -b '0.0.0.0'"
    volumes:
      - .:/app
      - bundle_data:/usr/local/bundle
    ports:
      - "3000:3000"
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://postgres:postgres@db:5432/app_development
      RAILS_ENV: development
    stdin_open: true
    tty: true

volumes:
  postgres_data:
  bundle_data:
```

#### 2.1.3 開発用の.env.exampleを作成する

`.env.example`:

```bash
# Database
DATABASE_URL=postgres://postgres:postgres@db:5432/app_development
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Rails
RAILS_ENV=development
RAILS_MASTER_KEY=your_master_key_here
```

#### 2.1.4 .dockerignoreを作成する

`.dockerignore`:

```
.git
.gitignore
log/*
tmp/*
storage/*
.docker-compose*
Dockerfile*
README.md
.env*
node_modules
```

### 2.2 Docker環境を起動・確認する

```bash
# イメージをビルド
docker compose build

# コンテナを起動
docker compose up -d

# バージョンを確認
docker compose exec web ruby -v    # 3.4.x であること
docker compose exec web rails -v   # 8.1.x であること
docker compose exec db psql --version  # 18.x であること

# ログを確認
docker compose logs -f web
```

### 2.3 よく使うDockerコマンド

```bash
# Railsコマンドを実行
docker compose exec web rails db:create
docker compose exec web rails db:migrate
docker compose exec web rails console

# Bundleコマンドを実行
docker compose exec web bundle install
docker compose exec web bundle update

# テストを実行
docker compose exec web rspec

# コンテナを停止
docker compose down

# ボリュームも含めて削除（データベースもリセット）
docker compose down -v
```

### 2.4 Docker環境のトラブルシューティング

#### 2.4.1 ポート競合エラー

**エラー**: `Bind for 0.0.0.0:5432 failed: port is already allocated`

ホストでPostgreSQLが既に起動している場合に発生する。

**解決方法1**: ホストのPostgreSQLを停止

```bash
# Ubuntu/Debian
sudo systemctl stop postgresql

# macOS (Homebrew)
brew services stop postgresql
```

**解決方法2**: docker-compose.ymlのポートを変更

```yaml
services:
  db:
    ports:
      - "5433:5432"  # ホスト側を5433に変更
```

この場合、直接接続時は `localhost:5433` を使用する。

**ポート使用状況の確認**:

```bash
# Linux/macOS
lsof -i :5432

# または
ss -tlnp | grep 5432
```

#### 2.4.2 ファイル権限エラー

**エラー**: `EACCES: permission denied`

Dockerコンテナ内でrootユーザーとして作成されたファイルに、ホストからアクセスできない。

**解決方法1**: コマンド実行時にユーザーを指定

```bash
# ファイルを作成するコマンドは --user オプションを使用
docker compose run --rm --user "$(id -u):$(id -g)" web rails generate model User
```

**解決方法2**: docker-compose.ymlにユーザー設定を追加

```yaml
services:
  web:
    user: "${UID:-1000}:${GID:-1000}"
    # ... 他の設定
```

起動前に環境変数を設定:

```bash
export UID=$(id -u)
export GID=$(id -g)
docker compose up -d
```

**解決方法3**: 既存ファイルの権限を修正

```bash
# sudoが使える場合
sudo chown -R $(id -u):$(id -g) .

# Dockerコンテナ内から修正
docker compose run --rm web chown -R $(id -u):$(id -g) /app
```

#### 2.4.3 sudoなしでDockerを実行する設定

```bash
# ユーザーをdockerグループに追加
sudo usermod -aG docker $USER

# 変更を反映（再ログインまたは以下を実行）
newgrp docker

# 確認
docker ps
```

### 2.5 管理画面の方式を決定する

ユーザーに以下の選択肢を提示：

| 方式 | 特徴 | 推奨ケース |
|------|------|-----------|
| **Rails一体型** | Railsアプリ内でViewを実装 | シンプル、即座に利用可能 |
| **React/Next.js別アプリ** | フロントエンドを分離 | リッチなUI、SPAが必要 |

#### Rails一体型の場合の選択肢

| ライブラリ | 特徴 |
|-----------|------|
| **Hotwire (Turbo + Stimulus)** | Rails 8標準、サーバーサイドレンダリング |
| **ActiveAdmin** | 管理画面特化、即座に構築可能 |
| **Administrate** | シンプル、カスタマイズ性高 |

### 2.6 追加Gemを検討する

| Gem | 用途 |
|-----|------|
| `jbuilder` または `alba` | JSONシリアライザ |
| `kaminari` または `pagy` | ページネーション |
| `ransack` | 検索・フィルタリング |
| `rack-cors` | CORS対応（API利用時） |
| `rspec-rails` | テスト |

## 出力

選定した管理画面の方式と追加Gemを記録する。
