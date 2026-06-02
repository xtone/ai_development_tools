# references: rails（バックエンド雛形レシピ・API 構成 / docker compose）

`project-backend-init` スキルの **Rails API 実装レシピ**。SKILL.md の「実装契約（言語非依存）」「運用契約」を Rails/Ruby で満たす具体手順。**契約は変えない**（土台の器のみ生成し、ドメインのモデル/マイグレーション/エンドポイント/業務ロジックは生成しない — DP-PINIT-11）。

> **方針: バックエンド環境はすべて docker compose でセットアップする**（ホストに Ruby/rbenv を入れない）。`rails new` も含めコンテナ内で完結させる。本構成は実機検証済み（`rails new --api` → docker compose `db:prepare` → `GET /up` = 200 → `rubocop` no offenses / Ruby 4.0.5・Rails 8.1.3・非 root 実行）。
>
> **コピペで貼りたい場合は [`../templates/rails/`](../templates/rails/) を使う**（B-09）。`templates/rails/` は対の**ファイル単位の最小雛形**（`Dockerfile.dev` / `compose.yaml` / `.dockerignore` / `.env.sample` / `database.yml.template` / `README.md`）。

- 対象: Rails（**API モード** = `rails new --api`）/ Ruby — **公式の最新安定版を使う**（固定しない）。採用日時点のスナップショットは `delivery/version-matrix.md`。Rails が要求する最小 Ruby は gemspec / `rails new` のエラー出力で都度確認（`ai-delivery/docs/environment-setup.md`）。バージョンは `Dockerfile.dev` の `ARG RUBY_VERSION` ／ `.ruby-version` で解決し、**数値をハードコードしない**。
- 前提: `project-monorepo-scaffold`（ワークスペース骨格）と `project-local-infra`（DB の docker compose）が先に生成済み。本レシピはその所定位置にバックエンドの器を載せる。
- いつ使うか: SPA フロント（Next.js 等）と組む API バックエンド土台。SSR/管理画面中心で Rails 内に描画を閉じるなら [`hotwire.md`](./hotwire.md)。

## 0. 責務分担（compose の所有・DP 記録）

| サービス | 所有 Skill | 備考 |
|---|---|---|
| `db`（PostgreSQL 等） | `project-local-infra` | DB イメージ・healthcheck・ボリューム |
| `web`（Rails コンテナ） | `project-backend-init` | `Dockerfile.dev` ＋ web サービス定義 |

> **既定**: 単一の `compose.yaml` に `db` と `web` を同居させ、所有境界をコメントで明示する（検証済み）。`db` は local-infra が定義し、backend は `web` を足す。compose を分割して `include:` / `-f` 合成する方式も可（案件規模で選択）。この分担は判断ポイントとして `docs/pending-decisions.md` に記録し人間が確定する（DP-PINIT-10 / warn_and_document）。

## 1. セットアップ（雛形生成・ホストに Ruby 不要）

ホストに Ruby を入れず、一時的な公式 Ruby **フルイメージ**で雛形を生成する（**全部 docker** 方針）。`RUBY_VERSION` は `delivery/version-matrix.md` の既定サジェスト（**Ruby 4 系最新**・DP-RUBY-VER）。

```bash
# 雛形生成。RUBY_VERSION は固定しない（着手時に version-matrix / 公式最新で解決）。
RUBY_VERSION=4.0.5   # 既定サジェスト = Ruby 4 系最新（DP-RUBY-VER）
docker run --rm -v "$PWD":/work -w /work \
  ruby:${RUBY_VERSION} bash -c \
  "gem install rails && rails new sample-api --api --database=postgresql --skip-test --skip-bundle --skip-git && chown -R $(id -u):$(id -g) sample-api"
echo "${RUBY_VERSION}" > sample-api/.ruby-version
```

- **フルイメージ（`ruby:<ver>`、slim でない）を使う**: slim には `make`/`gcc` が無く `gem install rails` の native 拡張（例: `websocket-driver`）ビルドが失敗する（実機で確認）。実行用 `Dockerfile.dev` は slim ＋ `build-essential` を入れるので別問題。
- **`bash -c` を使う（`-l` を付けない）**: ログインシェル（`bash -lc`）は `/etc/profile` で PATH を上書きし、gem の `rails` バイナリ（`/usr/local/bundle/bin`）が外れて `rails: command not found` になる（実機で確認）。
- **root 生成＋末尾 `chown`**: コンテナ root で生成しホスト UID/GID に chown する（`-u` で UID 指定すると `gem install` が HOME 権限で失敗するため、生成は root・所有権は後で合わせる）。
- `--api`: ビュー層・アセットを含まない最小構成。フロントは別ワークスペース（`project-frontend-init`）。
- `--database=postgresql`: `project-local-infra` の docker compose（既定 PostgreSQL）に合わせる。
- `--skip-bundle`: gem 解決は後段の `docker compose build` で行う（ホストで bundle しない）。
- `--skip-git`: モノレポのルート git を使う。
- `.ruby-version` に採用版を書き、`Dockerfile.dev` の `ARG RUBY_VERSION` と一致させる（`.env` の `RUBY_VERSION` で渡す）。
- **ドメインの `model`/`migration`/`controller` は生成しない**（境界 DP-PINIT-11）。各モジュールが土台の上に載せる。

> ホストに最新 Ruby があるチームは `rails new` をホストで打ってもよいが、**実行・起動・lint はすべて docker compose に寄せる**（本方針）。

## 2. 契約の実装（土台の器）

### 開発用 Dockerfile（本番 Dockerfile と分離）

Rails 8 は標準で**本番用 `Dockerfile`**（`designed for production, not development`）を生成する。開発は別ファイル `Dockerfile.dev` を使う（[`../templates/rails/Dockerfile.dev`](../templates/rails/Dockerfile.dev)）。

```dockerfile
# 抜粋（全文は templates/rails/Dockerfile.dev）。RUBY_VERSION は固定せず .env から渡す。
ARG RUBY_VERSION
FROM docker.io/library/ruby:${RUBY_VERSION}-slim
# libyaml-dev は Ruby 4 系の psych(YAML) bundled gem のビルドに必須（§4 既知の制約）。
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libyaml-dev postgresql-client git && rm -rf /var/lib/apt/lists/*
RUN groupadd --gid 1000 rails && useradd --uid 1000 --gid rails -m -s /bin/bash rails
WORKDIR /rails
COPY Gemfile Gemfile.lock* ./   # --skip-bundle 生成時は lock が無いためワイルドカード
RUN bundle install
COPY . .
RUN chown -R rails:rails /rails /usr/local/bundle
USER rails
EXPOSE 3000
CMD ["bin/rails", "server", "-b", "0.0.0.0", "-p", "3000"]
```

### compose.yaml（web + db・DB 接続核）

`web` は `db` の healthcheck を待ってから `db:prepare` → server 起動。接続情報は **ENV 経由**（[`../templates/rails/compose.yaml`](../templates/rails/compose.yaml)）。

```yaml
services:
  db:                      # ← project-local-infra 所有セクション
    image: postgres:16     # バージョンは local-infra の version-matrix で解決
    environment:
      POSTGRES_USER: ${DATABASE_USER:-postgres}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:-postgres}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER:-postgres}"]
      interval: 2s
      timeout: 3s
      retries: 30
    volumes: [ "pgdata:/var/lib/postgresql/data" ]
  web:                     # ← project-backend-init 所有セクション
    build: { context: ., dockerfile: Dockerfile.dev }
    command: bash -c "bin/rails db:prepare && bin/rails server -b 0.0.0.0 -p 3000"
    env_file: .env
    ports: [ "3000:3000" ]
    depends_on:
      db: { condition: service_healthy }
    volumes:
      - .:/rails                 # ソースを反映（開発）。gem はイメージ内 /usr/local/bundle（覆われない）
volumes:
  pgdata:
```

`config/database.yml` は接続情報を **ENV 解決**にする（[`../templates/rails/database.yml.template`](../templates/rails/database.yml.template)）。`DATABASE_HOST` は **compose のサービス名 `db`**（`localhost` ではない）。

`.env.sample` に DB 名/ユーザ/ポート等のキーだけ置く（**実値なし**・本体は `.gitignore`）。docker compose の `db` 環境変数とキー名を一致させる。

### lint（Rails 標準 omakase）

Rails 8 は標準で `rubocop-rails-omakase`（`.rubocop.yml` に `inherit_gem`）を同梱する。**rubocop を重複追加しない**。ルート CI からは docker compose 経由で叩く:

```bash
docker compose exec web bundle exec rubocop
```

ルート共有設定（DP-PINIT-10）との関係: JS 側は eslint、Ruby 側は omakase に委ねる（言語ごとの標準 lint を尊重）。ルートからは「コンテナ内 lint を呼ぶ」形で統一する。

## 3. 運用詳細（本番必須・why）

- **DB 待ち**: `web` の `depends_on: condition: service_healthy` ＋ `db` の `pg_isready` healthcheck で起動順を保証してから `db:prepare`（待たずに打つと接続エラー）。
- **`db:prepare` を使う**: 土台時点でマイグレーションは無い（ドメインを載せない）。スキーマ作成と接続疎通の確認が目的。
- **gem はイメージ内に焼く**: `/usr/local/bundle` は `.:/rails` の bind mount に覆われないため named volume は不要。Gemfile 変更時は再ビルド（`docker compose build`）。
- **バージョンロック**: `Gemfile.lock` / `.ruby-version` をコミットし version-matrix と整合。`Dockerfile.dev` の `ARG RUBY_VERSION` は `.ruby-version` に合わせる。`gem "rails"` は固定しない。

## 4. 既知の制約（docker × Rails 特有の落とし穴・徹底明文化）

- **雛形生成は Ruby フルイメージで**: `ruby:<ver>-slim` には `make`/`gcc` が無く、`gem install rails` の native 拡張（`websocket-driver` 等）ビルドが `make failed: No such file or directory` で落ちる。**生成は `ruby:<ver>`（フル）**、実行用 `Dockerfile.dev` は slim ＋ `build-essential`（実機で確認）。
- **生成コンテナは `bash -c`（`-l` 不可）**: `bash -lc` はログインシェルで PATH を上書きし、gem の `rails` バイナリ（`/usr/local/bundle/bin`）が外れ `rails: command not found` になる（実機で確認）。
- **`--skip-bundle` だと `Gemfile.lock` が無い**: `Dockerfile.dev` の `COPY Gemfile Gemfile.lock ./` が `not found` で失敗する。**`COPY Gemfile Gemfile.lock* ./`（ワイルドカード）**にし、`bundle install` に lock 生成を委ねる（実機で確認）。
- **`libyaml-dev` が無いと `bundle install` が exit 5**: Ruby 4 系で `psych`(YAML) が bundled gem 化され、native ビルドに libyaml が要る。`Dockerfile.dev` の apt に **`libyaml-dev`** を入れる（無いと `An error occurred while installing psych` で停止・実機で確認）。
- **コンテナ生成物の所有者**: `docker run` で `rails new` するとホスト側が **root 所有**になる。`-u` は `gem install` の HOME 権限で失敗するため、**root 生成＋末尾 `chown -R $(id -u):$(id -g)`** で合わせる（実機で確認）。
- **Rails 標準 `Dockerfile` は本番用**: そのまま開発に使うと `RAILS_ENV=production` / precompile / master.key 要求でハマる。**開発は `Dockerfile.dev` を分離**（非 root 実行・実機で確認）。
- **`DATABASE_HOST` は service 名**: ローカル直叩きの `localhost` ではなく compose の `db`。`database.yml` に直書きせず ENV 解決にする。
- **Rails 8 は `rubocop-rails-omakase` 標準**: 別途 `rubocop` / `rubocop-rails` を Gemfile に足すと**設定が衝突**する。omakase をそのまま使う（重複追加しない）。
- **gem はイメージ内（`/usr/local/bundle`）に焼く**: `.:/rails` の bind mount は `/usr/local/bundle` を覆わないので named volume は不要。Gemfile 変更時は再ビルド（土台は gem を頻繁に足さない）。
- **`--api` はミドルウェアが削られている**: Cookie/Session/Flash が既定で無い。必要ならモジュールが足す（土台は足さない・DP-PINIT-11）。
- **境界の逸脱に注意**: `rails generate scaffold` や認証 gem を土台で入れない。ドメイン/機能は各モジュールプラグインが載せる（DP-PINIT-11）。

## 5. 検証（DoD・B-15／実機確認済み）

土台のみなので「**起動・DB 接続・lint が通る**」ことを docker compose 上で確認する（ドメインテストは無い）。

```bash
docker compose up -d --build              # build → db(healthy) → web 起動 → db:prepare
docker compose logs web | grep -E "Created database|Listening on"   # DB 作成 & Puma 起動を確認
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:3000/up # => 200（Rails 標準ヘルスチェック）
docker compose exec web bundle exec rubocop                          # omakase で no offenses
docker compose down                                                  # 後片付け
```

- 起動疎通は Rails 標準 `GET /up`（`Rails::HealthController`）で確認（ドメインのエンドポイントを足さずに済む）。
- 確認結果は `delivery/scaffold-log.md`（または案件の実装ログ）に記録する。

## 6. 公式ツールの有無

- 雛形は Rails 標準 `rails new --api`（一時 Ruby コンテナ経由）。独自ジェネレータは作らない。
- ヘルスチェックは Rails 標準 `/up`。lint は Rails 標準 omakase。独自実装しない。

## 7. 規約（ファイル名・rails new オプション）

- **ファイル名**: `compose.yaml`（Compose v2 標準。`docker-compose.yml` は使わない）／ 開発イメージは `Dockerfile.dev`（本番は Rails 標準 `Dockerfile` を残す）／ 接続情報は `.env`（実値・gitignore）＋ `.env.sample`（雛形）。
- **rails new オプション**（土台で固定する規約）:
  - API は `--api`、Hotwire は付けない（[`hotwire.md`](./hotwire.md)）。
  - 共通: `--database=postgresql`（local-infra と一致）／`--skip-test`（既定テスト = RSpec のため）／`--skip-bundle`（bundle は compose build）／`--skip-git`（モノレポのルート git）。
  - **既定テスト = RSpec**（`Gemfile.snippet` で `rspec-rails` + `factory_bot_rails`、bundle 後に `bin/rails generate rspec:install`）。DP-TEST-FW・2026-06-02 確定。
  - **既定デザイン（Hotwire）= Tailwind CSS**（`--css=tailwind` = tailwindcss-rails・**Node 不要**、bundle 後に `bin/rails tailwindcss:install`）。JS は **importmap 維持**。DP-CSS-FW・2026-06-02 確定。
  - **作成時に確認する選択制は維持**（minitest / 他 CSS / esbuild 等への変更可・pending-decisions）。
  - `RUBY_VERSION` は `.env`・`.ruby-version`・`Dockerfile.dev` の `ARG` で一致させ、数値を散在ハードコードしない。

## templates

[`../templates/rails/`](../templates/rails/) に最小雛形（`Dockerfile.dev` / `compose.yaml` / `.dockerignore` / `.env.sample` / `database.yml.template` / `README.md`）。
