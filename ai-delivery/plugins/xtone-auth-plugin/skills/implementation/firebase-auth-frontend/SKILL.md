---
name: firebase-auth-frontend
description: Firebase Auth をフロントエンド（クライアント）に統合するスキル。実装フェーズで、サインイン（メール/パスワードレス/OIDC）・パスワード変更/リセット・メール変更・トークン保持と API への Bearer 付与・セッション復元を実装したいときに使う。言語/FW 非依存の AuthClient 契約を定義し、具体コードは references/（Hotwire / Next.js）に分離。バックエンド側は firebase-auth-setup を参照。
---

# Firebase Auth Frontend Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`design.schema.json` の認証設計のうち、`responsibility_split` で **`client`** に仕分けた機能をフロントエンドに実装する。本スキルは **言語/FW 非依存の AuthClient 契約**を定義し、具体コードは `references/<stack>.md` に分離する（バックエンドの [`firebase-auth-setup`](../firebase-auth-setup/SKILL.md) と対の構造）。

## 呼び出しトリガ（B-13）

以下のいずれかに該当する設計成果物が来たら **必ず本スキルを起動**する。判定は `implementation-skill-planner` が行い、`implementation-plan.json.skill_plan` に列挙する。手動判断で省略しない（B-13 由来。サンプル案件で frontend スキルが素通りされた）:

- `design.yaml.responsibility_split[].owner` に **`client` または `shared`** が含まれる
- `design.yaml.page_access_control.pages` に 1 件以上の定義がある（A/B/C パターンの実装が必要）

未呼び出しのまま実装フェーズが完了に到達した場合は `delivery/implementation-skill-plan.md` の `called` が false で残り、`docs/pending-decisions.md` に「未呼び出しスキル」として警告される（warn_and_document, T-002）。

> 役割分担: **Firebase クライアント SDK** が認証フロー（サインイン・パスワード/メール変更等）を担い、**サーバ（firebase-auth-setup）** は ID トークンの検証のみ。フロントは取得した ID トークンを API に Bearer で渡す。

> **MFA（多要素認証, DP-008）は本スキルの対象外。** 第2要素の登録（enrollment）・サインイン時の追加認証（challenge）も client 実装だが、backend/iaas にまたがる横断機能のため対の [`firebase-auth-mfa`](../firebase-auth-mfa/SKILL.md) に集約している。MFA を実装するときはそちらを参照。

> **ローカル検証（Docker で Auth Emulator 起動・E2E）**は対の [`firebase-auth-emulator`](../firebase-auth-emulator/SKILL.md) を参照。`connectAuthEmulator` の初期化と **SMS MFA での E2E 検証**手順をそちらに集約（TOTP MFA はエミュレーター非対応のため、ローカルは SMS で代替し TOTP の E2E は実 Identity Platform）。

## 入出力（スキーマ）

- 入力: `schemas/design.schema.json`（`authentication` / `responsibility_split` の client 項目 / セッション戦略）
- 出力: フロント実装コード + `schemas/implementation-plan.schema.json`

スキーマは編集しない（CONV-14）。

## 言語・フレームワーク別レシピ

| FW | レシピ | 状態 |
|---|---|---|
| Ruby on Rails + Hotwire | [`references/hotwire.md`](./references/hotwire.md) | ✅ |
| Next.js | [`references/nextjs.md`](./references/nextjs.md) | ✅ |
| その他（Vue / Flutter 等） | — | 追加可（rails 同様に契約を満たす） |

## 実装契約（FW 非依存）— AuthClient

| メソッド | 契約 | responsibility |
|---|---|---|
| `signInWithPassword(email, pw)` | メール+パスワードでサインイン | client + iaas |
| `signInWithEmailLink(email)` / `completeEmailLink()` | パスワードレス（メールリンク） | client + iaas |
| `signInWithOIDC(provider)` | Google / Apple 等 | client + iaas |
| `linkProvider(provider)` | 認証方式の追加（UC-A04） | client |
| `sendPasswordReset(email)` / `updatePassword(new)` | パスワードリセット / 変更 | iaas（Firebase が完結） |
| `updateEmail(new)` | メールアドレス変更 | iaas |
| `signOut()` | サインアウト（ローカルのトークン破棄） | client |
| `getIdToken({forceRefresh})` | API 呼び出し用 ID トークン取得（期限切れは自動リフレッシュ） | client |
| `onAuthStateChanged(cb)` | セッション復元・認証状態の購読 | client |
| `withdraw()` | 退会トリガ。サーバの `DELETE /account` を呼ぶ（IaaS 削除は backend） | shared |

アプリは `AuthClient` 越しに Firebase を呼ぶ。API 呼び出しには `getIdToken()` の Bearer を付け、サーバ（firebase-auth-setup）が検証する。

## デフォルトページ構成と認証アクセス制御

スキルが既定で要求するページ構成と振る舞い。**要件で別指定がある場合は要件優先**（`design` に `page_access_control` を追加して逸脱を明示・warn_and_document）。

### 3 つのアクセス制御パターン

| パターン | 名前 | ログイン時 | ログアウト時 |
|---|---|---|---|
| **A** | `protected-only`（認証必須） | 表示 | **`/login?callback=<元URL>` へリダイレクト** |
| **B** | `public-aware`（認証感知・公開） | 認証状態でコンテンツ切替（リダイレクトなし） | 同（リダイレクトなし） |
| **C** | `guest-only`（ゲスト専用） | **`callback`（または既定遷移先）へリダイレクト** | 表示 |

### デフォルトページ一覧（要件で別指定がない限り採用）

| パス | パターン | 振る舞い |
|---|---|---|
| `/login` | C: guest-only | サインイン。`?callback=<path>` を受け取り、ログイン後にそのパスへ遷移。`/signup` と**相互リンク**し callback を引き継ぐ |
| `/signup` | C: guest-only | 新規登録。**`/login` と別ページ**・相互リンク。`callback` を引き継ぐ |
| `/mfa/enroll` | A: protected-only | MFA 第2要素登録（[`firebase-auth-mfa`](../firebase-auth-mfa/SKILL.md) と組み合わせ） |
| `/settings/*`（退会・PW変更・メール変更 等） | A: protected-only | アカウント設定 |
| `/`（トップ） | B: public-aware | 認証状態でコンテンツ切替 |

> 案件のページが上記に無い場合は **A/B/C を明示**して `page_access_control` に追加する。デフォルトに反する設定（例: `/settings` を `public-aware` に開放する等）が要件で出たら、`design.decision_record` に根拠を残して逸脱を記録する。

### コールバックURL の仕様（共通契約）

- パラメータ名: **`callback`**（プロジェクトで統一）
- 値は **同一オリジンのパス**（先頭 `/`、外部 URL 不可）。**open redirect 防止**のため、`//` 始まり・絶対 URL・別ホストは拒否し、既定遷移先にフォールバック
- 既定遷移先（未指定時）: `/`（トップ）。案件で別にする場合は `page_access_control.default_after_login` を明示
- `/login` ↔ `/signup` の相互リンクは `callback` を**そのまま引き継ぐ**（ユーザーが行き来しても遷移先が保たれる）
- パターン A のページに未認証でアクセスした場合は `callback=<元URL>` を付けて `/login` にリダイレクト

### ガード実装契約（FW 非依存）

| パターン | 実装の意図 |
|---|---|
| A: protected-only | レンダー前にセッション無を検出してリダイレクト。**子コンテンツは認証確定後にのみマウント**。ローディング中はスケルトン |
| B: public-aware | 認証状態を子に渡すだけ。リダイレクトなし。SSR/RSC では session cookie を見て切替 |
| C: guest-only | セッション有を検出してリダイレクト。`callback` 優先・無ければ既定遷移先 |

各レシピ（`references/<stack>.md`）は **3 パターンの雛形**と上記**デフォルトページのスケルトン**を含む。

## バックエンド連携（firebase-auth-setup と対）

- ログイン後: `getIdToken()` → `POST /auth/session`（サーバがユーザーを upsert）
- API: `Authorization: Bearer <idToken>`（サーバが検証）
- 退会: `DELETE /account`（サーバが論理削除 ＋ Admin SDK で IaaS 削除）
- `responsibility_split`: **client = 本スキル / backend = firebase-auth-setup / iaas = Firebase が提供**

## 判断ポイント（人間判断をスルーさせない / DP相当）

セッション戦略は AI が決めず推奨だけ提示する:

- **トークン保持**: メモリ保持＋自動リフレッシュ（推奨。XSS 配慮で `localStorage` を避ける）/ Rails のクッキーセッションに載せ替え（SSR 主体なら有力）
- **Next.js の経路**: クライアントから Rails API へ直接 Bearer / BFF（Next.js Route Handler 経由でトークンを秘匿）

決められない場合は `undecided` と `docs/pending-decisions.md` に残す（T-002 warn_and_document）。

## 手順

1. design の `responsibility_split` から `client` 項目を確認する。
2. 採用 FW のレシピ（`references/<stack>.md`）を開く。無ければ追加。
3. `AuthClient` 契約を実装する。
4. ログイン → `POST /auth/session`、API への Bearer 付与、`onAuthStateChanged` でセッション復元を実装する。
5. セッション戦略を人間に確認する（DP）。
6. 実装タスク・依存・テスト方針を `implementation-plan.schema.json` に記録する。
7. **DoD（B-15）**: 本スキルだけで完了扱いにしない。`design.yaml.representative_use_cases` および `page_access_control.pages` の **A/B/C ガード・サインインフロー・MFA enrollment 等を [`auth-e2e-verify`](../../test/auth-e2e-verify/SKILL.md) でブラウザ実機検証 PASS** するまでが完了。`delivery/e2e-verification-report.md` に通過証跡を残す。DP 決定済みなのに未実装な UC（例: パスワード変更画面、退会導線）があれば pending-decisions に警告として残す（warn_and_document）。
