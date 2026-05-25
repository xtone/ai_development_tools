---
name: firebase-auth-design
description: Firebase Auth を使った認証設計をガイドするスキル。認証モジュールを設計するフェーズで、認証スタック比較（DP-007）・MFA 規則（DP-008）・dAccount/docomo 規約（DP-015）・セッション設計を含む design.schema.json を作りたいときに使う。MVP は Firebase Auth、IaaS 差し替え可能設計を前提とする。
---

# Firebase Auth Design Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`requirements.schema.json` の認証要件から `design.schema.json` を生成する。MVP では **Firebase Auth** を推奨しつつ、**最低 1 つの代替スタックを比較**し、IaaS 差し替え可能な設計を担保する（T-004 本決定）。authentication-architect Subagent が本スキルを使う。

## 入出力（スキーマ）

- 入力: `schemas/requirements.schema.json`（認証関連要件）
- 出力: `schemas/design.schema.json`（`tech_stack` / `architecture` / `decision_record` / `undecided` 等）、必要に応じ `docs/adr/ADR-NNN.md`

スキーマは編集しない（CONV-14）。

## 手順

1. requirements の `representative_use_cases` / `functional_requirements` / `non_functional_requirements` から認証要件（ログイン方式・MFA・規制・ユーザ規模）を読み取る。
2. **DP-007**: Firebase Auth と代替（例: Devise+OmniAuth / Cognito）を比較表にし、MVP 推奨と根拠を述べる。`tech_stack` に採用案を入れ、差し替え可能設計（認証アダプタ層）を `architecture` に明記する。
3. **DP-008**: MFA 方針を案件条件に当てはめ、決められなければ推奨だけ提示。
4. **DP-015**: docomo 系案件なら dAccount 規約遵守タイミングを設計に織り込む。非該当ならスコープ外と明記。
5. セッション設計（TTL、JWT 失効、リフレッシュ方針）を `architecture` に記述。
6. 決定済みは `decision_record`（decided_by / decided_at / rationale）に、未決は `undecided` に `DP-XXX` を残す。
7. 重要な決定は `templates/ADR.template.md` を用いて `docs/adr/ADR-NNN.md` を起票する。

## 差し替え可能設計の指針（T-004 本決定）

- 認証処理（サインイン/トークン検証/ユーザ取得）を **アダプタインターフェース**越しに呼ぶ。
- Firebase 固有 SDK 呼び出しはアダプタ実装に閉じ込め、アプリ本体は抽象に依存させる。
- 別 IaaS 追加時はアダプタ実装の差し替えのみで済む構造にする（Rollout で実証）。

## テンプレート

- `templates/ADR.template.md` — アーキテクチャ決定記録
- `templates/auth-section.template.md` — 設計書の認証セクション雛形

## 判断ポイント（人間判断をスルーさせない）

DP-007/008/015 は AI が勝手に決めず、推奨だけ提示する。未決は `docs/pending-decisions.md` と `undecided` に記録（T-002 warn_and_document）。
