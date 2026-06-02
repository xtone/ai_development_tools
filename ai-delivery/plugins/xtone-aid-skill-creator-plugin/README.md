# xtone-aid-skill-creator-plugin

Xtone AIデリバリシステムの **aid-skill-creator** プラグイン。マスターテンプレ `xtone-plugin-template`（T-019）から生成。

> 運用 context は `skills/aid-skill-creator-plugin-guide/SKILL.md` を参照（DP-27 / CONV-06: ルート CLAUDE.md は置かない）。
> プロジェクト全体のルールは `ai-delivery/CLAUDE.md` を参照。

## 構成

- `agents/` — Subagent（基盤6 ＋ ユースケース特化を追加可能）
- `commands/` — Slash Command（基盤8 ＋ 必要に応じて拡張）
- `hooks/` — hooks.json + 4 Hook（warn_and_document）
- `skills/aid-skill-creator-plugin-guide/` — 本プラグインの作業ガイド
- `skills/<phase>/<skill>/` — フェーズ別 Skill（テンプレは `skills/SKILL.md.template`）
- `schemas/` — `xtone-shared-plugin/schemas/v1` への symlink（編集不可・CONV-14）
- `docs/` — pending-decisions / adr 等

## はじめかた

Claude Code の **Marketplace 経由でインストール**する（推奨）:

```
/plugin marketplace add xtone/ai_development_tools
/plugin install xtone-aid-skill-creator-plugin
```

インストール後、Claude Code を再起動するとコマンド・スキルが有効になる。本プラグインは **Notion MCP 必須**（16 DB から引いて中身を生成する設計）— `.env` の `NOTION_TOKEN` を設定する（[`docs/usage-guide.md`](./docs/usage-guide.md) §1）。

開発時（本リポジトリで直接編集する場合）は品質ゲートで検証:

```bash
ai-delivery/scripts/validate-plugin.sh ai-delivery/plugins/xtone-aid-skill-creator-plugin
```
