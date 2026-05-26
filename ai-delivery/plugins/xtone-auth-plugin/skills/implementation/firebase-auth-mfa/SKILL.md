---
name: firebase-auth-mfa
description: Firebase Auth の MFA（多要素認証, TOTP/SMS）を実装するスキル。実装フェーズで、design の mfa_requirement（required/optional/admin_only）に従い、第2要素の登録（enrollment）・サインイン時の追加認証（challenge）・管理者必須の強制・ID トークンの MFA クレーム検証を実装したいときに使う。enrollment/challenge は client、検証/強制/失効は backend、第2要素検証は iaas(Firebase) にまたがる横断機能。言語/FW 非依存の契約を定義し、具体コードは references/（Rails=backend / Hotwire・Next.js=client）に分離。
---

# Firebase Auth MFA Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`design.schema.json` の `authentication.mfa_requirement`（DP-008 の決定）を実装に落とす。MFA は **client（登録・追加認証）／ backend（検証・強制・失効）／ iaas（第2要素の検証）にまたがる横断機能**なので、backend 専用の [`firebase-auth-setup`](../firebase-auth-setup/SKILL.md) や client 専用の [`firebase-auth-frontend`](../firebase-auth-frontend/SKILL.md) には収まらず、本スキルに集約する。design では責務 `MFA = shared`（設定は IaaS、フローは client）と仕分けられている（B-03 responsibility_split）。

> 設計方針: 他スキルと同じく **言語/FW 非依存の「契約」と「手順」**を定義し、具体コードは `references/<stack>.md` に分離する。契約は不変、実装手段だけがレシピごとに変わる。

> **前提**: MFA の有効化方法（全員必須 / 管理者のみ / オプトイン / 不要）は **設計フェーズの判断ポイント DP-008**。本スキルは「決まった方針を実装する」もので、方針自体は決めない。`mfa_requirement` が `undecided` のまま実装に来た場合は確定せず `docs/pending-decisions.md` に残す（T-002 warn_and_document）。

## 呼び出しトリガ（B-13）

`implementation-skill-planner` が以下を判定し `implementation-plan.json.skill_plan` に列挙する:

- `design.yaml.authentication.mfa_requirement` ∈ {`required`, `admin_only`} → **必須**
- `design.yaml.authentication.mfa_requirement` = `optional` → 推奨（オプトイン UI を実装）
- `design.yaml.authentication.mfa_requirement` = `none` → 呼び出し不要（skill_plan に並べない）

未呼び出しのまま実装フェーズが完了に到達した場合は warn_and_document に従い警告（T-002）。

> **前提（B-11）**: 本スキルを呼ぶ前に [`tech-version-check`](../tech-version-check/SKILL.md) を実行し、Firebase Admin SDK / Firebase JS SDK / TOTP / SMS 関連ライブラリ等の **最新安定版と要求ランタイム**を `delivery/version-matrix.md` に取得・記録しておく。`Gemfile` / `package.json` に書く version はそこから引く。

## スコープと責務分割（responsibility_split）

| 層 | 担当 | 本スキルでの内容 |
|---|---|---|
| **client** | アプリ・フロント（Firebase JS SDK） | 第2要素の登録（enrollment）、サインイン時の追加認証（challenge）、解除（unenroll） |
| **backend** | サーバ | ID トークンの MFA クレーム検証、`mfa_requirement` の強制（特に管理者必須）、enrollment 状態の確認、MFA 変更時のトークン失効 |
| **iaas** | Firebase（Identity Platform） | 第2要素そのものの検証、ID トークンへの `firebase.sign_in_second_factor` クレーム付与 |

> backend は **MFA を「検証・強制」するだけ**で、登録/追加認証のフローは持たない（client 主体）。逆に client は失効やロール強制を持たない。両者の接点は「enroll/unenroll の発生をサーバに通知してトークン失効させる」点（下記契約）。

## 入出力（スキーマ）

- 入力: `schemas/design.schema.json`（`authentication.mfa_requirement` ＝ DP-008 の決定 / `responsibility_split` の `MFA` 項目）
- 出力: 実装コード + `schemas/implementation-plan.schema.json`

スキーマは編集しない（CONV-14）。

## `mfa_requirement` の実装マッピング

design の `authentication.mfa_requirement`（enum: `required` / `optional` / `admin_only` / `none`）を次のように実装する。

| 値 | 意味 | client | backend |
|---|---|---|---|
| `required` | 全ユーザー必須 | 全員に enrollment 導線を出し、未登録なら保護機能の前で強制 | `mfa_satisfied?` が false の全ユーザーを拒否 → enrollment へ誘導 |
| `admin_only` | 管理者のみ必須（一般はオプトイン可） | 管理者に enrollment 必須、一般ユーザーには enrollment を提供（任意） | **管理者ロール**かつ `mfa_satisfied?` が false なら拒否。一般は素通り |
| `optional` | 任意（オプトイン） | 設定画面に enrollment 導線。強制しない | 強制しない（enroll 済みかは表示用にのみ参照） |
| `none` | 不要 | enrollment 導線を出さない | 強制しない（本スキルの backend 強制は実装不要） |

> **Issue #131（B-04）の「管理者必須・一般オプトイン」は `admin_only`**。管理者は enrollment 必須、一般ユーザーは設定画面から任意で登録できる、という二段構え。`admin_only` 実装では「誰が管理者か」（ロール判定の根拠）が前提になる — 下記「判断ポイント」を参照。

## 実装契約（言語非依存）

### client（enrollment / challenge / unenroll）

| 操作 | 契約 |
|---|---|
| `enrollTotp() → {secret, qrUrl}` / `confirmTotp(code, displayName)` | TOTP 第2要素を登録。secret/QR を提示 → 認証アプリの 6 桁コードで確定。 |
| `enrollSms(phoneNumber) → verificationId` / `confirmSms(verificationId, code, displayName)` | SMS 第2要素を登録。SMS 検証コードで確定（reCAPTCHA 必須）。 |
| `resolveChallenge(error, factorIndex, code) → Credential` | サインインが `auth/multi-factor-auth-required` を投げたら resolver で第2要素を解決。**TOTP は即時**、**SMS は「送信→入力」の2段**（レシピでは TOTP/SMS で関数を分離）。 |
| `listFactors() → Factor[]` / `unenroll(factor)` | 登録済み第2要素の一覧・解除。 |

enroll / unenroll が成功したら **サーバに通知**し、`backend.revoke_refresh_tokens` を呼ばせる（**IaaS の refresh のみ失効**＝他デバイスの古い MFA 無しトークンを無効化）。`auth_time` は MFA enrollment で更新されないため、サーバ側 `tokens_valid_after` は触らない（後述「既知の制約」）。

### backend（検証 / 強制 / 失効 / 状態確認）

| 操作 | 契約 |
|---|---|
| `verify_token(id_token) → AuthUser{..., second_factor}` | [firebase-auth-setup の `verify_token`](../firebase-auth-setup/SKILL.md) を拡張し、`firebase.sign_in_second_factor`（`"totp"` / `"phone"`、未MFAなら nil）を `AuthUser` に含める。 |
| `mfa_satisfied?(auth_user) → Bool` | ID トークンが第2要素で発行されたか（`second_factor` が非 nil）。 |
| `require_mfa!(auth_user, requirement, admin:)` | `mfa_requirement` と管理者フラグに応じて未充足を拒否（`required` は全員、`admin_only` は管理者のみ）。拒否は専用エラー（例: `mfa_required`）で返し、client に enrollment/再ログインを促す。 |
| `mfa_enrolled?(uid) → Bool` | IaaS 上で第2要素を登録済みか（Admin API の `mfaInfo`）。enrollment 強制の判定や管理画面表示に使う。 |
| `revoke_refresh_tokens(uid)` | enroll/unenroll 通知時に **IaaS の refresh のみ**失効する（他デバイスの古い MFA 無しトークンを無効化）。**サーバ側 `tokens_valid_after` は触らない**（後述「既知の制約」）。`firebase-auth-setup` の「2 段階の失効」の **soft 側**に対応。 |

> backend は AuthAdapter（DP-007）を壊さない。`second_factor` は `AuthUser` への**追加**で、既存の uid/email/provider 契約は不変。別 IaaS では同等のクレーム/状態にマップする。

## 手順（言語非依存）

1. design の `authentication.mfa_requirement` を確認する。`undecided` なら確定せず `docs/pending-decisions.md` に残す（DP-008）。
2. backend レシピ（`references/<stack>.md`）で `verify_token` に `second_factor` を追加し、`require_mfa!` を `mfa_requirement` に合わせて適用する。
3. client レシピで enrollment（TOTP/SMS）・challenge・unenroll を実装する。`admin_only` なら管理者に enrollment を必須化、`optional` なら設定画面に導線を置く。
4. enroll/unenroll 成功時にサーバへ通知し、`revoke_refresh_tokens` を呼ぶ（soft 失効。`auth_time` 仕様のためサーバ側 `tokens_valid_after` は触らない）。
5. Firebase コンソールで MFA（Identity Platform）を有効化する（下記「既知の制約」）。
6. ローカル動作確認（backend テストは `TestAdapter` の `second_factor` 注入で実 Firebase 不要）。
7. 実装タスク・依存・テスト方針を `implementation-plan.schema.json` に記録する。

## 言語・フレームワーク別レシピ

| 層 | 言語 / FW | レシピ | 状態 |
|---|---|---|---|
| backend | Ruby on Rails | [`references/rails.md`](./references/rails.md) | ✅ |
| client | Rails + Hotwire | [`references/hotwire.md`](./references/hotwire.md) | ✅ |
| client | Next.js | [`references/nextjs.md`](./references/nextjs.md) | ✅ |
| その他 | — | — | 追加可（契約を満たす形で `<stack>.md` を追加） |

## ローカル検証（エミュレーター）

`firebase-auth-emulator` で Docker 起動した Auth Emulator に対して、**SMS(phone) MFA** は enrollment/challenge の E2E が回せる。**TOTP MFA はエミュレーター非対応**（[firebase-tools #6224](https://github.com/firebase/firebase-tools/issues/6224)）なので、ローカル検証は SMS で代替し、TOTP の E2E は実 Identity Platform を使う。詳細・接続パラメータ・手順は [`firebase-auth-emulator`](../firebase-auth-emulator/SKILL.md) を参照。

## 既知の制約

- **`auth_time` は MFA enrollment で更新されない**: Firebase の `auth_time` クレームは「最後の認証イベント時刻」（sign-in / MFA challenge）で、**MFA enrollment では更新されない**。そのため backend は MFA 変更時に **IaaS の refresh のみ失効**し、サーバ側の即拒否（`tokens_valid_after` 更新）は行わない（[firebase-auth-setup](../firebase-auth-setup/SKILL.md) の運用契約 3「2 段階の失効」を参照）。**誤って即拒否すると enroll 直後の同セッションが `token revoked` で 401 になる**（実機で再現済み）。
- **emulator の MFA enrollment は `emailVerified=true` が前提**: Firebase Auth Emulator は `UNVERIFIED_EMAIL` エラーを返すため、signUp 直後に `accounts:update` で `emailVerified=true` を立てる必要がある（[`firebase-auth-emulator`](../firebase-auth-emulator/SKILL.md) を参照）。
- **Identity Platform 必須**: TOTP / SMS いずれの MFA も Google Cloud Identity Platform（GCIP）へのアップグレードが必要。Firebase コンソール → Authentication → Sign-in method → Advanced で MFA を有効化してから実装・検証する。無印の Firebase Auth プロジェクトのままでは enroll/challenge が失敗する。
- **SMS のコストと悪用**: SMS MFA は送信コストと SMS ポンピング（不正大量送信）のリスクがある。reCAPTCHA が必須。コスト/不正対策の許容は案件判断（下記「判断ポイント」）。
- **TOTP の管理 enroll 不可**: TOTP は Admin SDK からの代理登録に非対応で、登録は必ず client の enrollment フローを通る。SMS（phone）は Admin SDK でユーザー作成/更新時に登録情報を設定できる。
- **再認証が要る場合がある**: 最近サインインしていないユーザーの enroll/unenroll は `auth/requires-recent-login` を返すことがある。直近の再サインイン後に実行する。
- backend の MFA クレーム検証・enrollment 状態確認は IaaS のクレーム/API に依存する。別 IaaS へ差し替える場合は同等情報へのマッピングをレシピの「既知の制約」に明記する。

## 判断ポイント（人間判断をスルーさせない / DP-008 関連）

`mfa_requirement` 自体（DP-008）は設計で決まっている前提だが、**実装時に派生する判断**は確定せず推奨だけ提示し、未決は `docs/pending-decisions.md` に残す（T-002 warn_and_document）。

- **第2要素の種別（TOTP / SMS / 両方）**: TOTP はコスト 0・オフライン可で推奨。SMS は到達性が高いがコスト/悪用リスクあり。案件のユーザー層・規制で選ぶ。
- **`admin_only` の「管理者」定義**: どのロール/属性を管理者とみなすか（custom claims か アプリ DB のロールか）。強制対象の根拠を明示する。
- **enrollment 強制のタイミング（`required`/`admin_only`）**: 初回ログイン直後に必須化するか、保護機能アクセス時に遅延強制するか。UX とセキュリティのトレードオフ。
- **リカバリー手段**: 第2要素を失った際の回復（バックアップコード / 管理者リセット / 本人確認フロー）。Firebase はバックアップコードを提供しないため運用設計が要る。
