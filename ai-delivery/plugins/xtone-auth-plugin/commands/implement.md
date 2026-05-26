---
description: 実装。implementer を起動して design.schema.json からコードを生成する。
---

implementer サブエージェントを使って、`schemas/v1/design.schema.json` を読み込み、実装計画（`implementation-plan.schema.json`）とコードを生成してください。

## Step 0: 呼び出しスキルの計画（B-13・必須・先に実行）

`skills/implementation/implementation-skill-planner` を **必ず最初に**呼び出し、`delivery/design.yaml`（または `design.json`）の `responsibility_split` / `page_access_control` / `authentication.mfa_requirement` / `local_dev_stack` から **呼び出すべきスキル一覧**を導出して、`delivery/implementation-skill-plan.md` と `implementation-plan.json` の `skill_plan` フィールドに反映する。

- `skill_plan` に列挙されたスキル（`required=true`）は実装フェーズ中に必ず呼び出し、完了時に該当エントリの `called=true` に更新する。
- 完了時に `called=false` のまま残っている `required=true` のエントリがあれば **警告**（warn_and_document）し、`docs/pending-decisions.md` に「未呼び出しスキル: <skill-id> / 理由: <自動 vs 判断>」を起票する。**ブロックはしない**（T-002）。
- `skill_plan` は `implementation-plan.schema.json` 上 **required かつ minItems=1**。schema validation 段階で欠落・空配列は検出されるが、運用上も Step 0 で planner が必ず埋める。仮にすり抜けて完了に到達したら警告対象（warn_and_document）。
- 計画外のスキルを呼び出したい場合は、その場で `skill_plan` に追記してから実行する。

## Step 1 以降

- Step 0 の `skill_plan` に沿って `skills/implementation/` 配下の Skill を順次使う。
- 未決が残る場合は警告して進める（**ブロックしない**、warn_and_document）。
