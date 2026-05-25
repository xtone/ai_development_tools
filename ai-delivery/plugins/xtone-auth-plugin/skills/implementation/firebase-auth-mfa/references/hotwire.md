# MFA レシピ: Rails + Hotwire（client）

`firebase-auth-mfa` スキルの **client 実装レシピ（Rails + Hotwire / Stimulus ＋ Firebase JS SDK）**。SKILL.md の client 契約（enrollment / challenge / unenroll）を満たす。backend（検証・強制・失効）は [`rails.md`](./rails.md)、土台のサインインは [`firebase-auth-frontend/references/hotwire.md`](../../firebase-auth-frontend/references/hotwire.md)。

- 対象: Rails（Hotwire 同梱）/ Firebase JS SDK — **公式の最新安定版**（`ai-delivery/docs/environment-setup.md`）
- 前提: Firebase コンソールで MFA（Identity Platform）を有効化済み（SKILL.md「既知の制約」）

## 1. import（firebase-auth-frontend の client に追加）

```ruby
# config/importmap.rb — firebase/auth は既存（firebase-auth-frontend）。追加 pin は不要
```

MFA 関連シンボルは `firebase/auth` から import する（`multiFactor`, `TotpMultiFactorGenerator`, `PhoneAuthProvider`, `PhoneMultiFactorGenerator`, `RecaptchaVerifier`, `getMultiFactorResolver`）。

## 2. MfaClient（契約の実装）

```javascript
// app/javascript/auth/mfa-client.js
import {
  multiFactor, TotpMultiFactorGenerator, PhoneAuthProvider, PhoneMultiFactorGenerator,
  RecaptchaVerifier, getMultiFactorResolver, getAuth,
} from "firebase/auth"

const auth = getAuth()

// enroll/unenroll 後は backend にトークン失効を依頼する（rails.md: POST /auth/mfa/changed）
async function notifyChanged() {
  const idToken = await auth.currentUser.getIdToken(true)
  await fetch("/auth/mfa/changed", {
    method: "POST",
    headers: { Authorization: `Bearer ${idToken}`, "X-CSRF-Token": csrf() },
  })
}
function csrf() { return document.querySelector("meta[name='csrf-token']")?.content }

export const MfaClient = {
  // --- TOTP 登録 ---
  // 1) secret/QR を取得して画面に出す
  enrollTotp: async () => {
    const session = await multiFactor(auth.currentUser).getSession()
    const secret = await TotpMultiFactorGenerator.generateSecret(session)
    // 認証アプリ用の otpauth:// URL（QR にする）と、手入力用の secretKey の両方を返す
    const qrUrl = secret.generateQrCodeUrl(auth.currentUser.email, "みんなの読書会")
    return { secret, qrUrl, secretKey: secret.secretKey }
  },
  // 2) 認証アプリの 6 桁コードで確定
  confirmTotp: async (secret, code, displayName = "TOTP") => {
    const assertion = TotpMultiFactorGenerator.assertionForEnrollment(secret, code)
    await multiFactor(auth.currentUser).enroll(assertion, displayName)
    await notifyChanged()
  },

  // --- SMS 登録 ---
  enrollSms: async (phoneNumber, recaptchaContainerId) => {
    const verifier = new RecaptchaVerifier(auth, recaptchaContainerId, { size: "invisible" })
    const session = await multiFactor(auth.currentUser).getSession()
    const provider = new PhoneAuthProvider(auth)
    return provider.verifyPhoneNumber({ phoneNumber, session }, verifier)  // → verificationId
  },
  confirmSms: async (verificationId, code, displayName = "SMS") => {
    const cred = PhoneAuthProvider.credential(verificationId, code)
    const assertion = PhoneMultiFactorGenerator.assertion(cred)
    await multiFactor(auth.currentUser).enroll(assertion, displayName)
    await notifyChanged()
  },

  // --- サインイン時の第2要素チャレンジ ---
  // signInWith... が "auth/multi-factor-auth-required" を投げたら error を渡す
  resolveChallenge: async (error, factorIndex, code, recaptchaContainerId) => {
    const resolver = getMultiFactorResolver(auth, error)
    const hint = resolver.hints[factorIndex]
    if (hint.factorId === TotpMultiFactorGenerator.FACTOR_ID) {
      const assertion = TotpMultiFactorGenerator.assertionForSignIn(hint.uid, code)
      return resolver.resolveSignIn(assertion)
    }
    if (hint.factorId === PhoneMultiFactorGenerator.FACTOR_ID) {
      const verifier = new RecaptchaVerifier(auth, recaptchaContainerId, { size: "invisible" })
      const provider = new PhoneAuthProvider(auth)
      const verificationId = await provider.verifyPhoneNumber(
        { multiFactorHint: hint, session: resolver.session }, verifier)
      const cred = PhoneAuthProvider.credential(verificationId, code)  // ※SMS は「送信→入力」の2段なので実画面では分割する
      return resolver.resolveSignIn(PhoneMultiFactorGenerator.assertion(cred))
    }
    throw new Error("unsupported second factor")
  },

  // --- 一覧 / 解除 ---
  listFactors: () => multiFactor(auth.currentUser).enrolledFactors,  // [{uid, factorId, displayName, ...}]
  unenroll: async (factor) => {
    await multiFactor(auth.currentUser).unenroll(factor)
    await notifyChanged()
  },
}
```

> SMS の challenge は実 UI では「コード送信」→「コード入力」の2ステップに分ける（上記は短縮形）。`verifyPhoneNumber` で送信 → 入力後に `credential` を作る。TOTP は送信不要（認証アプリが生成）。

## 3. Stimulus: TOTP 登録（オプトイン設定画面 / 管理者強制）

```javascript
// app/javascript/controllers/mfa_enroll_controller.js
import { Controller } from "@hotwired/stimulus"
import { MfaClient } from "auth/mfa-client"

export default class extends Controller {
  static targets = ["qr", "secretKey", "code"]

  async start() {
    const { secret, qrUrl, secretKey } = await MfaClient.enrollTotp()
    this.secret = secret
    this.qrTarget.src = await toQrImage(qrUrl)   // 任意の QR ライブラリで otpauth URL を描画
    this.secretKeyTarget.textContent = secretKey // QR を読めない場合の手入力用
  }

  async confirm() {
    await MfaClient.confirmTotp(this.secret, this.codeTarget.value)
    Turbo.visit("/settings/security")  // 完了
  }
}
```

- **`admin_only`**: 管理画面の入口（サーバが `mfa_required` を返す導線）で本コントローラへ誘導し、管理者に enrollment を必須化する。
- **`optional`**: `/settings/security` に「2 要素認証を設定」導線として置く。強制しない。

## 4. Stimulus: サインイン時のチャレンジ

```javascript
// app/javascript/controllers/auth_controller.js（firebase-auth-frontend の signIn を拡張）
async signIn(e) {
  e.preventDefault()
  try {
    await AuthClient.signInWithPassword(this.emailTarget.value, this.passwordTarget.value)
    await this.establishSession()                          // firebase-auth-frontend
  } catch (error) {
    if (error.code === "auth/multi-factor-auth-required") {
      this.mfaError = error                                // 第2要素入力 UI を表示
      this.showSecondFactorForm()
    } else { throw error }
  }
}

async submitSecondFactor() {
  await MfaClient.resolveChallenge(this.mfaError, 0, this.codeTarget.value, "recaptcha-container")
  await this.establishSession()                            // 第2要素クリア後にセッション確立
}
```

## 5. 既知の制約 / 注意

- Firebase コンソールで MFA（Identity Platform）を有効化していないと enroll/challenge が失敗する（SKILL.md「既知の制約」）。
- SMS は reCAPTCHA 必須・送信コスト/悪用リスクあり。TOTP はコスト 0 で推奨（種別選択は SKILL.md 判断ポイント）。
- enroll/unenroll の直後は **必ず backend に通知**（`POST /auth/mfa/changed`）してトークン失効させる。失効後 `getIdToken(true)` で第2要素入りトークンに更新する。
- 最近サインインしていないと enroll/unenroll が `auth/requires-recent-login` を返す。直近の再サインイン後に実行する。
