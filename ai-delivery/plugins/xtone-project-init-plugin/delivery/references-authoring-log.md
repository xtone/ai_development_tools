# references-authoring-log（言語別レシピ起稿記録）

`aid-references-authoring` スキルに沿って起稿した references/templates の作成記録（手順10）。

## 2026-06-02 — project-backend-init: rails / hotwire 本実装（docker compose 方針）

| 項目 | 内容 |
|---|---|
| 対象 Skill | `skills/implementation/project-backend-init` |
| stack | `rails`（API 構成）/ `hotwire`（Rails+Hotwire） |
| 契約変更 | **なし**（SKILL.md の言語非依存契約は不変。土台のみ生成・DP-PINIT-11 を遵守） |
| セットアップ方針 | **バックエンド環境はすべて docker compose**（ユーザー方針・DP-PINIT-12 仮）。ホストに Ruby を入れず `rails new`・実行・lint を compose で完結 |
| 参照した学習リファレンス | `xtone-auth-plugin/.../firebase-auth-setup/references/rails.md`（型）／Rails 公式 Compose 流儀 |
| version-matrix | `delivery/version-matrix.md`（Ruby 4.0.5 / Rails 8.1.3・2026-06-02 取得・固定しないスナップショット） |

### 実機 E2E 検証（両スタックとも合格）

ホスト環境は system Ruby 2.6 / rbenv 3.3.6（environment-setup が警告する状況の実例）。検証は rbenv 3.3.6 で `rails new` し、**改訂後テンプレ（docker compose）をそのまま適用**して実施。

| stack | 生成 | docker compose | DB 疎通 | `GET /up` | rubocop |
|---|---|---|---|---|---|
| rails (API) | `rails new --api` | build/up OK | `db:prepare` で DB 作成 | **200** | 21 files **no offenses** |
| hotwire | `rails new`（フル・Turbo/Stimulus 既定同梱） | build/up OK | `db:prepare` で DB 作成 | **200** | 24 files **no offenses** |

- Rails: 8.1.3 / Ruby: 3.3.6（検証機）/ Puma 8.0.2 / PostgreSQL 16（compose）。
- **テンプレ自体を使って検証**したため、templates の実効性も確認済み。

### 生成物（docker compose 方針）

- `references/rails.md` / `references/hotwire.md` — docker compose で完結する手順に改訂
- `templates/rails/` — `Dockerfile.dev` / `compose.yaml` / `.dockerignore` / `database.yml.template`（host=`db`）/ `.env.sample`（host=`db`）/ `README.md`
- `templates/hotwire/` — 上記 ＋ `application.html.erb.template`（最小レイアウト核）
- 旧テンプレ（`Procfile.dev.sample` / `Gemfile.snippet` / `.rubocop.yml.snippet`）は **削除**（docker compose 方針＋omakase 標準で不要）
- `SKILL.md` 言語別レシピ表: `rails` / `hotwire` を ✅ 実装済みに更新

### 実機検証で確定し「既知の制約」に昇格した項目

- **Rails 8 標準 Dockerfile は本番用**（`designed for production`）→ 開発は `Dockerfile.dev` を分離（実機で確認）
- **`DATABASE_HOST` は compose のサービス名 `db`**（`localhost` ではない）
- **`docker run` で `rails new` するとホスト側が root 所有**になる → **root 生成＋末尾 `chown -R $(id -u):$(id -g)`**（`-u` は `gem install` が HOME 権限で失敗するため不可・実機確認）
- **Rails 8 は `rubocop-rails-omakase` 標準同梱** → 別 rubocop gem を足すと衝突（旧 Gemfile.snippet を撤回）
- **gem はイメージ内 `/usr/local/bundle` に焼く**（`.:/rails` の bind mount に覆われないため named volume は不要・Gemfile 変更時は `docker compose build` で再ビルド）
- Hotwire: Turbo/Stimulus は既定同梱（**二重インストール禁止**）／既定レイアウトに `javascript_importmap_tags` が既にある（補うのは欠落時のみ）／`--api` 取り違えが最頻事故

### 判断ポイント（pending-decisions に起票）

- **DP-PINIT-12（仮）**: バックエンド環境＝docker compose 全面化（方針確定・他 setup スキルへの波及反映が未完）
- **DP-PINIT-13（仮）**: compose の所有責務分担（`db`=local-infra / `web`=backend、単一統合 vs include 合成）— 既定で実装・人間確定待ち

### バージョン方針の遵守（environment-setup）

- references/templates に**バージョン数値をハードコードしない**（`Dockerfile.dev` の `ARG RUBY_VERSION` は `.ruby-version` と一致・`postgres:16` は local-infra の version-matrix で解決）。
- version-matrix は採用日スナップショット（Ruby 4.0.5）。**最終検証は ruby:4.0.5 コンテナで実施**（docker 方針なのでホスト Ruby 不要・コンテナ内 `ruby 4.0.5 +PRISM` 確認）。

## 2026-06-02（追補）— テスト/デザイン既定の確定（RSpec / Tailwind）

ユーザー指示「作成時に確認する選択制は維持しつつ、既定を rspec / tailwindcss に」を反映。

| 項目 | 既定 | 実装 | 検証 |
|---|---|---|---|
| テスト | **RSpec** + factory_bot | `--skip-test` ＋ `Gemfile.snippet`（rspec-rails/factory_bot_rails）＋ `rspec:install` | `bundle exec rspec` 動作（0 examples, 0 failures） |
| CSS（Hotwire） | **Tailwind CSS** | `--css=tailwind`（tailwindcss-rails・**Node 不要**）＋ `tailwindcss:install` | `tailwindcss:build` 成功・/up=200 |
| JS | **importmap 維持** | 変更なし（Node 追加せず） | — |

- 選択制は維持（DP-TEST-FW / DP-CSS-FW を pending-decisions に確定記録、minitest/他CSS/esbuild 等へ変更可）。
- **新たな罠（既知の制約に昇格）**: `rails new --css=tailwind --skip-bundle` では install タスクが走らず `app/assets/tailwind/application.css` が未生成 → bundle 後に `tailwindcss:install` / `rspec:install` を 1 回実行。
- 実機検証は Hotwire+Tailwind+RSpec+Ruby4.0.5+非root で /up=200・rspec 動作・tailwind:build 成功・`whoami: rails` を確認。
