# フロント認証レシピ: Next.js

`firebase-auth-frontend` スキルの **Next.js 実装レシピ**。SKILL.md の AuthClient 契約を Next.js（App Router）＋ Firebase JS SDK で満たす。バックエンド（ID トークン検証・/auth/session）は Rails の [`../../firebase-auth-setup/references/rails.md`](../../firebase-auth-setup/references/rails.md)（または同契約の任意 backend）。

- 対象: Next.js（App Router）/ Firebase JS SDK — **いずれも公式の最新安定版**（バージョン方針は `ai-delivery/docs/environment-setup.md`）
- 構成: Firebase JS SDK で認証（client）、ID トークンを Rails API へ Bearer。Rails API のオリジンは `NEXT_PUBLIC_API_BASE`。

## 1. セットアップ

```bash
npm i firebase
```

```ts
// lib/firebase.ts  ('use client' から利用)
import { initializeApp, getApps } from "firebase/app"
import { getAuth, setPersistence, inMemoryPersistence } from "firebase/auth"
const app = getApps()[0] ?? initializeApp({ /* NEXT_PUBLIC_FIREBASE_* から */ })
export const auth = getAuth(app)

// XSS 配慮: トークンをメモリのみに保持（Firebase 既定の localStorage/indexedDB を使わない）。
// 注意: リロードでセッションが切れる。BFF（経路B）で HttpOnly クッキーを使う場合は browserSessionPersistence も検討。
setPersistence(auth, inMemoryPersistence)
```

> Firebase の Web 設定（apiKey 等）は `NEXT_PUBLIC_FIREBASE_*` で渡す（公開前提値）。サービスアカウント鍵は **フロントに置かない**（backend のみ）。

## 2. AuthClient（契約の実装）

```ts
// lib/auth-client.ts  ('use client')
import { auth } from "./firebase"
import {
  signInWithEmailAndPassword, GoogleAuthProvider, OAuthProvider, signInWithPopup, linkWithPopup,
  sendPasswordResetEmail, updatePassword, updateEmail, signOut, onAuthStateChanged, getIdToken
} from "firebase/auth"

export const AuthClient = {
  signInWithPassword: (e: string, p: string) => signInWithEmailAndPassword(auth, e, p),
  signInWithOIDC: (id: "google" | "apple") =>
    signInWithPopup(auth, id === "apple" ? new OAuthProvider("apple.com") : new GoogleAuthProvider()),
  linkProvider: (id: "google" | "apple") =>
    linkWithPopup(auth.currentUser!, id === "apple" ? new OAuthProvider("apple.com") : new GoogleAuthProvider()),
  sendPasswordReset: (e: string) => sendPasswordResetEmail(auth, e),   // Firebase が完結（iaas）
  updatePassword: (p: string) => updatePassword(auth.currentUser!, p),
  updateEmail: (e: string) => updateEmail(auth.currentUser!, e),
  signOut: () => signOut(auth),
  getIdToken: (force = false) => (auth.currentUser ? getIdToken(auth.currentUser, force) : Promise.resolve(null)),
  onAuthStateChanged: (cb: Parameters<typeof onAuthStateChanged>[1]) => onAuthStateChanged(auth, cb),
  withdraw: async () => {                                              // 退会（responsibility=shared）
    const idToken = auth.currentUser ? await getIdToken(auth.currentUser, true) : null
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/account`, {
      method: "DELETE", headers: { Authorization: `Bearer ${idToken}` },
    })
    return signOut(auth)                                              // サーバが論理削除＋Admin SDK 削除
  },
}
```

## 3. ログイン → バックエンド連携

```tsx
// app/(auth)/login/page.tsx  ('use client')
"use client"
import { AuthClient } from "@/lib/auth-client"

async function establishSession() {
  const idToken = await AuthClient.getIdToken(true)
  await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/auth/session`, {
    method: "POST",
    headers: { Authorization: `Bearer ${idToken}` },
  })
}
```

API 呼び出しは `getIdToken()` の Bearer を付ける（サーバが検証）。`onAuthStateChanged` でリロード時のセッション復元を行う。

## 4. 経路の選択（判断ポイント）

| 経路 | 概要 | トレードオフ |
|---|---|---|
| **A. クライアント → Rails API 直接 Bearer（推奨・シンプル）** | ブラウザの Firebase JS SDK で取得した ID トークンを Rails API に Bearer 送信 | CORS 設定が要る。トークンはブラウザが保持 |
| **B. BFF（Next.js Route Handler 経由）** | `app/api/*/route.ts` をプロキシにし、トークンを HttpOnly クッキー等でサーバ側に秘匿 | トークン秘匿性が上がるが実装増。SSR/RSC で認可したい場合に有力 |

**どちらにするかは人間判断**（`firebase-auth-frontend` の判断ポイント）。SSR/RSC で保護ページを出すなら B（ミドルウェアでクッキー検証）が向く。

```ts
// 例: B の保護（middleware.ts）— BFF が設定した検証済みクッキーを確認
export function middleware(req: NextRequest) {
  if (!req.cookies.get("session")) return NextResponse.redirect(new URL("/login", req.url))
}
```

## 5. 既知の制約 / 注意

- ID トークンはメモリ保持＋リフレッシュを既定にし、`localStorage` を避ける（XSS 配慮）。BFF 採用時は HttpOnly クッキー。
- パスワード変更・リセット・メール変更は Firebase JS SDK で完結し **backend 実装不要**（responsibility=iaas）。
- 退会はフロントから `DELETE /account` を呼び、backend が論理削除＋Admin SDK 削除（responsibility=shared）。
- サービスアカウント鍵・Admin 操作は **フロントに置かない**（backend のみ）。
