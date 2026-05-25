# MFA レシピ: Next.js（client）

`firebase-auth-mfa` スキルの **client 実装レシピ（Next.js App Router ＋ Firebase JS SDK）**。SKILL.md の client 契約（enrollment / challenge / unenroll）を満たす。backend（検証・強制・失効）は [`rails.md`](./rails.md)、土台のサインインは [`firebase-auth-frontend/references/nextjs.md`](../../firebase-auth-frontend/references/nextjs.md)。

- 対象: Next.js（App Router）/ Firebase JS SDK — **公式の最新安定版**（`ai-delivery/docs/environment-setup.md`）
- 前提: Firebase コンソールで MFA（Identity Platform）を有効化済み（SKILL.md「既知の制約」）。MFA 操作はすべて `'use client'`。

## 1. MfaClient（契約の実装）

```ts
// lib/mfa-client.ts  ('use client')
import { auth } from "./firebase"  // firebase-auth-frontend の getAuth(app)
import {
  multiFactor, TotpMultiFactorGenerator, PhoneAuthProvider, PhoneMultiFactorGenerator,
  RecaptchaVerifier, getMultiFactorResolver, type MultiFactorError, type TotpSecret,
} from "firebase/auth"

// enroll/unenroll 後は backend にトークン失効を依頼（rails.md: POST /auth/mfa/changed）
async function notifyChanged() {
  const idToken = await auth.currentUser!.getIdToken(true)
  await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/auth/mfa/changed`, {
    method: "POST", headers: { Authorization: `Bearer ${idToken}` },
  })
}

export const MfaClient = {
  // --- TOTP 登録 ---
  enrollTotp: async () => {
    const session = await multiFactor(auth.currentUser!).getSession()
    const secret = await TotpMultiFactorGenerator.generateSecret(session)
    const qrUrl = secret.generateQrCodeUrl(auth.currentUser!.email ?? "", "MyApp")
    return { secret, qrUrl, secretKey: secret.secretKey }  // QR と手入力用キー
  },
  confirmTotp: async (secret: TotpSecret, code: string, displayName = "TOTP") => {
    const assertion = TotpMultiFactorGenerator.assertionForEnrollment(secret, code)
    await multiFactor(auth.currentUser!).enroll(assertion, displayName)
    await notifyChanged()
  },

  // --- SMS 登録 ---
  enrollSms: async (phoneNumber: string, recaptchaContainerId: string) => {
    const verifier = new RecaptchaVerifier(auth, recaptchaContainerId, { size: "invisible" })
    const session = await multiFactor(auth.currentUser!).getSession()
    const provider = new PhoneAuthProvider(auth)
    return provider.verifyPhoneNumber({ phoneNumber, session }, verifier)  // → verificationId
  },
  confirmSms: async (verificationId: string, code: string, displayName = "SMS") => {
    const cred = PhoneAuthProvider.credential(verificationId, code)
    const assertion = PhoneMultiFactorGenerator.assertion(cred)
    await multiFactor(auth.currentUser!).enroll(assertion, displayName)
    await notifyChanged()
  },

  // --- サインイン時の第2要素チャレンジ ---
  resolveTotpChallenge: async (error: MultiFactorError, factorIndex: number, code: string) => {
    const resolver = getMultiFactorResolver(auth, error)
    const hint = resolver.hints[factorIndex]
    const assertion = TotpMultiFactorGenerator.assertionForSignIn(hint.uid, code)
    return resolver.resolveSignIn(assertion)
  },
  // SMS は「送信(verificationId 取得)」→「入力(コード)」の2段
  startSmsChallenge: async (error: MultiFactorError, factorIndex: number, recaptchaContainerId: string) => {
    const resolver = getMultiFactorResolver(auth, error)
    const hint = resolver.hints[factorIndex]
    const verifier = new RecaptchaVerifier(auth, recaptchaContainerId, { size: "invisible" })
    const provider = new PhoneAuthProvider(auth)
    const verificationId = await provider.verifyPhoneNumber(
      { multiFactorHint: hint, session: resolver.session }, verifier)
    return { resolver, verificationId }
  },
  completeSmsChallenge: async (resolver: any, verificationId: string, code: string) => {
    const cred = PhoneAuthProvider.credential(verificationId, code)
    return resolver.resolveSignIn(PhoneMultiFactorGenerator.assertion(cred))
  },

  // --- 一覧 / 解除 ---
  listFactors: () => multiFactor(auth.currentUser!).enrolledFactors,
  unenroll: async (factor: Parameters<ReturnType<typeof multiFactor>["unenroll"]>[0]) => {
    await multiFactor(auth.currentUser!).unenroll(factor)
    await notifyChanged()
  },
}
```

## 2. TOTP 登録コンポーネント（オプトイン / 管理者強制）

```tsx
// app/(app)/settings/security/totp-enroll.tsx  ('use client')
"use client"
import { useState } from "react"
import { MfaClient } from "@/lib/mfa-client"
import type { TotpSecret } from "firebase/auth"

export function TotpEnroll() {
  const [secret, setSecret] = useState<TotpSecret | null>(null)
  const [qrUrl, setQrUrl] = useState(""); const [code, setCode] = useState("")

  const start = async () => {
    const r = await MfaClient.enrollTotp()
    setSecret(r.secret); setQrUrl(r.qrUrl)  // qrUrl は QR ライブラリで描画、r.secretKey は手入力用
  }
  const confirm = async () => {
    await MfaClient.confirmTotp(secret!, code)
    location.assign("/settings/security")
  }

  return secret
    ? (<><Qr value={qrUrl} /><input value={code} onChange={e => setCode(e.target.value)} /><button onClick={confirm}>確定</button></>)
    : (<button onClick={start}>2 要素認証を設定</button>)
}
```

- **`admin_only`**: 管理画面で backend が `mfa_required`（403）を返したら本フローへリダイレクトし、管理者に enrollment を必須化。
- **`optional`**: 設定画面に導線として置く。強制しない。

## 3. サインイン時のチャレンジ

```tsx
// app/(auth)/login/page.tsx  ('use client')
import { AuthClient } from "@/lib/auth-client"
import { MfaClient } from "@/lib/mfa-client"
import type { MultiFactorError } from "firebase/auth"

async function onSignIn(email: string, pw: string, code: () => Promise<string>) {
  try {
    await AuthClient.signInWithPassword(email, pw)
    await establishSession()                       // firebase-auth-frontend
  } catch (e) {
    const err = e as MultiFactorError
    if (err.code === "auth/multi-factor-auth-required") {
      await MfaClient.resolveTotpChallenge(err, 0, await code())  // TOTP の例
      await establishSession()                     // 第2要素クリア後にセッション確立
    } else { throw e }
  }
}
```

## 4. 既知の制約 / 注意

- Firebase コンソールで MFA（Identity Platform）を有効化していないと enroll/challenge が失敗する。
- SMS は reCAPTCHA 必須・送信コスト/悪用リスクあり。TOTP 推奨（種別選択は SKILL.md 判断ポイント）。
- enroll/unenroll 後は **必ず backend に通知**（`POST /auth/mfa/changed`）して失効させ、`getIdToken(true)` で第2要素入りトークンに更新する。
- MFA 操作（`multiFactor` 等）は client 専用。サービスアカウント鍵・Admin 操作はフロントに置かない（backend のみ）。
- 最近サインインしていないと enroll/unenroll が `auth/requires-recent-login` を返す。直近の再サインイン後に実行する。
