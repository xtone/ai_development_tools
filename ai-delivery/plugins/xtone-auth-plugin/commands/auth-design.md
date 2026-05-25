---
description: 認証設計。authentication-architect を起動し、firebase-auth-design スキルで requirements の認証要件から design.schema.json を生成する（認証スタックを複数比較）。
---

authentication-architect サブエージェントを使い、`skills/design/firebase-auth-design` スキルに沿って認証設計を進めてください。

1. `schemas/requirements.schema.json` 準拠の要件から、認証関連（ログイン方式・ソーシャル連携・MFA・規制・ユーザ規模）を読み取る。
2. **DP-007**（認証スタック）は Firebase Auth を含め **2 つ以上を比較**し、MVP 推奨と根拠、IaaS 差し替え可能設計の担保を示す（最終決定は人間）。
3. **DP-008**（MFA）/ **DP-015**（dAccount・docomo 規約）を案件条件に当てはめ、決められないものは推奨だけ提示。
4. `schemas/design.schema.json` を生成し、決定済みは `decision_record`、未決は `undecided` に `DP-XXX` を残す（warn_and_document）。
5. 重要な決定は `docs/adr/ADR-NNN.md` に記録する。

> 基盤の汎用設計でよい場合は `/design`（designer）を使う。`/auth-design` は認証ドメイン特化版。
