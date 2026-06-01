---
name: project-backend-init
description: 案件の土台にバックエンドアプリ雛形（初期サポート: Rails API もしくは Rails+Hotwire）を生成するスキル。implementation フェーズ（/project-scaffold の土台セットアップ・モノレポ骨格生成後）で、project-scope.json の確定スタック（backend）に従い、モノレポ内にバックエンド雛形を実生成したいときに使う。土台のみ生成しドメインのモデル/エンドポイント/業務ロジックは各モジュールが上に載せる（DP-PINIT-11）。具体構成は references/<stack>.md（rails / hotwire ほか拡張可能）に分離、バージョンは tech-version-check で最新安定版を解決。
---

# Project Backend Init Skill

> SKL-12: description は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

案件土台の**バックエンドアプリ雛形**を実生成する（DP-PINIT-11 土台内製化）。初期サポートは Rails（API もしくは Rails+Hotwire）。ドメインのモデル・エンドポイント・業務ロジックは生成しない（各モジュールが土台の上に載せる）。

## 呼び出しトリガ（B-13）

`/project-scaffold` の土台セットアップで、`project-monorepo-scaffold` 完了後かつ `project-scope.json.stack.backend.status == confirmed` のときに起動。

## 前提（B-11 / tech-version-check）

バージョンは `project-stack-select` が `tech-version-check`（B-17）で解決済みで `delivery/version-matrix.md` にある（Ruby / Rails・要求最小ランタイム含む）。fresh ならそれを使い、なければ `tech-version-check` を実行（B-13 skip。FW が要求する最小ランタイムは gemspec で都度確認・数値固定しない）。固定が必要なら人間判断。

## スコープと責務分担（responsibility_split）

| 項目 | owner |
|---|---|
| バックエンドアプリ雛形（起動・DB 接続核・lint 連携） | backend |
| （Hotwire 選択時の最小ビュー層） | backend |

> 単層（backend）。複数層にまたがらないため独立 Skill のまま（B-19）。Hotwire のフロント描画も Rails 内に閉じるため backend 扱い。

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`stack.backend`）
- 出力: モノレポ内のバックエンド雛形 ＋ `implementation-plan.schema.json` 準拠の生成計画。
- スキーマは編集しない（CONV-14）。

## 言語・FW 別レシピ

| stack | references | templates | state |
|---|---|---|---|
| `rails` | `references/rails.md` | `templates/rails/` | ⬜ 未実装（`/aid-references-new` で起こす） |
| `hotwire` | `references/hotwire.md` | `templates/hotwire/` | ⬜ 未実装 |
| `express` / `hono` / `aws-managed`（将来） | — | — | 未着手（DP-AID-04） |

## 実装契約（言語非依存）

- モノレポ内に**バックエンドの器**（起動・DB 接続核・設定・lint 連携）を生成する。
- ルート共有設定（lint/format/CI 核）を**継承**する（最小核は project-init 所有・DP-PINIT-10）。
- ドメインのモデル・マイグレーション・エンドポイント・業務ロジックは生成しない（境界 DP-PINIT-11）。
- 環境変数は env スキーマに従い `.env` サンプルを置く（実値は置かない）。
- API か Rails+Hotwire かは `stack.backend.choice` に従う（**要件で別指定があれば要件優先**）。

## 運用契約（本番必須・言語非依存）

- 雛形は起動・DB 接続（ローカル基盤と疎通）・lint が通る状態で生成。
- バージョンはロックし `version-matrix.md` と整合。

## 手順（言語非依存）

1. `tech-version-check` で Ruby/Rails 最新版解決。
2. `stack.backend.choice`（rails / hotwire）のレシピを選ぶ。
3. ワークスペース内に雛形生成 → ルート共有設定継承 → `project-local-infra` の DB と疎通設定。
4. 起動・lint の疎通を確認し記録。

## 新しい言語・FW への展開

`/aid-references-new project-backend-init <stack>`（express / hono / aws-managed 等）で references/templates を追加（契約不変）。

## DoD（B-15）

- 確定スタックでバックエンド雛形が生成され、起動・DB 接続・lint が通る。
- モノレポのルート共有設定を継承し、`project-local-infra` の DB と疎通する。

## 既知の制約

- 複数バックエンド FW の混在は本 Skill では扱わない（1案件1バックエンド方式を基本）。
- ドメインロジックは生成しない（境界 DP-PINIT-11）。

## 判断ポイント（人間判断をスルーさせない）

- **DP-PINIT-09**（スタック選択制）/ API vs Hotwire の選択は `project-stack-select` で確定。本 Skill は従う。
- 未サポート FW を要求された場合は代替で勝手に決めず references 追加を提案（warn_and_document）。
