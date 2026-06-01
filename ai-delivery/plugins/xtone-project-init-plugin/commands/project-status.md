---
description: 案件横断ステータス集約。横断索引（JSON 正本）と各モジュール delivery を読み、進捗・未決を一覧表示する。
---

`project-status-aggregation` スキル（`skills/test/project-status-aggregation/SKILL.md`）に従って、案件全体（複数モジュール横断）の進捗・未決を集約表示してください。

- 横断索引（`cross_cutting_index.json` 正本）と各モジュールの `delivery/<module>/` を読み、フェーズ進捗・未決（pending-decisions）件数を集約する。
- JSON 正本を更新し、人間可読の Markdown サマリを派生生成する（DP-PINIT-07）。
- 未決が残るモジュールを明示する（warn_and_document・ブロックしない）。
- 横断索引と実 delivery に乖離があれば、勝手に上書きせず差分を提示し人間判断に上げる。

> 前提: `/project-scaffold` で横断索引が初期化済み。MVP では should。
