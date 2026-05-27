# Rails 向け AuthAdapter コード雛形

`firebase-auth-setup` スキルの **Rails レシピ**（[`../../references/rails.md`](../../references/rails.md)）の対になる **コピペ起点のテンプレ**。markdown 内コードブロックを逐次写経する代わりに、ファイル単位で既存 Rails プロジェクトに貼り付けて改変できる。

> 由来: T-022 パイロット F-8 / Issue #134 (B-09)。「言語別の実装テンプレ（AuthAdapter 雛形）」を `references/rails.md` から分離し、コピペ可能なファイル群として同梱する。

## 含まれるもの

| パス | 役割 |
|---|---|
| `Gemfile.snippet` | 追加する gem（`jwt` / `googleauth`） |
| `dotenv.sample` | 必要な ENV 変数（`FIREBASE_PROJECT_ID` / `AUTH_ADAPTER` / `GOOGLE_APPLICATION_CREDENTIALS`） |
| `app/adapters/auth/adapter.rb` | `Auth::Adapter` 抽象（契約）と `AuthUser` / エラー |
| `app/adapters/auth/firebase_adapter.rb` | `FirebaseAdapter` 実装（JWT 検証 / 公開鍵キャッシュ / Admin REST） |
| `app/adapters/auth/test_adapter.rb` | `TestAdapter`（実 Firebase 不要のテスト用） |
| `app/controllers/concerns/authenticatable.rb` | JWT 認可 concern |
| `config/initializers/app_auth.rb` | `AppAuth.adapter` 選択（ENV `AUTH_ADAPTER` 切替） |
| `db/migrate/00000000000000_add_tokens_valid_after_to_users.rb.template` | `users.tokens_valid_after` 追加マイグレーションの雛形 |

> **契約は `references/rails.md` の「実装契約（言語非依存）」と同一。** 本テンプレは契約を変えずに具体コードを提供するだけ（DP-007 差し替え可能設計を維持）。

## 使い方

### 1. 前提を満たす

- 公式の最新安定版の Ruby / Rails（バージョンは固定しない。`tech-version-check` スキルで `delivery/version-matrix.md` に取得・記録してから着手する。バージョン方針は `ai-delivery/docs/environment-setup.md`）。
- Firebase プロジェクトを作成し、サービスアカウント鍵を取得（コミット禁止）。
- ローカル検証は実 Firebase に直接つながず、対の [`firebase-auth-emulator`](../../../firebase-auth-emulator/SKILL.md) スキルの Auth Emulator + Docker を起動するのが既定（B-12）。

### 2. ファイルを配置する

```sh
# プロジェクトルートで（適宜パスを置換）
PLUGIN=ai-delivery/plugins/xtone-auth-plugin/skills/implementation/firebase-auth-setup
cp -r "$PLUGIN"/templates/rails/app/.     ./app/
cp    "$PLUGIN"/templates/rails/config/initializers/app_auth.rb       ./config/initializers/
cp    "$PLUGIN"/templates/rails/db/migrate/00000000000000_add_tokens_valid_after_to_users.rb.template \
      ./db/migrate/"$(date +%Y%m%d%H%M%S)"_add_tokens_valid_after_to_users.rb
```

`Gemfile.snippet` の内容は `Gemfile` に追記、`dotenv.sample` の項目は `.env` / Secrets に展開（`.env` はコミット禁止）。

**マイグレーションの置換**: コピー後の migration ファイル冒頭 `ActiveRecord::Migration[<RAILS_MAJOR.MINOR>]` の `<RAILS_MAJOR.MINOR>` は、`bundle exec rails -v` で確認した Rails のメジャー.マイナーに置換する（バージョンを固定しない方針: `ai-delivery/docs/environment-setup.md`）。

### 3. User モデルに失効ヘルパーを追加する

テンプレに含めていない（既存 `User` への追記になり個別差が大きいため）。下記スニペットをコピペする:

```ruby
class User < ApplicationRecord
  # hard 失効: 退会 / パスワード変更 / 不正検知。サーバ側で即拒否 + IaaS refresh 失効
  def hard_revoke_tokens!
    update!(tokens_valid_after: Time.current)
    AppAuth.adapter.revoke(uid)
  end

  # soft 失効: MFA 変更。IaaS refresh のみ失効（同セッション維持）
  def revoke_refresh_tokens!
    AppAuth.adapter.revoke(uid)
  end

  # 検証時の失効判定（DB のみ・HTTP なし）
  def token_valid?(auth_time)
    tokens_valid_after.nil? || (auth_time.present? && Time.at(auth_time.to_i) >= tokens_valid_after)
  end
end
```

`uid` カラムは別途追加する（`add_column :users, :uid, :string, null: false; add_index :users, :uid, unique: true`）。User と Firebase の紐付け方は案件ごとに違うため、テンプレ化していない（マイグレーションは hard/soft 失効に必須な `tokens_valid_after` のみ提供）。

`hard_revoke_tokens!` / `revoke_refresh_tokens!` をどこから呼ぶかは [`references/rails.md`](../../references/rails.md) の「2 段階の失効」を参照。

### 4. コントローラに認可を組み込む

```ruby
class ApplicationController < ActionController::API
  include Authenticatable
end

class AccountController < ApplicationController
  before_action :require_registered_user!   # 登録済みユーザー必須のエンドポイント
  # ...
end
```

セッション確立（`POST /auth/session`）には `require_registered_user!` を付けない（`current_auth_user` から upsert するため）。

### 5. テストを TestAdapter で回す

`AUTH_ADAPTER=test`（または `Rails.env.test?` で既定） で `Auth::TestAdapter` に切り替わる。トークン形式 `test|<uid>|<email>|<provider>` を結合テストで使えば実 Firebase 不要。

## 既知の制約

- Ruby に公式 Firebase Admin SDK が無いため、Admin 操作（削除・失効）は Identity Toolkit REST + サービスアカウントの OAuth2 アクセストークンで実装する（`googleauth` gem）。
- 本テンプレは **バックエンド専用**。フロントエンド（サインイン UI / トークン保持 / Bearer 付与）は対の [`firebase-auth-frontend`](../../../firebase-auth-frontend/SKILL.md) を参照。
- MFA（DP-008）は対の [`firebase-auth-mfa`](../../../firebase-auth-mfa/SKILL.md) を参照。本テンプレが担う MFA 部分は「2 段階の失効（MFA 変更は soft）」のみ。

## 関連

- スキル本体: [`../../SKILL.md`](../../SKILL.md)
- Rails レシピ（解説 + 契約の根拠）: [`../../references/rails.md`](../../references/rails.md)
- ローカル開発の既定: [`firebase-auth-emulator`](../../../firebase-auth-emulator/SKILL.md)
- フロントエンド: [`firebase-auth-frontend`](../../../firebase-auth-frontend/SKILL.md)
- MFA: [`firebase-auth-mfa`](../../../firebase-auth-mfa/SKILL.md)
