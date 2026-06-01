---
name: project-scaffold
description: 案件ルートに (a) delivery/<module>/ 雛形＋横断索引（JSON 正本＋Markdown 派生）と (b) 土台セットアップ（モノレポ＋フロント＋バック＋ローカル基盤）を初期化・統合するオーケストレーションスキル。implementation フェーズ（/project-scaffold）で、project-scope.json の確定モジュール・確定スタックに従い、案件の土台と delivery 構造をまとめて立ち上げたいときに使う。土台生成は専用 setup 系 Skill（monorepo/frontend/backend/local-infra）に委譲し、本スキルは順序制御と横断索引初期化を担う。generate-plugin.sh のプラグイン生成とは別物。
---

# Project Scaffold Skill

> SKL-12: description は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

`/project-scaffold` の統合役。案件ルートに **(a) delivery 横断構造**（`delivery/<module>/` 雛形＋横断索引＋横断 pending-decisions）と **(b) 土台セットアップ**（モノレポ＋フロント＋バック＋ローカル基盤）を初期化する。土台の各層は専用 setup Skill に委譲し、本スキルは**順序制御・統合・横断索引初期化**を担う（DP-PINIT-04 / 11）。

## 呼び出しトリガ（B-13）

`/project-scaffold` 実行時。`project-scope.json` に確定モジュール（`selected_modules[*].status==confirmed`）と確定スタック（`stack.*.status==confirmed`）があることが前提（未確定は warn_and_document で進行）。

## スコープと責務分担（responsibility_split）

| 項目 | owner |
|---|---|
| 順序制御・統合・横断索引初期化（オーケストレーション） | shared |
| 土台各層の生成 | 委譲（monorepo=shared / frontend=client / backend=backend / local_infra=iaas） |

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`selected_modules` / `stack` / `delivery_layout`）
- 出力: 案件ルートの土台一式＋横断索引（`delivery_layout.cross_cutting_index_json` / `_md`）＋ `implementation-plan.schema.json` 準拠の計画
- スキーマは編集しない（CONV-14）。

## 委譲する setup 系 Skill（実行順）

1. `project-stack-select`（未確定なら）→ スタック＋最新版確定（tech-version-check 連携）
2. `project-monorepo-scaffold`（DP-PINIT-08 確定方式）→ 器＋共有設定（最小核は project-init 所有・DP-PINIT-10）
3. `project-frontend-init` / `project-backend-init` / `project-local-infra`（並行可。backend と local-infra は DB 疎通で前後）
4. delivery 横断索引の初期化（下記）

## 実装契約（言語非依存・横断索引）

- **横断索引（DP-PINIT-07: 両方）**: JSON を正本（`cross_cutting_index.json`）とし、Markdown を派生生成（`cross_cutting_index.md`）。各モジュールの `delivery/<module>/` パス・フェーズ・未決件数を保持し、`/project-status` が集約に使う。
- **案件ルート集約（DP-PINIT-04）**: 各モジュールの成果物は案件ルート配下の `delivery/<module>/` に集約する構造を用意。
- **横断 pending-decisions**: 案件全体の未決集約の入れ物を初期化。
- ドメイン機能は生成しない（土台のみ・DP-PINIT-11）。

> **要件で別指定があれば要件優先**。

## 手順（言語非依存）

1. `project-scope.json` の確定モジュール・確定スタックを確認（未確定は warn）。
2. setup 系 Skill を上記順で呼ぶ。
3. `delivery/<module>/` 雛形と横断索引（JSON 正本＋MD 派生）を初期化。
4. 結果を `delivery/` に記録し、次アクション（`/project-load-guide` / `/project-status`）を案内。

## DoD（B-15）

- 土台（モノレポ＋フロント＋バック＋ローカル基盤）が生成され相互疎通する。
- `delivery/<module>/` 構造と横断索引（JSON＋MD）が初期化され、`/project-status` が読める。

## 既知の制約

- 確定スタック/モジュールが無いと土台生成は限定的（warn_and_document で可視化）。
- プラグイン生成（generate-plugin.sh）とは別物。混同しない。

## 判断ポイント（人間判断をスルーさせない）

- 確定前のスタック/モジュールを勝手に確定しない（`project-stack-select` / `project-module-recommendation` に戻す）。
- **DP-PINIT-10**: 共有 base 設定の所有境界で迷ったら未決として残す。
