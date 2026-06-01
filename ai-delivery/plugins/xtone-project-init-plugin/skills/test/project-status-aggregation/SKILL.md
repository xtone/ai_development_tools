---
name: project-status-aggregation
description: 案件全体（複数モジュール横断）の進捗・未決を横断索引から集約表示するスキル。test→ops 横断フェーズ（/project-status）で、案件ルートの横断索引（JSON 正本）と各モジュールの delivery/<module>/ を読み、フェーズ進捗・未決（pending-decisions）件数を一覧したいときに使う。横断索引の JSON を正本に機械集約し、人間可読の Markdown サマリを派生生成する（DP-PINIT-04 / 07）。MVP should。
---

# Project Status Aggregation Skill

> SKL-12: description は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

案件全体の**横断ステータス**（複数モジュールの進捗・未決）を集約表示する（DP-PINIT-04）。`project-scaffold` が初期化した横断索引（JSON 正本）と各モジュールの `delivery/<module>/` を読み、フェーズ進捗・未決件数を一覧する。

## 検証対象（集約対象）

- 各モジュールの `delivery/<module>/` のフェーズ成果物（requirements / design / implementation-plan 等）の有無・状態
- 各モジュールの `docs/pending-decisions.md`（未決件数）
- 横断索引（`cross_cutting_index.json`）の整合

## ツール

- 横断索引 JSON の読み取り・集約（機械処理）
- 集約結果から人間可読 Markdown サマリを派生生成（DP-PINIT-07: JSON 正本＋MD 派生）

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`delivery_layout`）＋ 横断索引 JSON ＋ 各モジュール delivery
- 出力: 横断ステータスサマリ（JSON 集約＋Markdown 派生）
- スキーマは編集しない（CONV-14）。

## 手順（言語非依存）

1. 横断索引 JSON を読み、各モジュールの delivery_path / phase / pending_count を取得。
2. 不足・未更新があれば再走査（各モジュール delivery を直接確認）。
3. フェーズ進捗・未決件数を集約し、JSON 正本を更新 → Markdown サマリを派生生成。
4. 未決が残るモジュールを明示（warn_and_document・ブロックしない）。

## 通過証跡

- 集約結果（JSON＋MD）を案件ルートの横断索引に記録。実行日時を残す。

## DoD（B-15）

- 全 confirmed モジュールの進捗・未決が一覧でき、未決ゼロでないモジュールが明示される。
- JSON 正本と Markdown 派生が整合する。

## 判断ポイント（人間判断をスルーさせない）

- 横断索引と実 delivery の乖離を検出したら、勝手に上書きせず差分を提示し人間判断に上げる（warn_and_document）。
