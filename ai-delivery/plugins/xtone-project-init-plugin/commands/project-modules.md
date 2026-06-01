---
description: モジュール選定支援。module-advisor を起動し、必要モジュール候補を MCS／ドメインタクソノミーから提示する（確定は人間）。
---

`module-advisor` サブエージェント（`agents/module-advisor.md`）を使い、`project-module-recommendation` スキルに従って、`project-scope.json` から必要モジュール候補を推奨提示してください。

- Notion モジュールカタログDB（MCS）／ドメインタクソノミーDB を引いて、適用ドメインが一致するモジュールを複数案＋根拠で提示する。
- **AI は候補提示のみ・確定は人間**（DP-PINIT-02 warn_and_document）。`selected_modules` に `recommended` で記録し、人間確定で `confirmed`/`rejected`。
- 該当が薄い場合は無理に寄せず、新規モジュール起票の要否を人間に上げる。
- 次アクション: `/project-scaffold`（土台セットアップ＋案件雛形初期化）。

> 前提: `project-scope.json`（`/project-init` の出力）。Notion MCP 接続が必要。
