# フロント認証レシピ: Rails + Hotwire

`firebase-auth-frontend` スキルの **Rails + Hotwire 実装レシピ**。SKILL.md の AuthClient 契約を、Rails 内のフロント（Hotwire / Stimulus ＋ Firebase JS SDK）で満たす。バックエンド（ID トークン検証・/auth/session）は [`../../firebase-auth-setup/references/rails.md`](../../firebase-auth-setup/references/rails.md)。

- 対象: Rails（Hotwire 同梱）/ Firebase JS SDK — **いずれも公式の最新安定版**（バージョン方針は `ai-delivery/docs/environment-setup.md`）
- 構成: サーバ HTML（Turbo）＋ Stimulus コントローラで Firebase JS SDK を呼ぶ。認証フローはブラウザ（client）、トークン検証は Rails（backend）。

## 1. Firebase JS SDK の導入

importmap（Rails 標準）の例:

```ruby
# config/importmap.rb
pin "firebase/app", to: "https://www.gstatic.com/firebasejs/<latest>/firebase-app.js"
pin "firebase/auth", to: "https://www.gstatic.com/firebasejs/<latest>/firebase-auth.js"
```

> `<latest>` は固定値でなく公式の最新安定版を使う（environment-setup.md）。esbuild/jsbundling を使う場合は `npm i firebase`。Firebase の Web 設定値（apiKey 等）は公開前提の値だが、`config/credentials` か ENV から埋め込む。

## 2. AuthClient（契約の実装）

```javascript
// app/javascript/auth/client.js
import { initializeApp } from "firebase/app"
import {
  getAuth, setPersistence, inMemoryPersistence,
  signInWithEmailAndPassword, sendSignInLinkToEmail, isSignInWithEmailLink,
  signInWithEmailLink, GoogleAuthProvider, OAuthProvider, signInWithPopup, linkWithPopup,
  sendPasswordResetEmail, updatePassword, updateEmail, signOut, onAuthStateChanged
} from "firebase/auth"

const auth = getAuth(initializeApp(window.FIREBASE_CONFIG))

// XSS 配慮: トークンをメモリのみに保持（Firebase 既定の localStorage/indexedDB を使わない）。
// 注意: リロードでセッションが切れるため、戦略B（クッキーセッション）と併用するか SSR でログイン状態を保持する（下記「セッション戦略」）。
// 戦略B 採用時は browserSessionPersistence も選択肢。
setPersistence(auth, inMemoryPersistence)

export const AuthClient = {
  signInWithPassword: (email, pw) => signInWithEmailAndPassword(auth, email, pw),
  signInWithEmailLink: (email) => {
    window.localStorage.setItem("emailForSignIn", email)  // completeEmailLink で参照
    return sendSignInLinkToEmail(auth, email, {
      url: window.location.origin + "/auth/email-link",   // ActionCodeSettings — 要件に合わせて変更
      handleCodeInApp: true,
    })
  },
  completeEmailLink: () => {
    if (!isSignInWithEmailLink(auth, window.location.href)) return Promise.reject(new Error("invalid link"))
    const email = window.localStorage.getItem("emailForSignIn")   // 送信時に保存した email
    return signInWithEmailLink(auth, email, window.location.href)
  },
  signInWithOIDC: (id) => signInWithPopup(auth, id === "apple" ? new OAuthProvider("apple.com") : new GoogleAuthProvider()),
  linkProvider: (id) => linkWithPopup(auth.currentUser, id === "apple" ? new OAuthProvider("apple.com") : new GoogleAuthProvider()),
  sendPasswordReset: (email) => sendPasswordResetEmail(auth, email),     // Firebase が完結（iaas）
  updatePassword: (pw) => updatePassword(auth.currentUser, pw),
  updateEmail: (email) => updateEmail(auth.currentUser, email),
  signOut: () => signOut(auth),
  getIdToken: (force = false) => auth.currentUser ? auth.currentUser.getIdToken(force) : Promise.resolve(null),  // 期限切れは自動リフレッシュ
  onAuthStateChanged: (cb) => onAuthStateChanged(auth, cb),
  withdraw: async () => {                                                // 退会（responsibility=shared）
    const idToken = auth.currentUser ? await auth.currentUser.getIdToken(true) : null
    await fetch("/account", { method: "DELETE", headers: { Authorization: `Bearer ${idToken}` } })
    return signOut(auth)                                                 // サーバが論理削除＋Admin SDK 削除
  },
}
```

## 3. Stimulus コントローラ（サインイン → /auth/session）

```javascript
// app/javascript/controllers/auth_controller.js
import { Controller } from "@hotwired/stimulus"
import { AuthClient } from "auth/client"

export default class extends Controller {
  static targets = ["email", "password"]

  async signIn(e) {
    e.preventDefault()
    await AuthClient.signInWithPassword(this.emailTarget.value, this.passwordTarget.value)
    await this.establishSession()
  }

  async establishSession() {
    const idToken = await AuthClient.getIdToken(true)
    await fetch("/auth/session", {
      method: "POST",
      headers: { "Authorization": `Bearer ${idToken}`, "X-CSRF-Token": this.csrf() },
    })
    Turbo.visit("/")   // ログイン後の遷移
  }

  csrf() { return document.querySelector("meta[name='csrf-token']")?.content }
}
```

API を叩く場合は `getIdToken()` を取得して `Authorization: Bearer` を付ける。サーバ側の検証は firebase-auth-setup/rails.md。

## 4. セッション戦略（判断ポイント）

| 戦略 | 概要 | 向き |
|---|---|---|
| **A. Bearer 都度付与（推奨・SPA寄り）** | ID トークンをメモリ保持し、API 毎に `getIdToken()` で Bearer 付与。サーバはステートレス検証 | Turbo/Stimulus で API を叩く構成 |
| **B. クッキーセッション（SSR寄り）** | `/auth/session` で ID トークン検証後、Rails のセッションクッキーにログイン状態を載せる。以後は Rails セッションで認可 | サーバ HTML 主体・Turbo Drive 中心 |

SSR 主体の Hotwire では **B** が素直なことが多い。**どちらにするかは人間判断**（`firebase-auth-frontend` の判断ポイント参照）。B の場合、サーバ側は検証済み uid をセッションに保存し、ログアウトでセッション破棄。

## 5. セッション復元

```javascript
AuthClient.onAuthStateChanged((user) => {
  // リロード時: user があれば establishSession() 済み状態を反映、無ければログイン導線を表示
})
```

## 6. デフォルトページ構成と認証ガード（3パターン）

SKILL.md の 3 パターン（protected-only / public-aware / guest-only）を Rails + Hotwire で実装する雛形。SSR 主体なのでサーバ側 controller の `before_action` で宣言的にガードする。

### 共通モジュール

```ruby
# app/controllers/concerns/page_access_control.rb
module PageAccessControl
  extend ActiveSupport::Concern
  DEFAULT_AFTER_LOGIN = "/" # page_access_control.default_after_login

  class_methods do
    def protected_only(except: []) = before_action(:authenticate_user!,        except: except)
    def guest_only(except: [])     = before_action(:redirect_if_authenticated, except: except)
  end

  private

  def authenticate_user!
    return if user_signed_in?
    redirect_to login_path(callback: request.fullpath), allow_other_host: false
  end

  def redirect_if_authenticated
    return unless user_signed_in?
    redirect_to safe_callback(params[:callback]) || DEFAULT_AFTER_LOGIN, allow_other_host: false
  end

  # open redirect 防止: 同一オリジンの「/」始まりのみ・「//」拒否
  def safe_callback(c) = (c.is_a?(String) && c.start_with?("/") && !c.start_with?("//")) ? c : nil
end
```

### `/login`（guest-only）・`/signup`（guest-only） — 別 controller・相互リンク

```ruby
# app/controllers/sessions_controller.rb — /login
class SessionsController < ApplicationController
  include PageAccessControl
  guest_only

  def new
    @callback = safe_callback(params[:callback])
  end

  def create
    # クライアント SDK でサインイン後、サーバセッションを確立。成功時:
    redirect_to safe_callback(params[:callback]) || DEFAULT_AFTER_LOGIN
  end
end
```

```ruby
# app/controllers/registrations_controller.rb — /signup（/login と別 controller）
class RegistrationsController < ApplicationController
  include PageAccessControl
  guest_only

  def new
    @callback = safe_callback(params[:callback])
  end
end
```

```erb
<%# app/views/sessions/new.html.erb — /login → /signup へのリンク（callback 引き継ぎ）%>
<%= link_to "新規登録はこちら", signup_path(callback: @callback) %>

<%# app/views/registrations/new.html.erb — /signup → /login へのリンク（callback 引き継ぎ）%>
<%= link_to "ログインはこちら", login_path(callback: @callback) %>
```

### `/mfa/enroll`・`/settings/*`（protected-only）

```ruby
class MfaEnrollmentsController < ApplicationController
  include PageAccessControl
  protected_only
  # ビューで firebase-auth-mfa の client コード（Stimulus）を読み込む
end

class SettingsController < ApplicationController # 退会・PW 変更・メール変更
  include PageAccessControl
  protected_only
end
```

### `/`（public-aware）

```ruby
class HomeController < ApplicationController
  include PageAccessControl
  # ガード無し（public-aware）。user_signed_in? でビューを切替
end
```

```erb
<%# app/views/home/index.html.erb %>
<% if user_signed_in? %>
  <%= render "dashboard_preview" %>
<% else %>
  <%= render "public_landing" %>
<% end %>
```

### routes.rb

```ruby
get  "login",  to: "sessions#new",      as: :login
post "login",  to: "sessions#create"
get  "signup", to: "registrations#new", as: :signup
# /mfa/enroll, /settings/* も同様に定義
root to: "home#index"
```

## 7. 既知の制約 / 注意

- Firebase JS SDK はブラウザ実行。`localStorage` ではなくメモリ保持 ＋ リフレッシュを既定にし、XSS リスクを下げる（戦略 A）。
- パスワード変更・リセット・メール変更は Firebase JS SDK で完結し **Rails 実装不要**（responsibility=iaas）。
- 退会はフロントから `DELETE /account` を呼び、サーバが論理削除＋Admin SDK 削除を行う（responsibility=shared）。
