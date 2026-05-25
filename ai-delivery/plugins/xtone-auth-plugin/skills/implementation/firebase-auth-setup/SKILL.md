---
name: firebase-auth-setup
description: Firebase Auth をプロジェクトにセットアップする手順とコードサンプルを提供するスキル。実装フェーズで、design.schema.json の認証設計に従って Firebase Admin SDK 設定・JWT 検証・差し替え可能な認証アダプタを実装したいときに使う。
---

# Firebase Auth Setup Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`design.schema.json` の認証設計を実装に落とす。Firebase Admin SDK のセットアップ、JWT 認可、ログインセッション保持、そして **IaaS 差し替え可能な認証アダプタ層**の雛形を提供する。`implementation-plan.schema.json` のタスクに対応する。

## 入出力（スキーマ）

- 入力: `schemas/design.schema.json`（採用スタック・アーキテクチャ・decision_record）
- 出力: 実装コード + `schemas/implementation-plan.schema.json`（tasks / milestones / dependencies / test_plan / undecided）

スキーマは編集しない（CONV-14）。

## 手順

1. Firebase Console でプロジェクトを作成し、サービスアカウントキーを取得する（鍵は `.env` 管理、コミット禁止）。
2. Admin SDK をインストールする（Rails: `firebase-auth-rails` 相当 / Node: `firebase-admin`）。
3. `AuthAdapter` インターフェースを定義し、Firebase 実装（`FirebaseAuthAdapter`）を作る（差し替え可能設計, DP-007）。
4. API ミドルウェアで JWT を検証し、ユーザーを解決する（バックエンドの JWT 認可）。
5. フロント/アプリでセッション（IDトークン/リフレッシュトークン）を保持し、API リクエストに付与する。
6. ダミーメールパターン等でローカル動作確認をする。
7. 実装タスク・依存・テスト方針を `implementation-plan.schema.json` に記録する。

## 認証アダプタ層（差し替え可能設計の核）

```
AuthAdapter (interface)
  ├─ verify_token(id_token) -> AuthUser
  ├─ sign_in(...) / sign_out(...)
  └─ get_user(uid) -> AuthUser

FirebaseAuthAdapter implements AuthAdapter   # MVP
DeviseAuthAdapter   implements AuthAdapter   # 代替例（Rollout で実証）
```

アプリ本体は `AuthAdapter` にのみ依存する。Firebase 固有処理は `FirebaseAuthAdapter` に閉じ込める。

## 判断ポイント（人間判断をスルーさせない）

設計で未決のまま実装に来た判断（DP-008 MFA の有効化方法など）は実装で勝手に確定しない。`undecided` に残し `docs/pending-decisions.md` に起票する（T-002 warn_and_document）。
