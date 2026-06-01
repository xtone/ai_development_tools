---
name: project-monorepo-scaffold
description: 案件ルートにモノレポ骨格と共有設定（ワークスペース・共有 lint/format/CI・.gitignore・.editorconfig・全モジュール共通の最小核設定）を生成するスキル。implementation フェーズ（/project-scaffold の土台セットアップ）で、project-scope.json の確定スタック（monorepo 方式）に従って案件の土台リポジトリ構造を実生成したいときに使う。モノレポ方式は単一固定せず案件ごと選択（DP-PINIT-08）、具体構成は references/<stack>.md に分離（turborepo-pnpm / rails-js-hybrid / nx）。土台のみ生成しドメイン機能は各モジュールが上に載せる（DP-PINIT-11 境界）。
---

# Project Monorepo Scaffold Skill

> SKL-12: `description` は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

案件の**土台となるモノレポ骨格と共有設定**を実生成する（DP-PINIT-11 土台内製化・accepted）。モノレポ方式は `project-scope.json.stack.monorepo.choice` に従い、具体手順は言語別 references に分離する。**土台のみ**を作り、ドメイン機能（認証・決済等）は各モジュールプラグインが土台の上に載せる（DP-PINIT-11 境界）。

## 呼び出しトリガ（B-13）

`/project-scaffold` の土台セットアップ段で、`project-scope.json.stack.monorepo` が確定（`status: confirmed`）しているときに `implementation-skill-planner` 相当が起動する。フロント/バック/ローカル基盤の各 setup Skill より**先**に実行（ワークスペースの器を先に作る）。

## 前提（B-11 / tech-version-check）

バージョンは `project-stack-select`（design）が `tech-version-check`（B-17）で解決済みで `delivery/version-matrix.md` にある（pnpm / Turborepo / Node / Nx 等）。fresh ならそれを使い、未取得/陳腐化していれば `tech-version-check` を実行して更新する（B-13 の "version-matrix.md is fresh" skip）。バージョンは固定しない（env-setup 方針）。固定が必要なら人間判断（warn_and_document）。

## スコープと責務分担（responsibility_split・B-19 feature-spanning）

モノレポ骨格は複数層の共有設定にまたがるため **feature-spanning**。本体は横断（shared）だが、生成物は各層に共有設定を配る。

| 項目 | owner |
|---|---|
| ワークスペース定義・ルート構成 | shared |
| 共有 lint / format / CI / .gitignore / .editorconfig | shared |
| 全モジュール共通の最小核設定（型 / env スキーマ / CI ジョブの核）（DP-PINIT-10） | shared（project-init 所有） |
| 各モジュール固有設定の取り込み口（モジュールが土台にマージ）（DP-PINIT-10） | shared（境界・契約のみ提供） |

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`stack.monorepo` / `selected_modules`）
- 出力: 案件ルートのモノレポ骨格（ディレクトリ構造・設定ファイル群）＋ `implementation-plan.schema.json` 準拠の生成計画。
- スキーマは編集しない（CONV-14）。

## 言語・モノレポ方式別レシピ

| stack（方式） | references | templates | state |
|---|---|---|---|
| `turborepo-pnpm` | `references/turborepo-pnpm.md` | `templates/turborepo-pnpm/` | ⬜ 未実装（`/aid-references-new` で起こす） |
| `rails-js-hybrid` | `references/rails-js-hybrid.md` | `templates/rails-js-hybrid/` | ⬜ 未実装 |
| `nx` | `references/nx.md` | `templates/nx/` | ⬜ 未実装 |

## 実装契約（言語非依存）

モノレポ方式に依らず、以下を満たす土台を生成する（具体コマンド・ファイルは references）:

- **ワークスペース定義**: フロント / バック / 共有パッケージを配置できるワークスペースを定義する。
- **共有設定の単一所有（DP-PINIT-10）**: 全モジュール共通の最小核（lint / format / 型 / CI ジョブの核 / env スキーマ）は**ルート（project-init 所有）に置く**。モジュール固有設定はモジュール側がルート設定を継承・マージする口を用意する。
- **境界の明示（DP-PINIT-11）**: ドメイン機能のコードは生成しない。土台（器・共有設定）のみ。
- **delivery 連携（DP-PINIT-04 / 07）**: 案件ルートに `delivery/<module>/` を置ける構造とし、横断索引（JSON 正本＋Markdown 派生）を `project-scaffold` が初期化できるようにする。

> **要件で別指定があれば要件優先**（既定の最小核設定より案件要件を優先）。

## 運用契約（本番必須・言語非依存）

- 生成物は冪等に再実行できる（既存ファイルを破壊しない・差分マージ）。
- CI の核（lint / test / build）はルートで定義し、各ワークスペースから呼べる。
- バージョンはロックファイルで固定し、`version-matrix.md` と整合させる。

## 手順（言語非依存）

1. `tech-version-check` で方式のツール最新版を解決。
2. `project-scope.json.stack.monorepo.choice` のレシピ（references）を選ぶ。
3. ワークスペース＋共有設定（最小核）を生成。
4. フロント/バック/ローカル基盤 setup Skill が載るプレースを用意。
5. `delivery/skill-authoring-log.md` 相当に生成結果を記録し、`/project-status` 用の横断索引初期化を `project-scaffold` に引き渡す。

## 新しいモノレポ方式・言語への展開

`/aid-references-new project-monorepo-scaffold <stack>` で `references/<stack>.md` ＋ `templates/<stack>/` を追加する。契約（本 SKILL.md）は変更しない。

## DoD（B-15）

- 確定方式でモノレポ骨格が生成され、ルート共有設定（lint/format/CI/型/env 核）が機能する。
- フロント/バック/ローカル基盤 setup Skill が土台の上で動く（結合確認）。
- 横断索引の初期化に必要な `delivery/<module>/` 構造が用意されている。

## 既知の制約

- モノレポ方式の混在（同一案件で turborepo と nx 併用等）はサポートしない（方式は1つに確定）。
- ドメイン機能は生成しない（境界 DP-PINIT-11）。生成しようとした場合は警告。

## 判断ポイント（人間判断をスルーさせない）

- **DP-PINIT-08**（モノレポ方式）: 確定は人間（`project-stack-select`）。本 Skill は確定済み方式に従うのみ。
- **DP-PINIT-10**（境界粒度）: 最小核は project-init 所有。共有設定の所有境界で迷ったら未決として残す（warn_and_document）。
