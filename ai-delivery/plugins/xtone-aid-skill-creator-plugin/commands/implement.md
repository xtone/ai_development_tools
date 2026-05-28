---
description: 実装。implementer を起動して design.schema.json からコードを生成する。
---

implementer サブエージェントを使って、`schemas/v1/design.schema.json` を読み込み、実装計画（`implementation-plan.schema.json`）とコードを生成してください。

- `skills/implementation/` 配下の Skill を使う。
- 未決が残る場合は警告して進める（**ブロックしない**、warn_and_document）。
