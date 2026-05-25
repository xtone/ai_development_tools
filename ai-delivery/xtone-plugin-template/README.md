# xtone-plugin-template

Xtone **AIデリバリシステム**の Claude Code プラグイン用マスターテンプレート（T-019 / TPL-01〜30）。このディレクトリを複製して個別プラグイン（`xtone-auth-plugin` など）を作成する。

> 完全な利用ガイドは Notion [共通テンプレ実装DB（正）](https://www.notion.so/67d335eab7004f828e7cc3313e266c2a) と `docs/template-usage-guide.md`（TPL-28）を参照。

## 提供物

| カテゴリ | 件数 | 内容 |
|---|---|---|
| テンプレートファイル | 4 | plugin.json / README / .mcp.json.sample / .env.example（ルート CLAUDE.md は置かない＝DP-27） |
| スキーマリンク | 1 | xtone-shared-plugin への symlink |
| Subagent | 6 | requirements-analyst / designer / implementer / decision-recorder / pending-watcher / reviewer |
| Slash Command | 8 | /req-collect /design /implement /decide /status /next /pending-list /skip-review |
| Hook | 4 | pre-phase-transition / post-decision-record / pre-pr-merge / post-pr-merge |
| Skill | 2 | plugin-guide/SKILL.md.template（運用ガイド＝旧 CLAUDE.md, CONV-06）/ SKILL.md.template（フェーズ別雛形） |
| スクリプト | 2 | generate-plugin.sh / validate-plugin.sh |

## 新規プラグインの作成（手動コピー）

```bash
cd ai-delivery
cp -r xtone-plugin-template plugins/xtone-<usecase>-plugin
cd plugins/xtone-<usecase>-plugin

# symlink を再作成（コピーで実体化された場合）
rm -rf schemas
ln -s ../../xtone-shared-plugin/schemas/v1 schemas

# テンプレファイルを実体化（{{usecase}} を置換）
mv .claude-plugin/plugin.json.template .claude-plugin/plugin.json
mv skills/plugin-guide/SKILL.md.template skills/plugin-guide/SKILL.md   # 運用ガイド（旧 CLAUDE.md, DP-27）
mv skills/SKILL.md.template skills/<phase>/<skill>/SKILL.md             # フェーズ別 Skill
cp .env.example .env                  # トークンを設定
# ルート CLAUDE.md は作らない（--strict 非対応 / DP-27）。人間向け概要は README.md に置く（任意）。
```

`scripts/generate-plugin.sh`（TPL-26）で上記を自動化予定。

## 中核設計原則

- **人間判断をスルーさせない**: 未決は `docs/pending-decisions.md` に記録し pending-watcher が可視化（4チャネル）。
- **warn_and_document（T-002）**: すべて警告のみ・ブロックなし。
- **Single Source of Truth（CONV-14）**: `schemas/` は symlink。コピーしない。

## 関連

- `../CLAUDE.md` — ai-delivery 全体の作業ガイド
- `../docs/notion-db-catalog.md` — Notion DB 一覧
- `../docs/mcp-setup-guide.md` — MCP 接続手順
