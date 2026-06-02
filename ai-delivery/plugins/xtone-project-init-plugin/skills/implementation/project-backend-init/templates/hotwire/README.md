# templates/hotwire/（Rails+Hotwire バックエンド土台・docker compose 最小雛形）

`project-backend-init` の Rails+Hotwire（フル構成）土台を **docker compose で動かす**ための最小雛形。解説・why は [`../../references/hotwire.md`](../../references/hotwire.md)。docker 構成は [`templates/rails/`](../rails/) と共通で、差分は**フル構成生成**と**最小レイアウト核**のみ。

> **方針: バックエンド環境はすべて docker compose**（ホストに Ruby を入れない）。**土台＋最小ビュー層のみ**。ドメイン画面/モデル/業務ロジックは含めない（DP-PINIT-11）。

## 含まれるファイル

| ファイル | 配置先 | 用途 |
|---|---|---|
| `Dockerfile.dev` | バックエンド直下 | 開発用イメージ（本番 Dockerfile と分離・非 root 実行） |
| `compose.yaml` | バックエンド直下 | web（Rails）＋ db（PostgreSQL）。`db` は project-local-infra と統合 |
| `.dockerignore` | バックエンド直下 | ビルドコンテキスト除外（`.env` を入れない） |
| `database.yml.template` | `config/database.yml` | DB 接続核（ENV 経由・host は service 名 `db`） |
| `.env.sample` | バックエンド直下の `.env.sample` | DB 接続キー一覧（**実値なし**） |
| `Gemfile.snippet` | 既存 `Gemfile` へ追記 | 既定テスト = RSpec（rspec-rails / factory_bot_rails） |
| `application.html.erb.template` | `app/views/layouts/application.html.erb` | 最小レイアウト（Hotwire 読み込み核のみ） |

## 配置手順（ホストに Ruby 不要）

1. 一時 Ruby コンテナで**フル構成**の雛形生成（`--api` を付けない）:
   ```bash
   RUBY_VERSION=4.0.5   # 既定サジェスト = Ruby 4 系最新（DP-RUBY-VER・固定しない）
   docker run --rm -v "$PWD":/work -w /work \
     ruby:${RUBY_VERSION} bash -c \
     "gem install rails && rails new sample-hotwire --database=postgresql --css=tailwind --skip-test --skip-bundle --skip-git && chown -R $(id -u):$(id -g) sample-hotwire"
   ```
   既定: **Tailwind CSS**（`--css=tailwind` = tailwindcss-rails・**Node 不要**）＋ **RSpec**（`--skip-test`、gem は次手順）。Turbo/Stimulus は Rails 既定同梱（**二重インストールしない**）。
2. 上表のファイル＋`Gemfile.snippet`（RSpec gem）をコピー。`.template` 拡張子を外し、`Gemfile.snippet` の内容を `Gemfile` へ追記。`application.html.erb.template` は生成済みレイアウトを確認し**欠けている場合のみ**補う。
3. `.env.sample` をコピーして `.env` を作り実値を入れる（`.env` は `.gitignore` 済み・MCP-08）。
4. 初期化（**bundle 後に 1 回**・`--skip-bundle` 生成のため別途）:
   ```bash
   docker compose build                                                   # bundle install（rspec/tailwind 入る）
   docker compose run --rm web bin/rails tailwindcss:install              # Tailwind 入力CSS（app/assets/tailwind/application.css）生成
   docker compose run --rm web bin/rails generate rspec:install           # spec/ 生成
   ```
5. 起動・疎通確認:
   ```bash
   docker compose up -d
   curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:3000/up   # => 200
   docker compose exec web bin/rails tailwindcss:build                    # Tailwind ビルド（Done in ...ms）
   docker compose exec web bundle exec rspec                              # RSpec 実行
   docker compose exec web bundle exec rubocop                            # omakase で no offenses
   ```

## コミット禁止（重要）

- **`.env`（実値）は絶対にコミットしない**。雛形は `.env.sample`（キーのみ）。`.gitignore` / `.dockerignore` に `.env` を含める。
- 機密（鍵・トークン）は `templates/` に置かない（`.sample` で枠のみ）。
