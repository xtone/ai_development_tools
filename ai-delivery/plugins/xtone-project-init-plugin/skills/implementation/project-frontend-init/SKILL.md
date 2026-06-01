---
name: project-frontend-init
description: 案件の土台にフロントエンドアプリ雛形（初期サポート: Next.js）を生成するスキル。implementation フェーズ（/project-scaffold の土台セットアップ・モノレポ骨格生成後）で、project-scope.json の確定スタック（frontend）に従い、モノレポのワークスペース内にフロントエンド雛形を実生成したいときに使う。土台のみ生成しドメイン UI/機能は各モジュールが上に載せる（DP-PINIT-11）。具体構成は references/<stack>.md（nextjs ほか拡張可能）に分離、バージョンは tech-version-check で最新安定版を解決。
---

# Project Frontend Init Skill

> SKL-12: description は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

案件土台の**フロントエンドアプリ雛形**を実生成する（DP-PINIT-11 土台内製化）。初期サポートは Next.js。具体手順は references に分離し、ドメイン UI/機能は生成しない（各モジュールが土台の上に載せる）。

## 呼び出しトリガ（B-13）

`/project-scaffold` の土台セットアップで、`project-monorepo-scaffold` 完了後（ワークスペースが存在）かつ `project-scope.json.stack.frontend.status == confirmed` のときに起動。

## 前提（B-11 / tech-version-check）

バージョンは `project-stack-select` が `tech-version-check`（B-17）で解決済みで `delivery/version-matrix.md` にある（Node（Active LTS）/ Next.js）。fresh ならそれを使い、なければ `tech-version-check` を実行（B-13 skip）。バージョンは固定しない。固定が必要なら人間判断。

## スコープと責務分担（responsibility_split）

| 項目 | owner |
|---|---|
| フロントエンドアプリ雛形（ルーティング核・ビルド/起動・lint 連携） | client |

> 単層（client）。複数層にまたがらないため独立 Skill のまま（B-19）。

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`stack.frontend`）
- 出力: モノレポ内のフロントエンド雛形 ＋ `implementation-plan.schema.json` 準拠の生成計画。
- スキーマは編集しない（CONV-14）。

## 言語・FW 別レシピ

| stack | references | templates | state |
|---|---|---|---|
| `nextjs` | `references/nextjs.md` | `templates/nextjs/` | ⬜ 未実装（`/aid-references-new` で起こす） |
| `vuejs`（将来） | — | — | 未着手（DP-AID-04: 案件で必要時） |

## 実装契約（言語非依存）

- モノレポのワークスペース内に**フロントの器**（ルーティング核・共有設定継承・ビルド/起動スクリプト）を生成する。
- ルート共有設定（lint/format/型）を**継承**する（最小核は project-init 所有・DP-PINIT-10）。フロント固有設定はワークスペース側に置く。
- ドメイン画面・機能は生成しない（境界 DP-PINIT-11）。
- 環境変数は env スキーマに従い `.env` サンプルを置く（実値は置かない）。

> **要件で別指定があれば要件優先**。

## 運用契約（本番必須・言語非依存）

- 雛形はビルド・起動・lint が通る状態で生成する。
- バージョンはロックし `version-matrix.md` と整合。

## 手順（言語非依存）

1. `tech-version-check` で最新版解決。
2. `stack.frontend.choice` のレシピ（references）を選ぶ。
3. ワークスペース内に雛形生成 → ルート共有設定を継承。
4. 起動・lint の疎通を確認し記録。

## 新しい言語・FW への展開

`/aid-references-new project-frontend-init <stack>` で references/templates を追加（契約不変）。

## DoD（B-15）

- 確定スタックでフロント雛形が生成され、ビルド/起動/lint が通る。
- モノレポのルート共有設定を継承している。

## 既知の制約

- 複数フロント FW の混在は本 Skill では扱わない（1案件1フロント方式を基本）。

## 判断ポイント（人間判断をスルーさせない）

- **DP-PINIT-09**（スタック選択制）: 確定は `project-stack-select`。本 Skill は確定済みに従う。
- 未サポート FW を要求された場合は代替で勝手に決めず、references 追加を提案（warn_and_document）。
