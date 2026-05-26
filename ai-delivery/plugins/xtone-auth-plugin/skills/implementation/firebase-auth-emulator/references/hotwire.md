# レシピ: Rails + Hotwire frontend のエミュレーター対応

`firebase-auth-emulator` スキルの **client(Hotwire) 実装レシピ**。SKILL.md の client 契約（`connectAuthEmulator` / SMS MFA / SMS コード REST 取得）を、Rails 内の Stimulus + Firebase JS SDK 構成で満たす。土台は [`firebase-auth-frontend/references/hotwire.md`](../../firebase-auth-frontend/references/hotwire.md) と [`firebase-auth-mfa/references/hotwire.md`](../../firebase-auth-mfa/references/hotwire.md)。本レシピはその**差分のみ**を示す。

- 対象: Rails（importmap または jsbundling）/ Firebase JS SDK v9+ modular — 公式の最新安定版

## 1. EMULATOR_HOST をブラウザに渡す

Rails サーバから window 経由でブラウザに渡す。本番ビルドでは未設定（`nil`）にしておけば、自動的に本番経路に切り替わる。

```ruby
# config/initializers/firebase_config.rb
# `FIREBASE_AUTH_EMULATOR_HOST` を ENV から取得。production では未設定にする（本番混入ガード）。
if Rails.env.production? && ENV["FIREBASE_AUTH_EMULATOR_HOST"].present?
  abort "FATAL: FIREBASE_AUTH_EMULATOR_HOST is set in production. Refusing to start (firebase-auth-emulator)."
end
```

```erb
<%# app/views/layouts/application.html.erb の <head> 内に追加 %>
<%# ブラウザ向け: ホスト OS からエミュレーターに繋ぐので localhost:9099。
    Docker 内 Rails から rails コンテナ → emulator は auth-emulator:9099 と別物に注意。 %>
<script>
  window.FIREBASE_CONFIG = <%=
    raw({
      apiKey:     ENV.fetch("FIREBASE_API_KEY", "demo-key"),
      projectId:  ENV.fetch("FIREBASE_PROJECT_ID", "demo-project"),
      authDomain: ENV["FIREBASE_AUTH_DOMAIN"],
      appId:      ENV["FIREBASE_APP_ID"],
    }.to_json)
  %>;
  window.FIREBASE_AUTH_EMULATOR_HOST = <%= raw(ENV["FIREBASE_PUBLIC_EMULATOR_HOST"].to_json) %>;  // 例 "localhost:9099"。本番は null
</script>
```

> Rails コンテナの ENV では `FIREBASE_AUTH_EMULATOR_HOST=auth-emulator:9099`（コンテナ間 DNS）、ブラウザ向けには **別の ENV キー** `FIREBASE_PUBLIC_EMULATOR_HOST=localhost:9099`（ホスト OS の Docker ポートフォワード経由）を分けて持つ。混同するとブラウザから繋がらない。

## 2. connectAuthEmulator（初期化の差分）

`firebase-auth-frontend/references/hotwire.md` の `app/javascript/auth/client.js` に **差分**を入れる。一度だけ呼ぶ（HMR / Turbo 再評価で複数回呼ぶとエラーになる）。

```javascript
// app/javascript/auth/client.js（差分）
import { initializeApp } from "firebase/app"
import {
  getAuth, setPersistence, inMemoryPersistence, connectAuthEmulator,
  signInWithEmailAndPassword, /* ... 以下省略 */
} from "firebase/auth"

const auth = getAuth(initializeApp(window.FIREBASE_CONFIG))
setPersistence(auth, inMemoryPersistence)

// ★ EMULATOR_HOST が設定されている場合のみエミュレーターに接続。本番ビルドでは window.FIREBASE_AUTH_EMULATOR_HOST が null/undefined。
const EMU = window.FIREBASE_AUTH_EMULATOR_HOST
if (EMU) {
  try {
    connectAuthEmulator(auth, `http://${EMU}`, { disableWarnings: true })
  } catch {
    // Turbo Drive で auth/client.js が再評価された場合、connectAuthEmulator は2回目以降エラーを投げる。
    // 既に接続済みなので握りつぶしてよい（emulator/references/nextjs.md と同じ）。
  }
}
```

> Hotwire は Turbo Drive で頁遷移時に JS をリロードしないが、開発時の HMR や手動リロードでファイルが再評価される場面はある。`try/catch` で握りつぶすパターンは nextjs.md と一貫。

## 3. SMS MFA コード自動取得（E2E テスト用）

emulator の REST から最新の検証コードを取り、`firebase-auth-mfa/references/hotwire.md` の `confirmSms` に渡す。

```javascript
// test/system 等から呼ぶ E2E ヘルパ。production 環境では import しない。
export async function fetchLatestEmulatorSmsCode(projectId = "demo-project") {
  const host = window.FIREBASE_AUTH_EMULATOR_HOST
  if (!host) throw new Error("emulator not configured")
  const r = await fetch(`http://${host}/emulator/v1/projects/${projectId}/verificationCodes`)
  if (!r.ok) throw new Error(`emulator REST failed: ${r.status}`)
  const { verificationCodes } = await r.json()
  return verificationCodes.at(-1)?.code   // 最新のコード
}
```

> ブラウザ実機で UI 操作する場合は Emulator UI（`http://localhost:4000`）の「Auth → Phone numbers」から手動でコードを取れる。

## 4. Stimulus からの利用（差分は無し）

Stimulus controller（`firebase-auth-frontend/references/hotwire.md` の `auth_controller.js`）は **emulator/本番のどちらでも同じコード**。`AuthClient` 経由で呼ぶため、ホストの違いは `client.js` 内に閉じる。`alert()` 禁止・DOM フォールバック（B-16）は emulator でも本番でも同じ。

## 5. 既知の制約 / 注意

- 本レシピは `firebase-auth-frontend/references/hotwire.md` の差分。レシピ単独では動かない（土台と組み合わせる）。
- `setPersistence(auth, inMemoryPersistence)` は emulator でも維持する（XSS 配慮の理由は本番と変わらない）。
- 開発時に「`apiKey` 不正で `auth/api-key-not-valid` が出る」場合、`FIREBASE_API_KEY` は emulator なら任意値（"demo-key" 等）で OK。emulator は apiKey を検証しない。
- **本番ビルドの混入ガード**: `Rails.env.production? && ENV["FIREBASE_AUTH_EMULATOR_HOST"].present?` を起動時 abort で塞ぐ（initializer 例参照）。
- TOTP MFA は emulator 非対応。Hotwire でも TOTP の E2E は実 Identity Platform で実行する。

## 6. 関連レシピ

- 環境（compose）: [`./docker-compose.md`](./docker-compose.md)
- backend: [`./rails.md`](./rails.md)
- 別 FW client: [`./nextjs.md`](./nextjs.md)
- 本レシピの土台: [`../../firebase-auth-frontend/references/hotwire.md`](../../firebase-auth-frontend/references/hotwire.md)
