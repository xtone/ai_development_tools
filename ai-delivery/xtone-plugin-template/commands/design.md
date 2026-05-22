---
description: 設計。designer を起動して design.schema.json を生成し技術スタックを推奨する。
---

designer サブエージェントを使って、`schemas/v1/requirements.schema.json` を読み込み、`schemas/v1/design.schema.json` を作成してください。

- モジュールカタログの `tech_options` を参照し、技術スタックの推奨と根拠を提示する（**最終決定は人間**）。
- 決定済みは `decision_record` に、未決は `undecided` に `DP-XXX` を残す（warn_and_document）。
