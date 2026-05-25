# Firebase Auth レシピ: Ruby on Rails

`firebase-auth-setup` スキルの **Rails 実装レシピ**。スキル本体（SKILL.md）の「実装契約（言語非依存）」を Rails/Ruby で満たす具体コード。契約（AuthAdapter ＋ 運用契約）は変えず、実装手段だけを示す。T-022 パイロット（`~/RubymineProjects/t-021-sample/`）で実証済み。

- 対象: Rails 8（API モード）/ Ruby 3.1+（Rails 8 要件、環境前提は #129）
- 依存: `jwt`（ID トークン検証）・`googleauth`（Admin REST の OAuth2 アクセストークン取得）/ Admin 操作は Identity Toolkit REST API（Ruby 公式 Admin SDK は無いため REST で代替）

## 1. セットアップ

```ruby
# Gemfile
gem "jwt", "~> 3.2"
gem "googleauth"   # Admin REST の OAuth2 アクセストークン取得（退会削除・失効）
```

- Firebase プロジェクトを作成し、サービスアカウント鍵を取得。`GOOGLE_APPLICATION_CREDENTIALS`（または ENV）で渡す。**コミット禁止**（`.gitignore` / Secrets）。
- `FIREBASE_PROJECT_ID` を ENV に設定（ID トークンの aud/iss 検証に使用）。

## 2. AuthAdapter 契約の実装

```ruby
# app/adapters/auth/adapter.rb — 抽象（契約）
module Auth
  AuthUser = Struct.new(:uid, :email, :provider, :claims, keyword_init: true)
  class Error < StandardError; end
  class InvalidToken < Error; end

  class Adapter
    def verify_token(_id_token); raise NotImplementedError; end
    def get_user(_uid);          raise NotImplementedError; end
    def delete_user(_uid);       raise NotImplementedError; end  # 冪等
    def revoke(_uid);            raise NotImplementedError; end
  end
end
```

```ruby
# app/adapters/auth/firebase_adapter.rb — Firebase 実装
require "jwt"; require "net/http"; require "json"; require "openssl"

module Auth
  class FirebaseAdapter < Adapter
    CERTS_URI = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com".freeze

    def initialize(project_id: ENV["FIREBASE_PROJECT_ID"])
      @project_id = project_id.to_s
      raise Auth::Error, "FIREBASE_PROJECT_ID が未設定です" if @project_id.empty?
    end

    def verify_token(id_token)
      decoded, _ = JWT.decode(id_token, nil, true,
        algorithms: ["RS256"],
        iss: "https://securetoken.google.com/#{@project_id}", verify_iss: true,
        aud: @project_id, verify_aud: true, verify_expiration: true
      ) { |h| public_key_for(h["kid"]) }
      # 失効チェックは DB ベース（毎リクエスト HTTP を避ける）。下記「トークン失効」を参照。
      Auth::AuthUser.new(uid: decoded["sub"], email: decoded["email"],
                         provider: decoded.dig("firebase", "sign_in_provider"), claims: decoded)
    rescue JWT::DecodeError, OpenSSL::X509::CertificateError => e
      raise Auth::InvalidToken, e.message
    end

    # ユーザー取得（Identity Toolkit REST accounts:lookup）
    def get_user(uid)
      res  = identitytoolkit_post("accounts:lookup", localId: [uid])
      user = res.dig("users", 0)
      raise Auth::Error, "user not found" unless user
      Auth::AuthUser.new(uid: user["localId"], email: user["email"],
                         provider: user.dig("providerUserInfo", 0, "providerId"), claims: user)
    end

    # delete_user / revoke / certs / identitytoolkit_post は下記「運用詳細」を参照
  end
end
```

JWT 認可ミドルウェア（コントローラ concern）:

```ruby
# app/controllers/concerns/authenticatable.rb
module Authenticatable
  extend ActiveSupport::Concern
  included { before_action :authenticate!; attr_reader :current_user, :current_auth_user }
  private

  # authn: トークン検証で current_auth_user を確立する。
  # current_user は「ローカル DB に登録済みなら」設定される（初回ログインでは nil）。
  def authenticate!
    token = request.headers["Authorization"].to_s.delete_prefix("Bearer ")
    return render(json: { error: "no token" }, status: :unauthorized) if token.blank?
    @current_auth_user = AppAuth.adapter.verify_token(token)
    @current_user = User.active.find_by(uid: @current_auth_user.uid)
    if @current_user && !@current_user.token_valid?(@current_auth_user.claims["auth_time"])
      return render(json: { error: "token revoked" }, status: :unauthorized)  # DB 参照のみ（HTTP なし）
    end
  rescue Auth::InvalidToken => e
    render json: { error: e.message }, status: :unauthorized
  end

  # 登録済みユーザー必須のエンドポイントで使う before_action。
  # Firebase 認証済みでもローカル DB 未登録（current_user=nil）なら 401 で弾く。
  # ※ セッション確立（POST /auth/session）は current_auth_user から upsert するため本ガードは付けない。
  def require_registered_user!
    return if @current_user
    render json: { error: "user not found" }, status: :unauthorized
  end
end
```

登録済みユーザー必須のコントローラでは `before_action :require_registered_user!` を併用する（例: `AccountController`）。セッション確立コントローラ（`SessionsController#create`）は付けず、`current_auth_user` から `User.upsert_from_auth` で作成する。

アダプタの選択は ENV で切替（差し替え可能設計, DP-007）:

```ruby
# config 初期化（遅延）: ENV["AUTH_ADAPTER"]=firebase|test
module AppAuth
  def self.adapter = @adapter ||= (ENV.fetch("AUTH_ADAPTER", Rails.env.test? ? "test" : "firebase") == "test" ? Auth::TestAdapter.new : Auth::FirebaseAdapter.new)
end
```

## 3. 運用詳細（本番必須）

### 退会時の Admin SDK ユーザー削除（冪等）

```ruby
def delete_user(uid)
  # Identity Toolkit REST: POST /v1/projects/{pid}/accounts:delete （要 OAuth2 アクセストークン）
  identitytoolkit_post("accounts:delete", localId: uid)
  true
rescue NotFoundError
  true  # 冪等: 既に存在しない
end
```

### 公開鍵（証明書）キャッシュ（Cache-Control 準拠）

```ruby
def certs
  return @cache[:pem] if @cache && Time.now < @cache[:expires_at]
  res = Net::HTTP.get_response(URI(CERTS_URI))
  ttl = res["cache-control"].to_s[/max-age=(\d+)/, 1]&.to_i || 3600
  @cache = { pem: JSON.parse(res.body), expires_at: Time.now + ttl }
  @cache[:pem]
end

def public_key_for(kid)
  pem = certs[kid] || (@cache = nil; certs[kid])  # kid 不一致は強制再取得（ローテーション追従）
  raise Auth::InvalidToken, "unknown kid" unless pem
  OpenSSL::X509::Certificate.new(pem).public_key
end
```

### トークン失効 / リフレッシュ

**毎リクエストで HTTP を叩かない**ため、失効判定は DB で行う。User に `tokens_valid_after`（datetime）カラムを持ち、失効時に更新。検証時はこの DB 値と ID トークンの `auth_time` を比較するだけ（HTTP 不要）。IaaS 側のリフレッシュトークン失効は失効アクション時のみ呼ぶ。

```ruby
# db/migrate: add_column :users, :tokens_valid_after, :datetime

class User < ApplicationRecord
  # 退会・パスワード変更・MFA 変更・不正検知時に呼ぶ
  def revoke_tokens!
    update!(tokens_valid_after: Time.current)
    AppAuth.adapter.revoke(uid)   # IaaS 側のリフレッシュトークンも失効（ベストエフォート）
  end

  # 検証時の失効判定（DB のみ・HTTP なし）。auth_time が失効時刻以降なら有効。
  def token_valid?(auth_time)
    tokens_valid_after.nil? || (auth_time.present? && Time.at(auth_time.to_i) >= tokens_valid_after)
  end
end
```

```ruby
# FirebaseAdapter#revoke — IaaS 側のリフレッシュトークンを失効（失効アクション時のみ・冪等）
def revoke(uid)
  identitytoolkit_post("accounts:update", localId: uid, validSince: Time.now.to_i.to_s)
  true
rescue NotFoundError
  true
end
```

### Admin REST ヘルパー（FirebaseAdapter private）

Ruby に公式 Admin SDK が無いため、Admin 操作（削除・失効）は Identity Toolkit REST ＋ サービスアカウントの OAuth2 アクセストークンで行う。`NotFoundError` も定義する。

```ruby
class NotFoundError < Auth::Error; end

private

# サービスアカウント鍵から OAuth2 アクセストークンを取得（googleauth gem）。短命なのでキャッシュ。
def access_token
  return @token[:value] if @token && Time.now < @token[:expires_at]
  cred = Google::Auth::ServiceAccountCredentials.make_creds(
    json_key_io: File.open(ENV.fetch("GOOGLE_APPLICATION_CREDENTIALS")),
    scope: "https://www.googleapis.com/auth/identitytoolkit"
  )
  t = cred.fetch_access_token!
  @token = { value: t["access_token"], expires_at: Time.now + t["expires_in"].to_i - 30 }
  @token[:value]
end

def identitytoolkit_post(method, **body)
  uri = URI("https://identitytoolkit.googleapis.com/v1/projects/#{@project_id}/#{method}")
  req = Net::HTTP::Post.new(uri)
  req["Authorization"] = "Bearer #{access_token}"
  req["Content-Type"]  = "application/json"
  req.body = JSON.dump(body)
  res = Net::HTTP.start(uri.host, uri.port, use_ssl: true) { |h| h.request(req) }
  raise NotFoundError if res.code == "404"
  raise Auth::Error, "identitytoolkit #{method}: #{res.code}" unless res.is_a?(Net::HTTPSuccess)
  res.body.to_s.empty? ? {} : JSON.parse(res.body)
end
```

退会・パスワード変更・MFA 変更・不正検知時に `user.revoke_tokens!` を呼ぶ（DB 更新＋ IaaS 失効）。

## 4. テスト（実 Firebase 不要）

`TestAdapter`（同じ契約）でトークン形式 `test|<uid>|<email>|<provider>` を検証し、結合テストを実 Firebase なしで回す（パイロットは 8 tests / 0 failures）。

## 5. 既知の制約

- Ruby には公式 Firebase Admin SDK が無いため、Admin 操作（削除・失効）は Identity Toolkit REST API ＋ サービスアカウントの OAuth2 アクセストークンで実装する。
- 本番鍵が無い環境では削除/失効はスタブ化し、検証（verify_token）と証明書キャッシュのみ動作確認する。
