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

```bash
# .env.local（例。値は Firebase コンソールの Web アプリ設定から）
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<project>.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=<project>
NEXT_PUBLIC_FIREBASE_APP_ID=...
NEXT_PUBLIC_API_BASE=http://localhost:3000   # Rails API のオリジン
```

## 2. AuthClient（契約の実装）

```ts
// lib/auth-client.ts  ('use client')
import { auth } from "./firebase"
import {
  signInWithEmailAndPassword, sendSignInLinkToEmail, isSignInWithEmailLink, signInWithEmailLink,
  GoogleAuthProvider, OAuthProvider, signInWithPopup, linkWithPopup,
  sendPasswordResetEmail, updatePassword, updateEmail, signOut, onAuthStateChanged, getIdToken
} from "firebase/auth"

export const AuthClient = {
  signInWithPassword: (e: string, p: string) => signInWithEmailAndPassword(auth, e, p),
  signInWithEmailLink: (email: string) => {
    window.localStorage.setItem("emailForSignIn", email)  // completeEmailLink で参照
    return sendSignInLinkToEmail(auth, email, {
      url: `${window.location.origin}/auth/email-link`,   // ActionCodeSettings — 要件に合わせて変更
      handleCodeInApp: true,
    })
  },
  completeEmailLink: () => {
    if (!isSignInWithEmailLink(auth, window.location.href)) return Promise.reject(new Error("invalid link"))
    const email = window.localStorage.getItem("emailForSignIn")   // 送信時に保存した email
    return signInWithEmailLink(auth, email!, window.location.href)
  },
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

## 5. デフォルトページ構成と認証ガード（3パターン）

SKILL.md の 3 パターン契約（protected-only / public-aware / guest-only）を Next.js (App Router) で実装する雛形。`<AuthGate>` クライアントコンポーネントで宣言的にガードする。

### AuthGate コンポーネント

```tsx
// components/AuthGate.tsx
"use client";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { AuthClient } from "@/lib/auth-client";

type Type = "protected" | "public-aware" | "guest";

// open redirect 防止: 同一オリジンの「/」始まりのみ、「//」は拒否
function safeCallback(c: string | null): string | null {
  if (!c || !c.startsWith("/") || c.startsWith("//")) return null;
  return c;
}
const DEFAULT_AFTER_LOGIN = "/"; // page_access_control.default_after_login

export function AuthGate({ type, children, render }: {
  type: Type;
  children?: ReactNode;
  render?: (s: { uid: string | null; ready: boolean }) => ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();
  const [ready, setReady] = useState(false);
  const [uid, setUid] = useState<string | null>(null);

  useEffect(() => AuthClient.onAuthStateChanged((u) => { setUid(u?.uid ?? null); setReady(true); }), []);

  useEffect(() => {
    if (!ready) return;
    if (type === "protected" && !uid) {
      router.replace(`/login?callback=${encodeURIComponent(pathname)}`);
    } else if (type === "guest" && uid) {
      router.replace(safeCallback(search.get("callback")) ?? DEFAULT_AFTER_LOGIN);
    }
  }, [ready, uid, type, pathname, search, router]);

  if (!ready) return null;                           // ローディング（必要ならスケルトン）
  if (type === "protected" && !uid) return null;     // リダイレクト中は何も出さない
  if (type === "guest" && uid) return null;
  if (render) return <>{render({ uid, ready })}</>;
  return <>{children}</>;
}
```

### `/login`（guest-only）と `/signup`（guest-only）— 別ページ・相互リンク

```tsx
// app/login/page.tsx
"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { AuthClient } from "@/lib/auth-client";
import { AuthGate } from "@/components/AuthGate";

function safe(c: string | null) { return c && c.startsWith("/") && !c.startsWith("//") ? c : "/"; }

export default function LoginPage() {
  const router = useRouter();
  const callback = useSearchParams().get("callback");
  const [email, setEmail] = useState(""); const [pw, setPw] = useState(""); const [msg, setMsg] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await AuthClient.signInWithPassword(email, pw);
      const t = await AuthClient.getIdToken(true);
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/auth/session`, { method: "POST", headers: { Authorization: `Bearer ${t}` } });
      router.replace(safe(callback));
    } catch (e) { setMsg((e as Error).message); }
  };

  return (
    <AuthGate type="guest">
      <main>
        <h1>ログイン</h1>
        <form onSubmit={submit}>{/* email / password */}</form>
        <p>アカウントをお持ちでない方は <Link href={`/signup${callback ? `?callback=${encodeURIComponent(callback)}` : ""}`}>新規登録</Link></p>
        {msg && <p>{msg}</p>}
      </main>
    </AuthGate>
  );
}
```

```tsx
// app/signup/page.tsx — /login と別ページ。callback を引き継ぐ。
"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AuthGate } from "@/components/AuthGate";
// signUp は createUserWithEmailAndPassword 等で実装し、成功時に router.replace(safe(callback)) する

export default function SignupPage() {
  const callback = useSearchParams().get("callback");
  return (
    <AuthGate type="guest">
      <main>
        <h1>新規登録</h1>
        {/* signUp フォーム */}
        <p>既にアカウントをお持ちの方は <Link href={`/login${callback ? `?callback=${encodeURIComponent(callback)}` : ""}`}>ログイン</Link></p>
      </main>
    </AuthGate>
  );
}
```

### `/mfa/enroll`・`/settings/*`（protected-only）

```tsx
// app/mfa/enroll/page.tsx
import { AuthGate } from "@/components/AuthGate";
export default function MfaEnrollPage() {
  return (
    <AuthGate type="protected">
      <main>{/* MfaClient.enrollSms / confirmSms （firebase-auth-mfa） */}</main>
    </AuthGate>
  );
}
```

```tsx
// app/settings/layout.tsx — /settings 配下をまとめて protected に
import { AuthGate } from "@/components/AuthGate";
export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return <AuthGate type="protected">{children}</AuthGate>;
}
```

### `/`（public-aware）

```tsx
// app/page.tsx
"use client";
import { AuthGate } from "@/components/AuthGate";
export default function Home() {
  return (
    <AuthGate type="public-aware" render={({ uid }) => (
      <main>{uid ? <DashboardPreview /> : <PublicLanding />}</main>
    )} />
  );
}
```

### middleware（任意・BFF 採用時）

セッション戦略が **BFF（Route Handler + HttpOnly クッキー）**の場合は、`middleware.ts` で cookie を見てサーバサイドガードを併用する（クライアントガードと二重化で堅牢）。クライアント Bearer 直叩きの場合は AuthGate のみで十分。

```ts
// middleware.ts（BFF 採用時の例）
import { NextResponse, type NextRequest } from "next/server";
const PROTECTED = [/^\/mfa\//, /^\/settings(?:\/|$)/];
const GUEST_ONLY = [/^\/login$/, /^\/signup$/];
function safe(c: string | null) { return c && c.startsWith("/") && !c.startsWith("//") ? c : "/"; }
export function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const session = req.cookies.get("session");
  if (PROTECTED.some((r) => r.test(path)) && !session)
    return NextResponse.redirect(new URL(`/login?callback=${encodeURIComponent(path)}`, req.url));
  if (GUEST_ONLY.some((r) => r.test(path)) && session)
    return NextResponse.redirect(new URL(safe(req.nextUrl.searchParams.get("callback")), req.url));
}
```

## 6. 既知の制約 / 注意

- ID トークンはメモリ保持＋リフレッシュを既定にし、`localStorage` を避ける（XSS 配慮）。BFF 採用時は HttpOnly クッキー。
- パスワード変更・リセット・メール変更は Firebase JS SDK で完結し **backend 実装不要**（responsibility=iaas）。
- 退会はフロントから `DELETE /account` を呼び、backend が論理削除＋Admin SDK 削除（responsibility=shared）。
- サービスアカウント鍵・Admin 操作は **フロントに置かない**（backend のみ）。
