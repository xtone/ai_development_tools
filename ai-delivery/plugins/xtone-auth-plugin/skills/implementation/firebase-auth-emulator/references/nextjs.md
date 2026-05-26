# レシピ: Next.js frontend のエミュレーター対応

`firebase-auth-emulator` スキルの **client(Next.js) 実装レシピ**。SKILL.md の client 契約（`connectAuthEmulator`・SMS MFA・SMS コード REST 取得）を実装する。土台は [`firebase-auth-frontend/references/nextjs.md`](../../firebase-auth-frontend/references/nextjs.md) と [`firebase-auth-mfa/references/nextjs.md`](../../firebase-auth-mfa/references/nextjs.md)。本レシピはその**差分のみ**を示す。

- 対象: Next.js（App Router）/ Firebase JS SDK — 公式の最新安定版

## 1. connectAuthEmulator（初期化の差分）

`NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST` を見て、設定されていれば emulator に接続する。一度だけ呼ぶ（HMR で複数回呼ばないよう注意）。

```ts
// lib/firebase.ts（差分）
import { initializeApp, getApps } from "firebase/app";
import { getAuth, setPersistence, inMemoryPersistence, connectAuthEmulator } from "firebase/auth";

const app =
  getApps()[0] ??
  initializeApp({
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  });

export const auth = getAuth(app);
setPersistence(auth, inMemoryPersistence);

// ★ EMULATOR_HOST が設定されている場合のみエミュレーターに接続。本番ビルドでは未設定にする。
const EMU = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST;
if (EMU && typeof window !== "undefined" && !(auth as unknown as { _canInitEmulator: boolean })._canInitEmulator === false) {
  // disableWarnings: コンソール赤帯の警告を抑制（本番ビルドではこのコードに来ない前提）
  connectAuthEmulator(auth, `http://${EMU}`, { disableWarnings: true });
}
```

> 本番ビルドでは `NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST` を **未設定**にする（`.env.production` に書かない）。`NEXT_PUBLIC_*` はビルド時に埋め込まれるため、誤って production に混入させない。

## 2. SMS MFA（エミュレーターで E2E できる唯一の MFA）

本番では TOTP 主体／SMS 補助でも、ローカル検証は **SMS MFA で第2要素を満たす**。`firebase-auth-mfa/references/nextjs.md` の `enrollSms` / `startSmsChallenge` / `completeSmsChallenge` をそのまま使える（emulator 側で reCAPTCHA はスキップされる扱いだが、API としては `RecaptchaVerifier` を渡す）。

```ts
// 例: SMS MFA enrollment（mfa-client.ts の enrollSms をそのまま呼ぶ）
const verificationId = await MfaClient.enrollSms("+81-90-XXXX-XXXX", "recaptcha-container");
// → ターミナル（emulator 出力）または REST でコードを取得して確定
const code = await fetchEmulatorSmsCode(); // 下記
await MfaClient.confirmSms(verificationId, code, "SMS");
```

## 3. SMS コードの自動取得（テスト用 REST）

E2E スクリプトでは、エミュレーターの REST から最新の SMS コードを取得して `confirmSms` / `completeSmsChallenge` に渡す。

```ts
// E2E ヘルパー（テスト用、本番には含めない）
export async function fetchEmulatorSmsCode(): Promise<string> {
  const EMU = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST!;
  const project = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!;
  const res = await fetch(`http://${EMU}/emulator/v1/projects/${project}/verificationCodes`, {
    headers: { Authorization: "Bearer owner" },
  });
  if (!res.ok) throw new Error(`emulator verificationCodes: ${res.status}`);
  const { verificationCodes } = (await res.json()) as { verificationCodes: { code: string }[] };
  if (!verificationCodes?.length) throw new Error("no SMS code in emulator");
  return verificationCodes[verificationCodes.length - 1].code;
}
```

> 本番では当然このエンドポイントは存在しない。**テストコードを `lib/` 直下ではなく `test/` 系に置く**、または `process.env.NODE_ENV !== "production"` でガードする。

## 4. TOTP のバイパス（エミュレーター時のみ）

`firebase-auth-mfa/references/nextjs.md` の `MfaClient.enrollTotp` はエミュレーターでは **失敗する**（#6224、`Missing phoneEnrollmentInfo`）。UI から enrollment 種別を選ぶ場合、emulator 環境では TOTP を非表示／非活性にしておくと開発体験が良い。

```ts
// 設定画面の例: 環境で TOTP の出し分け
const isEmulator = !!process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST;
{!isEmulator && <button onClick={() => MfaClient.enrollTotp()}>TOTP で登録</button>}
<button onClick={() => MfaClient.enrollSms(phone, "recaptcha-container")}>SMS で登録</button>
```

> 設計（ADR）で「TOTP の E2E は実 Identity Platform」と決めておくこと。

## 5. 起動

`docker-compose.yml` から（[`docker-compose.md`](./docker-compose.md) 参照）：

```env
NEXT_PUBLIC_FIREBASE_PROJECT_ID=demo-telemed
NEXT_PUBLIC_FIREBASE_API_KEY=demo-key
NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
NEXT_PUBLIC_API_BASE=http://localhost:3000
```

ブラウザ側コードは `localhost:9099` で emulator に直接アクセスする（コンテナ間 DNS は使えない）。

## 6. 既知の制約

- TOTP はエミュレーターで失敗する（#6224）。ローカルは SMS、本番／staging で TOTP。
- Emulator UI（`http://localhost:4000`）で mock user 作成・電話番号設定が手軽。
- `connectAuthEmulator` は **一度だけ**呼ぶ。HMR で再評価されると `auth/emulator-config-failed` が出ることがある。`getAuth(app)` の app 単一インスタンスを保つ（`getApps()[0] ?? initializeApp(...)` の慣習を守る）。
- `NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST` を本番ビルドに混入させない（`.env.production` に書かない）。
