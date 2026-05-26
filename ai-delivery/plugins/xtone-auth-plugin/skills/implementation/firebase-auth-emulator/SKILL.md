---
name: firebase-auth-emulator
description: Firebase Auth Emulator を Docker で起動し、認証フローをローカルで E2E 検証するスキル。実装フェーズで、firebase-auth-setup(backend) / firebase-auth-frontend(client) / firebase-auth-mfa(横断) の実装を実 Firebase 無しで起動・確認したいときに使う。基本フロー（メール+PW / パスワードレス / 退会 / ロール認可）と **SMS(phone) MFA** は対応、**TOTP MFA は非対応**（firebase-tools #6224）。署名検証スキップ・Admin REST のエミュレーター切替・connectAuthEmulator・SMS コード取得 REST を言語非依存の契約として定義し、具体コードは references/（docker-compose / rails / nextjs）に分離。
---

# Firebase Auth Emulator Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

Firebase Auth Emulator を Docker で起動して、`firebase-auth-setup`（backend）／`firebase-auth-frontend`（client）／`firebase-auth-mfa`（横断）の実装を **実 Firebase / Identity Platform 無しで E2E 検証**するためのスキル。backend/client/emulator にまたがる横断トピックなので、既存スキルの片方には収まらず本スキルに集約する（`firebase-auth-mfa` と同じ論理）。

> **本番ではない**: 本スキルは「ローカル検証専用」。本番は実 Firebase Auth（MFA は Identity Platform）を使う。スキルが定義する署名検証スキップや `Bearer owner` は **本番経路では絶対に有効化しない**。

## 呼び出しトリガ（B-13）

`implementation-skill-planner` が以下を判定し `implementation-plan.json.skill_plan` に列挙する:

- `design.yaml.local_dev_stack` ∈ {`emulator_docker`, `emulator_host`} → **必須**
- `design.yaml.local_dev_stack` = `cloud_direct` → 呼び出し不要（ただし `decision_record` に「ローカルから実 Firebase に直接接続する」根拠を残させる）
- `design.yaml.local_dev_stack` **未指定** → **既定で emulator_docker** として必須化（B-12: ローカル開発の既定は Emulator+Docker）

未呼び出しのまま実装フェーズが完了に到達した場合は warn_and_document に従い警告（T-002）。

## スコープと既知の制約

| 項目 | エミュレーター対応 | 検証方針 |
|---|---|---|
| メール+PW サインイン / パスワードレス | ✅ | エミュレーターで E2E |
| 退会（Admin 削除）/ トークン失効 / Bearer 認可 | ✅ | エミュレーターで E2E |
| **SMS(phone) MFA**（enrollment / challenge） | ✅ | エミュレーターで E2E。SMS コードはターミナル / REST で取得 |
| **TOTP MFA** | ❌ **非対応**（[firebase-tools #6224](https://github.com/firebase/firebase-tools/issues/6224)） | **実 Identity Platform** で検証。設計が TOTP 主体でも、ローカル検証は SMS で代替する |
| Phone Auth の reCAPTCHA / APN / Console のテスト電話番号 | ❌ | エミュレーター内ではスキップ可能（コードはターミナル出力） |
| ID トークンの署名 | **unsigned**（alg=none 相当） | backend は **EMULATOR_HOST 検出時に署名検証をスキップ**（iss/aud/exp/sub は手動検証） |

> design の `authentication.mfa_requirement` が `required` でも、ローカル検証は **SMS MFA で E2E** ／ TOTP は実 Identity Platform、という前提を案件のドキュメント（ADR・pilot-report 等）に明記する。

## 入出力（スキーマ）

- 入力: `schemas/design.schema.json`（`authentication.stack=Firebase Auth` を前提）、案件の `responsibility_split`
- 出力: `docker-compose.yml` / `firebase.json` / backend 起動 ENV / frontend `connectAuthEmulator` 初期化コード + `schemas/implementation-plan.schema.json`

スキーマは編集しない（CONV-14）。

## 実装契約（言語非依存）

### emulator 接続パラメータ

| 名前 | 値 | 用途 |
|---|---|---|
| `FIREBASE_AUTH_EMULATOR_HOST` | `host:port`（プロトコル**無し**、例 `auth-emulator:9099`） | backend / client / Admin SDK 共通の検出フラグ |
| Auth Emulator port | `9099` | REST / SDK 接続先 |
| Emulator UI port | `4000` | ブラウザ UI（mock user 管理） |
| project id | 任意（例 `demo-project`） | エミュレーター内で完結する識別子 |

### backend 契約（firebase-auth-setup / mfa の差分）

| 操作 | エミュレーター時の振る舞い |
|---|---|
| `verify_token(id_token)` | ID トークンは **unsigned**。EMULATOR_HOST 設定時は **署名検証をスキップ**してデコードし、`iss=https://securetoken.google.com/<project>` / `aud=<project>` / `exp` / `sub` を手動検証する。`firebase.sign_in_second_factor`（SMS の場合 `"phone"`）も従来どおり読む（`firebase-auth-mfa`）。 |
| `delete_user(uid)` / `revoke(uid)` / `mfa_enrolled?(uid)` | Admin REST のホストを `http://${EMULATOR_HOST}/identitytoolkit.googleapis.com` に切替、`Authorization: Bearer owner`。サービスアカウント鍵は不要。 |
| `require_mfa!` | クレーム読みは本番と同じ。**SMS MFA で第2要素を満たすトークン** が入ってくれば `mfa_satisfied?=true`。 |

### client 契約（firebase-auth-frontend / mfa の差分）

| 操作 | エミュレーター時の振る舞い |
|---|---|
| 初期化 | `connectAuthEmulator(auth, http://${EMULATOR_HOST}, { disableWarnings: true })` を初回に1回呼ぶ。 |
| SMS enrollment | 本番と同じ API。reCAPTCHA は `RecaptchaVerifier` の代わりに **テスト用の verifier** を使う（実コードは `references/nextjs.md`）。SMS コードはサーバ送信されず、エミュレーターのコンソール出力か REST で取得。 |
| TOTP enrollment | **エミュレーターでは失敗する**（#6224）。コードを残す場合は `if (!EMULATOR) await MfaClient.enrollTotp(...)` で分岐し、実 Identity Platform でのみ実行する。 |
| SMS コード自動取得（テスト） | `GET http://${EMULATOR_HOST}/emulator/v1/projects/{project}/verificationCodes` → `verificationCodes[]` から最新コードを取り、`confirmSms` に渡す。 |

## 手順（言語非依存）

1. `firebase.json` の `emulators.auth.port=9099` を設定（ポートはデフォルト推奨）。
2. `docker-compose.yml` で Auth Emulator サービス（`firebase-tools` 入り Node + JRE のイメージ）を起動。`FIREBASE_AUTH_EMULATOR_HOST` を backend / frontend サービスに渡す。
3. backend は EMULATOR_HOST を検出して、`verify_token` の **署名検証スキップ** と Admin REST の **ホスト切替**を有効化する。
4. frontend は `connectAuthEmulator(auth, http://${EMULATOR_HOST})` を呼ぶ。
5. mock user を Emulator UI（`http://localhost:4000`）か REST で作成（MFA 用に電話番号を設定可能）。
6. 基本フローを E2E：メール+PW サインイン → `POST /auth/session` → 保護リソース → 退会。
7. SMS MFA を E2E：enrollment（電話番号入力 → SMS コード取得 REST → 確定）→ challenge（再ログイン時の第2要素）→ 保護リソース。
8. TOTP MFA は **エミュレーターをバイパス**して実 Identity Platform で検証することを案件ドキュメントに明記。

## 言語・フレームワーク別レシピ

| 層 | 言語 / FW | レシピ | 状態 |
|---|---|---|---|
| 環境 | Docker | [`references/docker-compose.md`](./references/docker-compose.md) | ✅ |
| backend | Ruby on Rails | [`references/rails.md`](./references/rails.md) | ✅ |
| client | Next.js | [`references/nextjs.md`](./references/nextjs.md) | ✅ |
| その他 | — | — | 追加可（契約を満たす形で追加） |

## 既知の制約（くりかえし）

- **TOTP MFA は不可**（#6224）。設計が TOTP 主体でも、ローカル検証は SMS で代替する。
- ID トークンは **unsigned**。本番経路で署名検証スキップを誤って有効化すると重大なセキュリティ事故になる。**EMULATOR_HOST が立っているときのみ**スキップする条件分岐を必ず置く。
- Admin REST の `Bearer owner` は **エミュレーター専用**。本番は OAuth2 アクセストークン（サービスアカウント）。
- Phone Auth の reCAPTCHA / APN / Console のテスト電話番号機能はエミュレーター内では使えない。

## 判断ポイント（人間判断をスルーさせない）

- **TOTP 検証の代替方針**: ローカル E2E では SMS MFA で代替し、TOTP の実 E2E は staging / 実 Identity Platform で行う、という分担を案件 ADR に明記するか。
- **エミュレーター用 mock user の管理**: 初期データを `auth_export/` から自動インポートするか、起動ごとに手動作成するか。
- **本番 / emulator の切替戦略**: ENV だけで切るか、Docker profile で切るか。誤って本番に EMULATOR_HOST が漏れない構成にする（プロダクションビルドで参照しない、CI のシークレットに含めない）。
