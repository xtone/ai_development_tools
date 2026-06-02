# references: hotwire（バックエンド雛形レシピ・Rails+Hotwire / docker compose）

`project-backend-init` スキルの **Rails+Hotwire 実装レシピ**。SKILL.md の契約を Rails/Ruby で満たす具体手順。**契約は変えない**（土台の器＋最小ビュー層のみ。ドメイン画面/モデル/業務ロジックは生成しない — DP-PINIT-11）。

> **方針: バックエンド環境はすべて docker compose**（ホストに Ruby を入れない）。docker 構成・DB 接続核・lint・責務分担（compose 所有）は [`rails.md`](./rails.md) と**共通**。本ファイルは Hotwire 固有点（フル構成・最小ビュー層・importmap）に絞る。
>
> **コピペで貼りたい場合は [`../templates/hotwire/`](../templates/hotwire/) を使う**（B-09）。

- 対象: Rails（**フル構成** = `rails new`、`--api` を付けない）+ Hotwire（turbo-rails / stimulus-rails・Rails 既定同梱）/ Ruby — **公式の最新安定版**（固定しない・`delivery/version-matrix.md`）。
- いつ使うか: **SSR / 管理画面中心で、別フロント SPA を持たず Rails 内で Hotwire 描画する案件**。SPA フロントと組む API 構成なら [`rails.md`](./rails.md)。
- 前提: `project-monorepo-scaffold` と `project-local-infra` が先に生成済み。Hotwire 案件はフロントを Rails 内に閉じるため `project-frontend-init`（別 SPA）は通常呼ばない。

## 0〜2. docker 構成・DB 接続核・lint・責務分担

[`rails.md` の該当節](./rails.md)と**同一**:
- 責務分担（`db`=local-infra / `web`=backend、compose 所有は DP・[`rails.md` §0](./rails.md#0-責務分担compose-の所有dp-記録)）
- `Dockerfile.dev`（本番 Dockerfile と分離）/ `compose.yaml`（web + db・healthcheck 待ち）/ `.dockerignore`
- `config/database.yml` の ENV 解決（`DATABASE_HOST=db`）・`.env.sample`（実値なし）
- lint は Rails 標準 omakase（`docker compose exec web bundle exec rubocop`）

**唯一の差分**は生成コマンド（フル構成）と**最小ビュー層**（下記）。

## 1. セットアップ（雛形生成・ホストに Ruby 不要／フル構成）

```bash
# --api を付けない（フル構成）。Rails 既定で Turbo/Stimulus が同梱される。
RUBY_VERSION=4.0.5   # 既定サジェスト = Ruby 4 系最新（DP-RUBY-VER）
docker run --rm -v "$PWD":/work -w /work \
  ruby:${RUBY_VERSION} bash -c \
  "gem install rails && rails new sample-hotwire --database=postgresql --css=tailwind --skip-test --skip-bundle --skip-git && chown -R $(id -u):$(id -g) sample-hotwire"
echo "${RUBY_VERSION}" > sample-hotwire/.ruby-version
```

- `--api` を**付けない**（ビュー層・アセットを含むフル構成）。
- **ドメイン画面（コントローラ/ビュー/モデル）は生成しない**。**最小レイアウト核**（`app/views/layouts/application.html.erb` の Turbo/Stimulus 読み込み）までが土台の範囲（DP-PINIT-11）。
- **既定 = Tailwind CSS（`--css=tailwind`）＋ RSpec（`--skip-test`）**（DP-CSS-FW / DP-TEST-FW）。`tailwindcss-rails` は **Node 不要**（importmap 維持と両立）。選択制は維持。

### 初期化（bundle 後に 1 回・`--skip-bundle` 生成のため別途）

`--skip-bundle` で生成すると Tailwind/RSpec の install タスクが走らない。`Gemfile.snippet`（`rspec-rails` + `factory_bot_rails`）を Gemfile に追記し、`docker compose build`（bundle）後に:

```bash
docker compose run --rm web bin/rails tailwindcss:install   # app/assets/tailwind/application.css 生成（無いと tailwindcss:build が失敗）
docker compose run --rm web bin/rails generate rspec:install # spec/ 生成
```

> 罠（実機確認）: `rails new --css=tailwind --skip-bundle` では `app/assets/tailwind/application.css` が**未生成**。bundle 後に `tailwindcss:install` を 1 回流す（流さないと `tailwindcss:build` が "input file does not exist" で失敗）。

## 2'. 最小ビュー層（Hotwire 読み込みのみ）

土台が持つビューは **レイアウトの Hotwire 読み込み核だけ**。ドメイン画面は含めない（[`../templates/hotwire/application.html.erb.template`](../templates/hotwire/application.html.erb.template)）。Rails 既定で同等のレイアウトが生成されるため、**欠けている場合のみ補う**（二重に Hotwire を入れない）。

- アセット構成は Rails 既定（importmap）に従う。importmap なら Node 不要で `web` コンテナだけで完結する。
- esbuild/bun 構成にする場合のみ `compose.yaml` の `web.command` にアセット watch を足す（案件選択・pending-decisions）。ドメインの partial / view component は土台では作らない。

## 3. 運用詳細（Hotwire 固有）

- **起動は `bin/rails server` で足りる**: importmap 既定なら JS バンドル不要なので、`compose.yaml` の `command` は API と同じ（`db:prepare && server`）でよい。`bin/dev`（foreman）はホスト開発用で、docker compose では compose が起動管理を担うため不要。
- **DB 待ち / `db:prepare` / gem volume / バージョンロック**: [`rails.md` の運用詳細](./rails.md#3-運用詳細本番必須why)と同一。

## 4. 既知の制約（Rails+Hotwire 固有 ＋ docker 共通）

- **既定 Hotwire を二重インストールしない**: 新規 Rails は既定で Turbo/Stimulus を含む。`bin/rails turbo:install` を重ねると importmap/レイアウトに重複が入る。**既定で入っているか確認してから**、無い場合のみ明示インストール。
- **`--api` と取り違えない**: Hotwire はフル構成が前提。誤って `--api` で生成するとビュー層が無く Turbo が動かない。**この取り違えが最頻の事故**。生成コマンドを必ず確認。
- **importmap vs JS バンドラ**: 土台では importmap 既定に倒す（Node 不要）。バンドラ移行は案件判断（pending-decisions）。
- **CSRF**: フル構成は CSRF 保護が既定 ON。Turbo のフォーム送信は対応済み。土台で `protect_from_forgery` を外さない。
- **docker 共通の落とし穴**（フルイメージ必須 / `bash -c`（`-l` 不可）/ `Gemfile.lock*` ワイルドカード / `libyaml-dev` / root 生成＋chown / Rails 標準 Dockerfile は本番用 / `DATABASE_HOST` は service 名 / omakase 重複 / gem はイメージ内に焼く / 境界の逸脱）は [`rails.md` §4](./rails.md#4-既知の制約docker--rails-特有の落とし穴徹底明文化) と共通。

## 5. 検証（DoD・B-15）

```bash
docker compose up -d --build
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:3000/up   # => 200（Rails 標準ヘルスチェック）
docker compose exec web bundle exec rubocop                            # omakase で no offenses
docker compose down
```

- 起動疎通は Rails 標準 `/up` で確認。最小レイアウトが Hotwire を読み込めているかは、生成直後の `/up` 緑 ＋ 起動エラーが無いことで判断。
- 確認結果は `delivery/scaffold-log.md`（または案件の実装ログ）に記録する。

## 6. 公式ツールの有無

- 雛形は Rails 標準 `rails new`（フル）＋ Rails 既定同梱の Hotwire。`turbo-rails` / `stimulus-rails` は公式 gem。独自セットアップは作らない。

## templates

[`../templates/hotwire/`](../templates/hotwire/) に最小雛形（`Dockerfile.dev` / `compose.yaml` / `.dockerignore` / `database.yml.template` / `.env.sample` / `application.html.erb.template` / `README.md`）。
