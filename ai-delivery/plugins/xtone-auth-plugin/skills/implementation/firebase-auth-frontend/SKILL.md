---
name: firebase-auth-frontend
description: Firebase Auth をフロントエンド（クライアント）に統合するスキル。実装フェーズで、サインイン（メール/パスワードレス/OIDC）・パスワード変更/リセット・メール変更・トークン保持と API への Bearer 付与・セッション復元を実装したいときに使う。言語/FW 非依存の AuthClient 契約を定義し、具体コードは references/（Hotwire / Next.js）に分離。バックエンド側は firebase-auth-setup を参照。
---

# Firebase Auth Frontend Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`design.schema.json` の認証設計のうち、`responsibility_split` で **`client`** に仕分けた機能をフロントエンドに実装する。本スキルは **言語/FW 非依存の AuthClient 契約**を定義し、具体コードは `references/<stack>.md` に分離する（バックエンドの [`firebase-auth-setup`](../firebase-auth-setup/SKILL.md) と対の構造）。

> 役割分担: **Firebase クライアント SDK** が認証フロー（サインイン・パスワード/メール変更等）を担い、**サーバ（firebase-auth-setup）** は ID トークンの検証のみ。フロントは取得した ID トークンを API に Bearer で渡す。

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
