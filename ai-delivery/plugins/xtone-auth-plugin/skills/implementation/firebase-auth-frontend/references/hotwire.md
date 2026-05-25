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
    const idToken = await auth.currentUser?.getIdToken(true)
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

## 6. 既知の制約 / 注意

- Firebase JS SDK はブラウザ実行。`localStorage` ではなくメモリ保持 ＋ リフレッシュを既定にし、XSS リスクを下げる（戦略 A）。
- パスワード変更・リセット・メール変更は Firebase JS SDK で完結し **Rails 実装不要**（responsibility=iaas）。
- 退会はフロントから `DELETE /account` を呼び、サーバが論理削除＋Admin SDK 削除を行う（responsibility=shared）。
