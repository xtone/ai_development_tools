---
name: auth-requirements-extraction
description: クライアント要件の説明から認証関連要件を抽出して requirements.schema.json に反映するスキル。新規・既存案件の要件定義フェーズで、ログイン方式（メール+パスワード/パスワードレス/OIDC）・MFA・規制・退会などの認証要件を漏れなく洗い出したいときに使う。
---

# Auth Requirements Extraction Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

クライアント要件の説明テキストから **認証モジュール（MOD-001）に関わる要件**を抽出し、`requirements.schema.json`（T-011 本実装）の `scope` / `representative_use_cases` / `functional_requirements` / `non_functional_requirements` 等に反映する。要件定義フェーズ（`/req-collect`）の認証特化版。

## 入出力（スキーマ）

- 入力: クライアント要件の説明テキスト
- 出力: `schemas/requirements.schema.json`（T-011 本実装。必須: scope / representative_use_cases / functional_requirements / non_functional_requirements / domain_tags / stakeholders / client_approval。warn_and_document 用に undecided を追加保持）

スキーマは編集しない（`schemas/` は xtone-shared-plugin への symlink, CONV-14）。

## 抽出チェックリスト（認証ユースケース／T-004 スコープ）

以下の有無・要否を必ず確認し、`representative_use_cases` / `functional_requirements` / `scope` に落とす。

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

## 運用方針（招待 / 監査ログ / 通知）

要件抽出段階で気づける運用系の判断ポイント。要件で言及されたら必ず `representative_use_cases` / `functional_requirements` / `non_functional_requirements` に反映し、未確定の項目は `undecided` に該当 DP を追加して `docs/pending-decisions.md` に起票する（warn_and_document）。**要件に登場しなくても**、operator 招待制／監査ログ／通知メールは BtoB 系や規制業界で実装直前まで未決のまま持ち越されやすい構造的論点なので、ヒアリングで明示的に有無を確認する。

### 招待制サインアップ（採用される場合 → DP-INVITATION-POLICY-001）

- [ ] 招待トークンの有効期限（既定: 72h / 案件指定）
- [ ] 1 回限り使い切り / 再発行ポリシー
- [ ] 招待リンク送信の通知手段（メール / Slack）
- [ ] 失効通知の有無

### 監査ログ（→ DP-AUDIT-VIEW-001）

- [ ] 対象操作（ログイン / ログアウト / パスワード変更 / 退会 / 招待発行 / role 変更 等）
- [ ] 保存期間
- [ ] 閲覧権限（operator / admin / 限定 admin 等）
- [ ] 閲覧 UI の有無（管理画面 / CSV エクスポートのみ / なし）

### 通知（→ DP-NOTIFY-001）

- [ ] 通知手段（メール / Slack / Web push / なし）
- [ ] 通知イベント（パスワード変更 / 新規ログイン / MFA 設定変更 / 退会受付 / 招待発行 等）
- [ ] オプトアウト可否
- [ ] 開発環境での実送信 vs Mailcatcher 等

## ページ単位のアクセス制御（firebase-auth-frontend と協調）

`firebase-auth-frontend` スキルは 3 パターン（**A: protected-only / B: public-aware / C: guest-only**）と既定ページ（`/login` `/signup` `/mfa/enroll` `/settings/*` `/`）を持つ。要件抽出時に**案件特有のページ**を A/B/C に振り分け、デフォルトに反する設定があれば明示する（要件で別指定がある場合は要件優先）。

- [ ] 認証必須ページ（A）の列挙（例: マイページ / 申込フォーム / 決済 / `/mfa/enroll` / `/settings/*`）
- [ ] 認証感知ページ（B、公開だが認証で表示が変わる）の列挙（例: トップ / 商品一覧）
- [ ] ゲスト専用ページ（C）の列挙（通常は `/login` と `/signup`。案件追加があれば）
- [ ] **既定遷移先（ログイン後のホーム）**: 既定 `/`。案件で別指定がある場合は明示（例 `/dashboard`）
- [ ] **callback パラメータ**の採用（既定パラメータ名 `callback`）と検証ポリシー（既定: 同一オリジンの `/` 始まりのみ・`//` 拒否で open redirect 防止）
- [ ] `/login` と `/signup` を**別ページ**で提供することの確認（既定。統合する案件指定があれば理由とともに明示）

検出した内容は `representative_use_cases` / `functional_requirements` に反映し、設計フェーズへ `page_access_control` として引き継ぐ（authentication-architect / firebase-auth-design の責務）。

## 手順

1. 説明テキストを読み、上記チェックリストで認証要件を洗い出す。
2. 各フィールドへマッピングする（`scope` で Must/Should/Could を振り分け、認証ユースケースは `representative_use_cases` / `functional_requirements` へ）。
3. 不足・曖昧な点は人間に質問する。
4. 人間判断が必要な点（スタック・MFA・dAccount・招待ポリシー・監査ログ・通知 等）は勝手に決めず、`undecided` に該当 DP（`DP-007` / `DP-008` / `DP-015` / `DP-INVITATION-POLICY-001` / `DP-AUDIT-VIEW-001` / `DP-NOTIFY-001`）を追加し、`docs/pending-decisions.md` に起票する。

## 判断ポイント（人間判断をスルーさせない）

要件段階で確定しない認証方針は AI が決めない。推奨だけ提示し、未決は `undecided` と `docs/pending-decisions.md` に残す。設計フェーズ（`/auth-design`）の authentication-architect が DP-007/008/015 と運用系 DP（DP-INVITATION-POLICY-001 / DP-AUDIT-VIEW-001 / DP-NOTIFY-001）を引き継ぐ（T-002 warn_and_document）。

運用系 DP は要件段階で抽出されないと設計 ADR で「設計フェーズで具体化する」のリスク記述として残り、実装直前まで未決のまま持ち越される構造的問題があるため、本スキルで先回りして起票する（B-22 / Issue #181）。判断ポイントカタログDB（`64248f5c-b2f5-4c90-8ccb-7f53692b59b2`）への正式採番は別途行う。
