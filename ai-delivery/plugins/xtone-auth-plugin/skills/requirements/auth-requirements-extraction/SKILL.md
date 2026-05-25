---
name: auth-requirements-extraction
description: クライアント要件の説明から認証関連要件を抽出して requirements.schema.json に反映するスキル。新規・既存案件の要件定義フェーズで、ログイン方式（メール+パスワード/パスワードレス/OIDC）・MFA・規制・退会などの認証要件を漏れなく洗い出したいときに使う。
---

# Auth Requirements Extraction Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

クライアント要件の説明テキストから **認証モジュール（MOD-001）に関わる要件**を抽出し、`requirements.schema.json` の `use_cases` / `functional_requirements` / `non_functional_requirements` / `undecided` に反映する。要件定義フェーズ（`/req-collect`）の認証特化版。

## 入出力（スキーマ）

- 入力: クライアント要件の説明テキスト
- 出力: `schemas/requirements.schema.json`（7フィールド: project_name / overview / actors / use_cases / functional_requirements / non_functional_requirements / undecided）

スキーマは編集しない（`schemas/` は xtone-shared-plugin への symlink, CONV-14）。

## 抽出チェックリスト（認証ユースケース／T-004 スコープ）

以下の有無・要否を必ず確認し、`use_cases` / `functional_requirements` に落とす。

- [ ] メールアドレス + パスワード認証
- [ ] メールアドレス + 一時トークン（パスワードレス）認証
- [ ] OIDC（Google / Apple ID など）連携
- [ ] 既存アカウントへの認証方式の追加
- [ ] パスワード変更 / パスワードリセット
- [ ] メールアドレス変更
- [ ] 退会（アカウント削除）
- [ ] バックエンド: API の JWT 認可 / ログインセッション保持（Rails 等）
- [ ] フロント・アプリ: セッション保持 / JWT を用いた API リクエスト

非機能・規制（`non_functional_requirements`）として確認:

- [ ] 対象ユーザ規模（DP-007 の判断軸）
- [ ] セキュリティ規制・業界要件（金融/医療/B2B など → DP-008 MFA、DP-015 dAccount）
- [ ] docomo / dメニュー系連携の有無（→ DP-015）

## 手順

1. 説明テキストを読み、上記チェックリストで認証要件を洗い出す。
2. 7フィールドへマッピングする（`project_name` / `overview` は案件全体、認証は `use_cases` 等へ）。
3. 不足・曖昧な点は人間に質問する。
4. 人間判断が必要な点（スタック・MFA・dAccount 等）は勝手に決めず、`undecided` に `DP-007` / `DP-008` / `DP-015` を追加し、`docs/pending-decisions.md` に起票する。

## 判断ポイント（人間判断をスルーさせない）

要件段階で確定しない認証方針は AI が決めない。推奨だけ提示し、未決は `undecided` と `docs/pending-decisions.md` に残す。設計フェーズ（`/auth-design`）の authentication-architect が DP-007/008/015 を引き継ぐ（T-002 warn_and_document）。
