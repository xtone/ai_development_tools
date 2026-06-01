---
name: project-load-guide
description: 確定した選定モジュールプラグイン群のロード手順・共存設定（名前空間前提）を出力するスキル。implementation フェーズ（/project-load-guide）で、project-scope.json の confirmed モジュールに対応するプラグインをどの順でロードし、/<plugin>:<command> 名前空間でどう併用するかの開発指針を案件チームに提示したいときに使う。Claude Code 標準名前空間で衝突回避済みを前提とした薄い案内（DP-PINIT-03）。MVP should。
---

# Project Load Guide Skill

> SKL-12: description は 3要素（何を / いつ / どんな条件で）を含む。

## 概要

確定した選定モジュールに対応するプラグイン群の**ロード手順と共存設定**を出力する（DP-PINIT-03 accepted: 名前空間前提の薄い層）。各モジュールは `/<plugin>:<command>` で進められるため、本スキルは衝突回避機構ではなく**「どの順で何をロードし、どう併用するか」の開発指針**を案件チームに渡す。

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`selected_modules[*].status==confirmed`）
- 出力: ロードガイド（`load-guide`: 各 `{plugin, load_order, coexistence_notes}`。Markdown 指針＋必要なら設定スニペット）
- スキーマは編集しない（CONV-14）。

## 手順（言語非依存）

1. confirmed モジュール → 対応プラグイン（例: 認証 MOD-001 → xtone-auth-plugin）を対応付ける。
2. ロード順（依存のあるものを先に）と、`/<plugin>:<command>` 名前空間での併用方法を整理。
3. 共存上の注意（同名コマンドは名前空間で区別される旨・各プラグインの plugin-guide 参照先）を記述。
4. 案件チーム向けに「この案件はこの型で進める」開発指針として出力。

## 実装契約（言語非依存）

- ハード衝突は Claude Code 標準名前空間で回避済み前提。**独自の衝突回避機構は持たない**（DP-PINIT-03）。
- 各モジュールプラグインの運用 context は各プラグインの `<usecase>-plugin-guide` を指す（重複させない）。

## DoD（B-15）

- confirmed 全モジュールのロード順・共存設定が出力され、案件チームが `/<plugin>:<command>` で各モジュールを開始できる。

## 既知の制約

- 各モジュール固有の要件定義〜実装は各プラグインの責務（本スキルは案内のみ）。

## 判断ポイント（人間判断をスルーさせない）

- ロード順に依存解釈の曖昧さがあれば未決として残す（warn_and_document）。
