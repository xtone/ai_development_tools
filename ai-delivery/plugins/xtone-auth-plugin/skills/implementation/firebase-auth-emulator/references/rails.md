# レシピ: Rails backend のエミュレーター対応

`firebase-auth-emulator` スキルの **backend(Rails) 実装レシピ**。SKILL.md の backend 契約（署名検証スキップ・Admin REST 切替）を実装する。土台は [`firebase-auth-setup/references/rails.md`](../../firebase-auth-setup/references/rails.md) と [`firebase-auth-mfa/references/rails.md`](../../firebase-auth-mfa/references/rails.md)。本レシピはその**差分のみ**を示す。

- 対象: Rails（API モード）/ Ruby — 公式の最新安定版
- 依存: 追加なし（jwt / googleauth のまま）

## 1. EMULATOR_HOST の検出

`AppAuth` で一元管理する。`FIREBASE_AUTH_EMULATOR_HOST` が設定されているかどうかで分岐する。

```ruby
# config/initializers/app_auth.rb（差分）
module AppAuth
  def self.adapter
    @adapter ||= (ENV.fetch("AUTH_ADAPTER", Rails.env.test? ? "test" : "firebase") == "test" ? Auth::TestAdapter.new : Auth::FirebaseAdapter.new)
  end
  def self.mfa_requirement = ENV.fetch("MFA_REQUIREMENT", "required")
  def self.emulator_host   = ENV["FIREBASE_AUTH_EMULATOR_HOST"].presence   # host:port（プロトコル無し）
  def self.emulator?       = !emulator_host.nil?
  def self.reset!          = (@adapter = nil)
end
```

## 2. verify_token: 署名検証スキップ + 手動 iss/aud/exp 検証

エミュレーターの ID トークンは **unsigned**（alg=none 相当）。jwt gem の署名検証はスキップし、iss/aud/exp/sub と `auth_time` は手動で確認する。

```ruby
# app/adapters/auth/firebase_adapter.rb（差分: verify_token）
def verify_token(id_token)
  decoded =
    if AppAuth.emulator?
      decode_unsigned(id_token)              # 署名スキップ ＋ 手動検証
    else
      decode_signed(id_token)                # 本番: RS256 + 公開鍵
    end
  raise Auth::InvalidToken, "empty sub" if decoded["sub"].to_s.empty?
  Auth::AuthUser.new(
    uid:           decoded["sub"],
    email:         decoded["email"],
    provider:      decoded.dig("firebase", "sign_in_provider"),
    second_factor: decoded.dig("firebase", "sign_in_second_factor"),
    claims:        decoded
  )
rescue JWT::DecodeError, OpenSSL::X509::CertificateError => e
  raise Auth::InvalidToken, e.message
end

private

def decode_signed(id_token)
  JWT.decode(id_token, nil, true,
    algorithms: ["RS256"],
    iss: "https://securetoken.google.com/#{@project_id}", verify_iss: true,
    aud: @project_id, verify_aud: true, verify_expiration: true, verify_iat: true
  ) { |h| public_key_for(h["kid"]) }.first
end

# エミュレーター: 署名検証なしでデコードし、payload は手動で検証する。
# 本番経路では絶対に呼ばない（emulator? でしか到達しない）。
def decode_unsigned(id_token)
  payload, _header = JWT.decode(id_token, nil, false)   # 署名検証スキップ
  raise Auth::InvalidToken, "bad iss" unless payload["iss"] == "https://securetoken.google.com/#{@project_id}"
  raise Auth::InvalidToken, "bad aud" unless payload["aud"] == @project_id
  raise Auth::InvalidToken, "expired" if payload["exp"].is_a?(Integer) && Time.now.to_i >= payload["exp"]
  payload
end
```

> **本番混入の防止**: `decode_unsigned` は `AppAuth.emulator?` が true のときしか呼ばれない。production で誤って `FIREBASE_AUTH_EMULATOR_HOST` を設定しないこと（環境設定・CI Secrets で隔離）。

## 3. Admin REST の host 切替（delete_user / revoke / mfa_enrolled?）

エミュレーター時は `http://${EMULATOR_HOST}/identitytoolkit.googleapis.com` に向け、認可ヘッダを `Bearer owner` に変える。サービスアカウント鍵は不要。

```ruby
# app/adapters/auth/firebase_adapter.rb（差分: private ヘルパー）
def access_token
  return "owner" if AppAuth.emulator?       # ★ エミュレーター専用トークン
  return @token[:value] if @token && Time.now < @token[:expires_at]
  cred = Google::Auth::ServiceAccountCredentials.make_creds(
    json_key_io: StringIO.new(File.read(ENV.fetch("GOOGLE_APPLICATION_CREDENTIALS"))),
    scope: "https://www.googleapis.com/auth/identitytoolkit"
  )
  t = cred.fetch_access_token!
  @token = { value: t["access_token"], expires_at: Time.now + t["expires_in"].to_i - 30 }
  @token[:value]
end

def identitytoolkit_uri(method)
  base = AppAuth.emulator? ? "http://#{AppAuth.emulator_host}/identitytoolkit.googleapis.com" : "https://identitytoolkit.googleapis.com"
  URI("#{base}/v1/projects/#{@project_id}/#{method}")
end

def identitytoolkit_post(method, **body)
  uri = identitytoolkit_uri(method)
  req = Net::HTTP::Post.new(uri)
  req["Authorization"] = "Bearer #{access_token}"     # 本番=OAuth2 / emulator=owner
  req["Content-Type"]  = "application/json"
  req.body = JSON.dump(body)
  res = Net::HTTP.start(uri.host, uri.port, use_ssl: uri.scheme == "https") { |h| h.request(req) }
  raise Auth::NotFoundError if res.code == "404"
  raise Auth::Error, "identitytoolkit #{method}: #{res.code}" unless res.is_a?(Net::HTTPSuccess)
  res.body.to_s.empty? ? {} : JSON.parse(res.body)
end
```

`delete_user` / `revoke` / `mfa_enrolled?` は変更なし（このヘルパーを通る）。emulator 上のユーザー削除・失効・enrollment 状態取得が `Bearer owner` でそのまま動く。

## 4. 起動

`docker-compose.yml` から `FIREBASE_AUTH_EMULATOR_HOST=auth-emulator:9099` と `FIREBASE_PROJECT_ID=demo-telemed` を渡す（[`docker-compose.md`](./docker-compose.md)）。`AUTH_ADAPTER=firebase` で `FirebaseAdapter` が選ばれ、内部で emulator? によって署名・Admin host が自動切替する。

```bash
# ローカル単体起動の例（docker を使わない場合）
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099 \
FIREBASE_PROJECT_ID=demo-telemed \
AUTH_ADAPTER=firebase \
bin/rails s
```

## 5. テスト（エミュレーター E2E）

既存の minitest 結合テスト（`TestAdapter`）はそのまま回す。**emulator E2E は別途、emulator を起動した状態で `AUTH_ADAPTER=firebase` のテストグループ**を分けると整理しやすい（CI ではエミュレーター起動が要るので、ローカル/E2E ジョブのみで実行）。本レシピのスコープは「実装と起動」までで、E2E スクリプトは案件側で組む（例: `bin/e2e` で curl 連打）。

## 6. 既知の制約

- 本番経路で `FIREBASE_AUTH_EMULATOR_HOST` を**絶対に有効化しない**。`decode_unsigned` と `Bearer owner` が本番に出ると、認証が無効化される重大事故になる。production ENV / CI Secrets で隔離し、起動時に Rails.env=production && AppAuth.emulator? なら **abort** する一行を入れるとさらに安全。
- Ruby に公式 Firebase Admin SDK が無い前提のため、Admin 操作は Identity Toolkit REST のホスト切替で対応している（本スキル独自の手段ではなく `firebase-auth-setup` の REST 経路を流用）。
