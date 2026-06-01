---
description: ロード手順生成。確定モジュールに対応するプラグイン群のロード順・共存設定（名前空間前提）を出力する。
---

`project-load-guide` スキル（`skills/implementation/project-load-guide/SKILL.md`）に従って、選定モジュールプラグイン群のロード手順・共存設定を出力してください。

- `project-scope.json` の `confirmed` モジュール → 対応プラグインを対応付け、ロード順（依存順）と `/<plugin>:<command>` 名前空間での併用方法を整理する。
- ハード衝突は Claude Code 標準名前空間で回避済み前提（独自の衝突回避機構は持たない・DP-PINIT-03）。
- 各モジュールの運用 context は各プラグインの `<usecase>-plugin-guide` を参照（重複させない）。
- 案件チーム向けに「この案件はこの型で進める」開発指針として出力。

> 前提: `/project-scaffold` 完了（確定モジュールあり）。MVP では should。
