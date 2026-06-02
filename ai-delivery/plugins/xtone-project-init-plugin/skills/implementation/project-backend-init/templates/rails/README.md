# templates/rails/（Rails API バックエンド土台・docker compose 最小雛形）

`project-backend-init` の Rails（API モード）土台を **docker compose で動かす**ための最小雛形。解説・why は [`../../references/rails.md`](../../references/rails.md)。

> **方針: バックエンド環境はすべて docker compose**（ホストに Ruby を入れない）。**土台のみ**でドメインのモデル/マイグレーション/コントローラは含めない（DP-PINIT-11）。実機検証済み（`db:prepare` → `GET /up` = 200 → rubocop no offenses）。

## 含まれるファイル

| ファイル | 配置先 | 用途 |
|---|---|---|
| `Dockerfile.dev` | バックエンド直下 | 開発用イメージ（Rails 標準の本番 Dockerfile と分離・非 root 実行） |
| `compose.yaml` | バックエンド直下 | web（Rails）＋ db（PostgreSQL）。`db` は project-local-infra と統合 |
| `.dockerignore` | バックエンド直下 | ビルドコンテキスト除外（`.env` を入れない） |
| `database.yml.template` | `config/database.yml` | DB 接続核（ENV 経由・host は service 名 `db`） |
| `.env.sample` | バックエンド直下の `.env.sample` | DB 接続キー一覧（**実値なし**） |
| `Gemfile.snippet` | 既存 `Gemfile` へ追記 | 既定テスト = RSpec（rspec-rails / factory_bot_rails） |

## 配置手順（ホストに Ruby 不要）

1. 一時 Ruby コンテナで雛形生成（オーナーをホストに合わせる）:
   ```bash
   RUBY_VERSION=4.0.5   # 既定サジェスト = Ruby 4 系最新（DP-RUBY-VER・固定しない）
   docker run --rm -v "$PWD":/work -w /work \
     ruby:${RUBY_VERSION} bash -c \
     "gem install rails && rails new sample-api --api --database=postgresql --skip-test --skip-bundle --skip-git && chown -R $(id -u):$(id -g) sample-api"
   ```
   既定テスト = **RSpec**（`--skip-test`、gem は次手順）。（バージョンは固定しない・[`references/rails.md`](../../references/rails.md)）
2. 上表のファイル＋`Gemfile.snippet`（RSpec gem）をコピー。`.template` 拡張子を外し（`database.yml.template` → `config/database.yml`）、`Gemfile.snippet` の内容を `Gemfile` へ追記。
3. `.env.sample` をコピーして `.env` を作り**実値を入れる**（`.env` は `.gitignore` 済み・MCP-08）。`compose.yaml` の `db` 環境変数とキー名を一致させる。
4. 初期化（**bundle 後に 1 回**）:
   ```bash
   docker compose build                                          # bundle install（rspec 入る）
   docker compose run --rm web bin/rails generate rspec:install  # spec/ 生成
   ```
5. 起動・疎通確認:
   ```bash
   docker compose up -d
   curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:3000/up   # => 200
   docker compose exec web bundle exec rspec                              # RSpec 実行
   docker compose exec web bundle exec rubocop                            # omakase で no offenses
   ```

## コミット禁止（重要）

- **`.env`（実値）は絶対にコミットしない**。雛形は `.env.sample`（キーのみ）。`.gitignore` と `.dockerignore` に `.env` を含める。
- 機密（鍵・トークン）は `templates/` に置かない（`.sample` で枠のみ）。

## 補足

- Rails 8 は `rubocop-rails-omakase` を標準同梱するため、lint 用に別 gem を足さない。
- `bundle` は `/usr/local/bundle`（イメージ内）に入り、`.:/rails` の bind mount には覆われないため named volume は不要。Gemfile 変更時は `docker compose build` で再ビルドする。
