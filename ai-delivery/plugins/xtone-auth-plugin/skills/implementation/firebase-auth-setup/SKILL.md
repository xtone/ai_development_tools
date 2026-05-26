---
name: firebase-auth-setup
description: Firebase Auth を任意のバックエンドに統合するスキル。実装フェーズで、design.schema.json の認証設計に従い、差し替え可能な認証アダプタ・JWT 検証・退会時の Admin SDK 削除・公開鍵キャッシュ・トークン失効を実装したいときに使う。言語/FW 非依存の契約と手順を定義し、具体コードは references/ の言語別レシピに分離（現状 Rails、Node 等は追加可能）。
---

# Firebase Auth Setup Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`design.schema.json` の認証設計を実装に落とす。本スキルは **言語・フレームワーク非依存の「契約」と「手順」**を定義し、具体的なコードは `references/<stack>.md`（言語別レシピ）に分離する。MVP は Firebase Auth、`AuthAdapter` で IaaS 差し替え可能（DP-007）。

> 設計方針: 言語が変わっても **契約は不変**、実装手段（SDK/コード）だけがレシピごとに変わる。Rails 固定にせず、Node/Laravel 等へ展開できる構造にする。

> **スコープ: バックエンド（サーバ）専用。** ID トークン検証・JWT 認可・退会時の Admin SDK 削除・トークン失効など。フロントエンド（サインインUI・パスワード/メール変更・トークン保持・API への Bearer 付与）は対の [`firebase-auth-frontend`](../firebase-auth-frontend/SKILL.md) を参照。`responsibility_split` の **backend = 本スキル / client = firebase-auth-frontend / iaas = Firebase が提供**。MFA（多要素認証, DP-008）は client/backend/iaas 横断のため対の [`firebase-auth-mfa`](../firebase-auth-mfa/SKILL.md) に集約（本スキルが担う MFA 部分は「クレーム検証・管理者強制・変更時の失効」）。

> **ローカル検証（Docker で Auth Emulator 起動・E2E）**は対の [`firebase-auth-emulator`](../firebase-auth-emulator/SKILL.md) を参照。`FIREBASE_AUTH_EMULATOR_HOST` 検出時の **署名検証スキップ**と **Admin REST の host 切替（`Bearer owner`）** はそちらに集約し、本スキルの本番経路（RS256 + サービスアカウント）と分離する。

## 入出力（スキーマ）

- 入力: `schemas/design.schema.json`（`authentication.stack` / `architecture.stack` / decision_record）
- 出力: 実装コード + `schemas/implementation-plan.schema.json`

スキーマは編集しない（CONV-14）。

## 言語・フレームワーク別レシピ

design の `architecture.stack` / 採用言語を見て、該当レシピを参照する。レシピが無い言語は、下記「新しい言語・FW への展開」に従って追加してから実装する。

| 言語 / FW | レシピ | 状態 |
|---|---|---|
| Ruby on Rails | [`references/rails.md`](./references/rails.md) | ✅ |
| Node.js / Express | `references/node.md` | ⬜ 未作成（rails.md を雛形に追加） |
| Laravel (PHP) | `references/laravel.md` | ⬜ 未作成 |
| その他 | — | 追加可 |

## 実装契約（言語非依存）

すべてのレシピは以下の契約を満たす。

### AuthAdapter（差し替え可能設計の核, DP-007）

| メソッド | 契約 |
|---|---|
| `verify_token(id_token) → AuthUser` | ID トークン(JWT)を検証し uid/email/provider を返す。無効なら InvalidToken。失効済みも拒否。 |
| `get_user(uid) → AuthUser` | ユーザー取得。 |
| `delete_user(uid)` | IaaS 上のユーザー削除（退会）。**冪等**（既に無くても成功）。 |
| `revoke(uid)` | リフレッシュトークン失効。 |

アプリ本体は `AuthAdapter` にのみ依存する。Firebase 固有処理は `FirebaseAuthAdapter` に閉じ込め、別 IaaS は別実装（例: `DeviseAuthAdapter`）に差し替える。テストは同契約の `TestAdapter` で実 IaaS なしに回す。

### 運用契約（本番必須・言語非依存）

T-022 パイロット発見 F-3 / Issue #127 の解消。

1. **退会時の IaaS ユーザー削除**: Admin SDK（サービスアカウント鍵、コミット禁止）で削除。冪等。
2. **公開鍵（証明書）キャッシュ**: 検証鍵は HTTP の `Cache-Control: max-age` に従いキャッシュ。`kid` 不一致時は強制再取得（鍵ローテーション追従）。
3. **トークン失効 / リフレッシュ**: ID トークン短命＋リフレッシュトークン。退会・パスワード変更・MFA 変更・不正検知時はサーバ側で失効し、以後 `auth_time` が失効時刻より前のトークンを拒否。

## 手順（言語非依存）

1. design の採用スタックを確認し、該当レシピ（`references/<stack>.md`）を開く。無ければ新レシピを追加。
2. Firebase プロジェクト / サービスアカウント鍵を用意（`.env` / Secrets、コミット禁止）。
3. `AuthAdapter` 契約を実装する（`FirebaseAuthAdapter`）。
4. API で JWT を検証してユーザーを解決する。
5. クライアントでセッション（ID/リフレッシュトークン）を保持し、API リクエストに付与する。
6. **運用契約**（退会削除・証明書キャッシュ・トークン失効）を実装する。
7. ローカル動作確認（テストは `TestAdapter` で実 Firebase 不要）。
8. 実装タスク・依存・テスト方針を `implementation-plan.schema.json` に記録する。

## 新しい言語・FW への展開

1. `references/<stack>.md` を作成する（例: `node.md`, `laravel.md`）。[`references/rails.md`](./references/rails.md) を雛形にする。
2. 上記 **実装契約**（AuthAdapter ＋ 運用契約）を、その言語の SDK / エコシステムで満たすコードを記述する。
3. **契約は変えない**（差し替え可能設計を維持）。上のレシピ表に1行追加する。
4. 言語特有の制約（例: Ruby に公式 Admin SDK が無く REST で代替）はレシピの「既知の制約」に明記する。

## 判断ポイント（人間判断をスルーさせない）

設計で未決のまま実装に来た判断（DP-008 MFA の有効化方法など）は実装で勝手に確定しない。`undecided` に残し `docs/pending-decisions.md` に起票する（T-002 warn_and_document）。MFA の実装パターン（TOTP/SMS、管理者必須・一般オプトイン）は [`firebase-auth-mfa`](../firebase-auth-mfa/SKILL.md) スキルを参照する。
