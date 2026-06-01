---
name: project-module-recommendation
description: 案件のドメイン・スコープから必要なモジュール（MOD-XXX）を Notion モジュールカタログDB（MCS）／ドメインタクソノミーDB を引いて推奨提示するスキル。design フェーズ（/project-modules）で、project-scope.json をもとに必要モジュール候補を複数案＋根拠で提示し、人間が確定（recommended→confirmed）したいときに使う。AI は候補提示のみ・確定は人間（DP-PINIT-02 warn_and_document）。module-advisor Subagent から起動される。
---

# Project Module Recommendation Skill

> SKL-12: description は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

案件のドメイン・スコープに対して**必要なモジュールプラグイン群を推奨提示**する（DP-PINIT-02 accepted: AI推奨＋人間確定）。AI は MCS（モジュールカタログ）／ドメインタクソノミーを参照して候補と根拠を出すのみで、**選定確定は人間**が行う（T-002 人間判断をスルーさせない）。

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`domain` / `scale` / `constraints`）＋ Notion MCS / ドメインタクソノミー
- 出力: `project-scope.json.selected_modules`（各 `{module_id, status, rationale}`。`status` は `recommended` → 人間確定で `confirmed`、不採用は `rejected`）
- スキーマは編集しない（CONV-14）。

## 手順

1. `project-scope.json.domain` / 制約を読む。
2. Notion MCS（`a983ee9b-9f4c-4e76-810e-3ed7b1bb1462`）／ドメインタクソノミー（`cddc07df-d76e-4ff9-a0c4-5b32d8027097`）を引き、適用ドメインが一致するモジュールを抽出。
3. 各候補を**根拠（ドメイン適合・典型要件・依存）つき**で複数案提示し、`status: "recommended"` で記録。
4. **人間に確定を仰ぐ**（AI は決めない）。確定したものを `confirmed`、外したものを `rejected`。
5. 未確定は warn_and_document で残す。確定後、次アクション（`/project-scaffold`）を案内。

## 差し替え可能設計（参照源・T-004 適応）

モジュールカタログの参照源（Notion）は adapter 越しに読む設計余地を残し、参照源（Notion / ローカルキャッシュ / 将来別 SoT）を差し替え可能に保つ。直接 Notion SDK を全所で叩く実装は避ける。

## 判断ポイント（人間判断をスルーさせない）

- **DP-PINIT-02**（モジュール選定の主体）: AI は候補提示のみ・確定は人間。自動確定しない。
- カタログに該当が薄い案件は、無理に既存モジュールへ寄せず未決として残し、新規モジュール起票の要否を人間に上げる（warn_and_document）。
