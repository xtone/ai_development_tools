# MFA レシピ: Ruby on Rails（backend）

`firebase-auth-mfa` スキルの **backend 実装レシピ**。SKILL.md の backend 契約（MFA クレーム検証・`mfa_requirement` 強制・enrollment 状態確認・失効）を Rails/Ruby で満たす。**登録/追加認証フローは持たない**（それは client = [`hotwire.md`](./hotwire.md) / [`nextjs.md`](./nextjs.md)）。

土台は [`firebase-auth-setup/references/rails.md`](../../firebase-auth-setup/references/rails.md)（`FirebaseAdapter` / `Authenticatable` / `revoke_tokens!`）。本レシピはその**差分のみ**を示す。

- 対象: Rails（API モード）/ Ruby — **公式の最新安定版**（バージョン方針は `ai-delivery/docs/environment-setup.md`）
- 依存追加なし（firebase-auth-setup と同じ `jwt` / `googleauth`）

## 1. ID トークンの MFA クレームを取り込む

`firebase.sign_in_second_factor` は、ユーザーが**第2要素でサインインしたときのみ** ID トークンに入る（`"totp"` / `"phone"`）。`AuthUser` に `second_factor` を追加する（既存の uid/email/provider 契約は不変）。

```ruby
# app/adapters/auth/adapter.rb — AuthUser に second_factor を追加（差分）
module Auth
  AuthUser = Struct.new(:uid, :email, :provider, :second_factor, :claims, keyword_init: true)
end
```

```ruby
# app/adapters/auth/firebase_adapter.rb — verify_token の戻り値に second_factor を含める（差分）
def verify_token(id_token)
  decoded, _ = JWT.decode(id_token, nil, true, **decode_options) { |h| public_key_for(h["kid"]) }
  raise Auth::InvalidToken, "empty sub" if decoded["sub"].to_s.empty?
  Auth::AuthUser.new(
    uid:           decoded["sub"],
    email:         decoded["email"],
    provider:      decoded.dig("firebase", "sign_in_provider"),
    second_factor: decoded.dig("firebase", "sign_in_second_factor"),  # "totp" / "phone" / nil
    claims:        decoded
  )
rescue JWT::DecodeError, OpenSSL::X509::CertificateError => e
  raise Auth::InvalidToken, e.message
end
```

## 2. `mfa_requirement` の強制（concern）

`mfa_satisfied?` は「この ID トークンが第2要素で発行されたか」。`require_mfa!` を `before_action` で使い、未充足を専用エラーで弾いて client に enrollment / 再ログインを促す。

```ruby
# app/controllers/concerns/mfa_enforceable.rb
module MfaEnforceable
  extend ActiveSupport::Concern
  private

  # この ID トークンが第2要素で発行されたか（DB/HTTP 不要、クレームのみ）
  def mfa_satisfied?
    @current_auth_user&.second_factor.present?
  end

  # mfa_requirement に応じて未充足を拒否する。
  # requirement は design.authentication.mfa_requirement（ENV や設定から注入）。
  def require_mfa!(requirement: AppAuth.mfa_requirement)
    case requirement
    when "required"
      deny_mfa! unless mfa_satisfied?
    when "admin_only"
      deny_mfa! if current_user&.admin? && !mfa_satisfied?  # 管理者の定義は案件判断（DP-008 派生）
    end
    # "optional" / "none" は強制しない
  end

  def deny_mfa!
    # client はこの応答で enrollment 画面 or 再ログイン（第2要素）へ誘導する
    render json: { error: "mfa_required" }, status: :forbidden
  end
end
```

```ruby
# 例: 管理者だけ MFA 必須にするコントローラ
class Admin::BaseController < ApplicationController
  include Authenticatable      # firebase-auth-setup（authenticate! / current_user）
  include MfaEnforceable
  before_action :require_registered_user!
  before_action -> { require_mfa!(requirement: "admin_only") }
end
```

`mfa_requirement` は design 由来の設定。ENV か初期化子で一元管理する:

```ruby
module AppAuth
  def self.mfa_requirement = ENV.fetch("MFA_REQUIREMENT", "none")  # required|optional|admin_only|none
end
```

## 3. enrollment 状態の確認（Identity Toolkit REST）

「IaaS 上で第2要素を登録済みか」は `accounts:lookup` の `mfaInfo` で判定する。`required` / `admin_only` で「トークンは未MFAだが enroll は済んでいる（＝再ログインで第2要素を通せる）」のか「そもそも未登録（＝enrollment が要る）」のかを区別したいときに使う。管理画面の表示にも使う。

```ruby
# app/adapters/auth/firebase_adapter.rb（差分）— private は firebase-auth-setup の identitytoolkit_post を再利用
def mfa_enrolled?(uid)
  res  = identitytoolkit_post("accounts:lookup", localId: [uid])
  info = res.dig("users", 0, "mfaInfo")
  info.is_a?(Array) && info.any?
rescue NotFoundError
  false
end
```

## 4. MFA 変更時のトークン失効

enroll / unenroll が起きたら、既存トークンに反映するため失効させる。firebase-auth-setup の運用契約「退会・パスワード変更・**MFA 変更**・不正検知時はサーバ側で失効」の具体化。client は enroll/unenroll 成功後にこのエンドポイントを叩く。

```ruby
# config/routes.rb
post "auth/mfa/changed", to: "mfa#changed"
```

```ruby
# app/controllers/mfa_controller.rb
class MfaController < ApplicationController
  include Authenticatable
  before_action :require_registered_user!

  # client が enroll / unenroll 成功直後に呼ぶ。既存リフレッシュトークンを失効する。
  def changed
    current_user.revoke_tokens!   # firebase-auth-setup: tokens_valid_after 更新 ＋ IaaS revoke
    head :no_content
  end
end
```

> 失効後、client は `getIdToken(true)` で第2要素を含む新しい ID トークンを取得し直す（次回の保護アクセスで `mfa_satisfied?` が true になる）。

## 5. テスト（実 Firebase 不要）

`TestAdapter` の検証トークンに第2要素を載せ、`require_mfa!` の分岐を実 Firebase なしで検証する。

```ruby
# app/adapters/auth/test_adapter.rb（差分）— 形式 test|<uid>|<email>|<provider>|<second_factor?>
def verify_token(id_token)
  _, uid, email, provider, second_factor = id_token.to_s.split("|")
  raise Auth::InvalidToken, "bad test token" if uid.to_s.empty?
  Auth::AuthUser.new(uid: uid, email: email, provider: provider,
                     second_factor: second_factor.presence, claims: { "auth_time" => Time.now.to_i })
end
```

```ruby
# test 例: admin_only の強制
test "admin without second factor is denied" do
  get admin_root_url, headers: bearer("test|u1|a@example.com|password")          # 第2要素なし
  assert_response :forbidden
end

test "admin with totp second factor passes" do
  get admin_root_url, headers: bearer("test|u1|a@example.com|password|totp")      # 第2要素あり
  assert_response :success
end
```

## 6. 既知の制約

- backend は **MFA の登録/追加認証フローを持たない**（client 主体）。backend の役割は「第2要素で入ったかの検証」「`mfa_requirement` の強制」「enrollment 状態の確認」「変更時の失効」に限る。
- `firebase.sign_in_second_factor` は Firebase（Identity Platform）が ID トークンに付与する。別 IaaS へ差し替える場合は同等クレーム/状態（例: `amr`）へマッピングし、本節に明記する。
- TOTP は Admin REST/SDK からの代理登録に非対応。SMS（phone）は `accounts:update` の `mfa` で登録情報を設定できるが、原則は client の enrollment フローに寄せる。
