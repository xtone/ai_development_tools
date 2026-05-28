---
description: AIデリバリ用プラグインの骨格生成。aid-plugin-scaffold スキルを起動し、ai-delivery/scripts/generate-plugin.sh を delivery/plugin-architecture.json から引数組立・対話確認・実行・post-checks まで一気通貫で行う。
argument-hint: <usecase> [--force] [--no-domain-architect]
---

`aid-plugin-scaffold` スキル（`skills/implementation/aid-plugin-scaffold/SKILL.md`）に従って、新規 AIデリバリプラグインの骨格を生成してください。

引数: $ARGUMENTS （形式: `<usecase> [--force] [--no-domain-architect]`）

1. **前提**: `delivery/plugin-architecture.json` が存在すること（無ければ `/aid-skill-creator-design` を先に実行するよう促す・warn_and_document）。
2. **CLI 引数組立**: `plugin-architecture.json` の `applicable_domains` / `module_candidates` / `domain_label` から `--description` / `--author` / `--domains` / `--modules` / `--domain` を組み立てる。不足項目はユーザに質問（AI が勝手に埋めない）。
3. **プレビュー**: 組み立てた `bash ai-delivery/scripts/generate-plugin.sh <args>` を**実行前に表示**して確認を取る。
4. **`--force` 取扱**: 既存プラグインがある場合、`--force` は**ユーザが明示的に文字列で許可した場合のみ**付与（事故防止）。
5. **実行 + post-checks**: スクリプト実行 → symlink 整合（schemas / tech-version-check / implementation-skill-planner）/ 未置換二重波括弧プレースホルダ / `<usecase>-architect.md` の実体化確認 / `validate-plugin.sh` 起動。
6. **記録**: 実行コマンド・出力・post-checks を `delivery/scaffold-log.md` に記録。
7. **次アクション提示**: `/aid-architect-author <usecase>` → `/aid-skill-new <phase> <skill>` → `/aid-references-new` → `/aid-dp-register` → `/aid-sample-case-binding` → `/aid-validation-runner` の順を log 末尾に書く。

> ブロックしない（warn_and_document, T-002）。未決は `docs/pending-decisions.md` に追記。
