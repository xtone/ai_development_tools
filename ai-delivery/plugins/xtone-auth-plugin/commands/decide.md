---
description: 判断記録。decision-recorder を起動して decision_record と ADR を生成する。
argument-hint: <DP-ID> <選択肢> <rationale>
---

decision-recorder サブエージェントを使って、判断ポイントの決定を記録してください。

引数: $ARGUMENTS （形式: `<DP-ID> <選択肢> <rationale>`）

`decided_by` / `decided_at` / `rationale` のトリオを必須とし、`docs/adr/ADR-NNN.md` を生成、対象 decision-point の `status` を `decided` に更新してください。トリオが揃わない場合は warn_and_document（警告のみ・ブロックなし）。
