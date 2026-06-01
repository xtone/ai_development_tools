---
description: 案件初期化。ドメイン・規模・制約をヒアリングし project-scope.json を生成する（案件全体の横断スコープ）。
argument-hint: [案件の説明テキスト]
---

`project-scope-extraction` スキル（`skills/requirements/project-scope-extraction/SKILL.md`）に従って、案件全体の横断スコープ `project-scope.json` を生成してください。

入力: $ARGUMENTS

- ドメイン（T-008 タクソノミー）/ 規模 / 制約 / やりたいことをヒアリングする（不足は質問）。
- `project-scope.json` の `project_name` / `domain` / `scale` / `constraints` を埋める（`selected_modules` / `stack` は後続コマンドで埋める）。
- 人間判断が要る点は決めず未決として `docs/pending-decisions.md` に残す（warn_and_document）。
- 次アクション: `/project-modules`（必要モジュールの推奨）。
