---
name: project-local-infra
description: 案件の土台にローカル開発基盤（初期サポート: docker-compose・.env・DB 等）を生成するスキル。implementation フェーズ（/project-scaffold の土台セットアップ）で、project-scope.json の確定スタック（local_infra）に従い、フロント/バックが疎通するローカル開発環境の土台を実生成したいときに使う。local_dev_stack=emulator_docker を既定とし実クラウド接続は本番のみ（B-12）。具体構成は references/<stack>.md（docker-compose ほか拡張可能）に分離。
---

# Project Local Infra Skill

> SKL-12: description は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

案件土台の**ローカル開発基盤**（docker-compose・.env・DB 等）を実生成する（DP-PINIT-11 土台内製化）。`local_dev_stack=emulator_docker` を既定とし、実クラウドサービス接続は本番のみ（B-12 協調）。

## 呼び出しトリガ（B-13）

`/project-scaffold` の土台セットアップで、`project-monorepo-scaffold` 完了後かつ `project-scope.json.stack.local_infra.status == confirmed` のときに起動。バックエンド雛形（DB 接続）と疎通するため、`project-backend-init` と前後して実行。

## 前提（B-11 / tech-version-check）

バージョンは `project-stack-select` が `tech-version-check`（B-17）で解決済みで `delivery/version-matrix.md` にある（Docker / DB（PostgreSQL 等）イメージ）。fresh ならそれを使い、なければ `tech-version-check` を実行（B-13 skip）。バージョンは固定しない。固定が必要なら人間判断。

## スコープと責務分担（responsibility_split）

| 項目 | owner |
|---|---|
| docker-compose・.env サンプル・DB/補助サービスのローカル起動 | iaas |

> 単層（iaas）。複数層にまたがらないため独立 Skill のまま（B-19）。

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`stack.local_infra` / `selected_modules`）
- 出力: ローカル基盤一式（docker-compose・.env サンプル・初期化スクリプト）＋ `implementation-plan.schema.json` 準拠の生成計画。
- スキーマは編集しない（CONV-14）。

## 言語・FW 別レシピ

| stack | references | templates | state |
|---|---|---|---|
| `docker-compose` | `references/docker-compose.md` | `templates/docker-compose/` | ⬜ 未実装（`/aid-references-new` で起こす） |
| クラウド直結（将来） | — | — | 未着手（DP-AID-04） |

## 実装契約（言語非依存）

- フロント/バックが疎通する**ローカル開発基盤**（DB・補助サービス）を起動できる構成を生成する。
- `.env` は**サンプルのみ**（実値・シークレットは置かない・MCP-08）。
- `local_dev_stack=emulator_docker` 既定：実クラウド接続は本番経路のみ（ローカルはエミュレータ/コンテナ）。
- `project-backend-init` の DB 接続核と整合する DB 名・ポート・認証情報（サンプル）を提供する。

> **要件で別指定があれば要件優先**（既定の emulator_docker より案件要件を優先）。

## 運用契約（本番必須・言語非依存）

- `docker compose up` で DB/補助サービスが起動し、バックエンドが接続できる。
- 本番経路（実クラウド）とローカル経路（コンテナ/エミュレータ）を分離する。

## 手順（言語非依存）

1. `tech-version-check` で Docker/DB イメージ版を解決。
2. `stack.local_infra.choice`（docker-compose）のレシピを選ぶ。
3. docker-compose・.env サンプル・初期化スクリプトを生成。
4. `project-backend-init` の DB 接続と疎通確認。

## 新しい基盤方式への展開

`/aid-references-new project-local-infra <stack>` で references/templates を追加（契約不変）。

## DoD（B-15）

- `docker compose up` で DB/補助サービスが起動し、バックエンド雛形が接続できる。
- `.env` はサンプルのみでシークレットを含まない。

## 既知の制約

- 本番インフラ（IaC・クラウドプロビジョニング）は本 Skill のスコープ外（ローカル基盤のみ）。
- シークレット実値は生成しない（サンプルのみ）。

## 判断ポイント（人間判断をスルーさせない）

- **DP-PINIT-09**（スタック選択制）: local_infra の確定は `project-stack-select`。本 Skill は従う。
- 実クラウド前提のローカル構成が要求された場合は、B-12（既定 emulator_docker）との差異を未決として残す（warn_and_document）。
