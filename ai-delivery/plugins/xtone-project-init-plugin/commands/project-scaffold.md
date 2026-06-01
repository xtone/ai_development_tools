---
description: 案件土台セットアップ＋雛形初期化。スタック選択（最新版併記）→モノレポ/フロント/バック/ローカル基盤生成→delivery 横断索引初期化を統合実行する。
argument-hint: [target_root]
---

`project-scaffold` スキル（`skills/implementation/project-scaffold/SKILL.md`）に従って、案件ルートの土台と delivery 横断構造を初期化してください。

統合フロー:

1. **スタック選択**: `project-stack-select` スキルで、サポート済みスタックを候補提示する。**`tech-version-check`（B-17）で各 FW/言語の最新安定版を取得して併記**し、人間が確定する（DP-PINIT-09・バージョン固定は人間判断）。確定を `project-scope.json.stack`（version 含む）に保持。
2. **土台セットアップ**（土台のみ・ドメイン機能は各モジュール・DP-PINIT-11）:
   - `project-monorepo-scaffold`（確定方式・DP-PINIT-08。最小核設定は project-init 所有・DP-PINIT-10）
   - `project-frontend-init` / `project-backend-init` / `project-local-infra`（version-matrix.md を再利用）
3. **delivery 横断構造**: `delivery/<module>/` 雛形＋横断索引（JSON 正本＋Markdown 派生・DP-PINIT-04/07）＋横断 pending-decisions を初期化。

- 確定スタック/モジュールが無い項目は warn_and_document で残す（勝手に確定しない）。
- 次アクション: `/project-load-guide`（ロード手順）→ `/project-status`（横断集約）。

> 注意: これは案件土台の初期化であり、`generate-plugin.sh` のプラグイン生成とは別物。
