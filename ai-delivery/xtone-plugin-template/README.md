# xtone-plugin-template

Xtone **AIデリバリシステム**の Claude Code プラグイン用マスターテンプレート（T-019 / TPL-01〜30）。このディレクトリを複製して個別プラグイン（`xtone-auth-plugin` など）を作成する。

> 完全な利用ガイドは Notion [共通テンプレ実装DB（正）](https://www.notion.so/67d335eab7004f828e7cc3313e266c2a) と `docs/template-usage-guide.md`（TPL-28）を参照。

> **実行環境**: 言語・FW のバージョンは固定せず**公式の最新安定版**を使う。セットアップ手順とバージョン方針は [`../docs/environment-setup.md`](../docs/environment-setup.md)。`.ruby-version` 等には固定値を置かず、生成・着手時に最新を解決する。

## 提供物

| カテゴリ | 件数 | 内容 |
|---|---|---|
| テンプレートファイル | 4 | plugin.json / README / .mcp.json.sample / .env.example（ルート CLAUDE.md は置かない＝DP-27） |
| スキーマリンク | 1 | xtone-shared-plugin への symlink |
| 横断スキルリンク | 2 | `skills/implementation/tech-version-check`（B-17）／ `skills/implementation/implementation-skill-planner`（B-18） → xtone-shared-plugin への symlink |
| Subagent | 6 | requirements-analyst / designer / implementer / decision-recorder / pending-watcher / reviewer |
| Slash Command | 8 | /req-collect /design /implement /decide /status /next /pending-list /skip-review |
| Hook | 4 | pre-phase-transition / post-decision-record / pre-pr-merge / post-pr-merge |
| Skill | 2 | plugin-guide/SKILL.md.template（運用ガイド＝旧 CLAUDE.md, CONV-06）/ SKILL.md.template（フェーズ別雛形） |
| スクリプト | 2 | generate-plugin.sh / validate-plugin.sh |

## 新規プラグインの作成（generate-plugin.sh）

`scripts/generate-plugin.sh`（TPL-26）でテンプレからプラグインスケルトンを生成する。手動コピーは原則不要。

```bash
ai-delivery/scripts/generate-plugin.sh <usecase> \
  --description "<プラグイン説明>" \
  --author      "<著者>" \
  --domains     "<適用ドメイン>" \
  --modules     "<MOD-XXX>"

# 例
ai-delivery/scripts/generate-plugin.sh auth \
  --description "ユーザー認証とセッション管理を型化する Xtone AIデリバリプラグイン" \
  --author "Xtone" \
  --domains "BtoCアプリ,MaaS・モビリティ" \
  --modules "MOD-001"
```

スクリプトは次を自動で行う:

- `plugins/xtone-<usecase>-plugin/` を作成（既存時は `--force` で上書き）
- `schemas/` を `xtone-shared-plugin/schemas/v1` への symlink で作成
- `skills/implementation/tech-version-check/` を `xtone-shared-plugin/skills/implementation/tech-version-check` への symlink で作成（B-17）
- `skills/implementation/implementation-skill-planner/` を `xtone-shared-plugin/skills/implementation/implementation-skill-planner` への symlink で作成（B-18）
- `.claude-plugin/plugin.json.template` → `plugin.json` に実体化
- `skills/plugin-guide/` → `skills/<usecase>-plugin-guide/` にディレクトリ改名、`SKILL.md.template` → `SKILL.md` に実体化
- 各種ファイル中の `{{usecase}}` / `{{description}}` / `{{author_name}}` / `{{applicable_domains}}` / `{{dependent_modules}}` を置換
- `hooks/*.sh` に実行権限を付与
- 未置換 `{{...}}` を検出して警告（warn_and_document）
- プラグイン用の最小 `README.md` 雛形を生成

> ルート `CLAUDE.md` は作らない（DP-27 本決定: Claude Code が context として読まないため）。運用ガイドは `skills/<usecase>-plugin-guide/SKILL.md` に集約する（CONV-06）。

### 生成後の検証

```bash
ai-delivery/scripts/validate-plugin.sh ai-delivery/plugins/xtone-<usecase>-plugin
```

`validate-plugin.sh`（TPL-27）が `plugin.json` 必須フィールド・`schemas/` symlink・`skills/implementation/tech-version-check/` symlink（B-17）・`skills/implementation/implementation-skill-planner/` symlink（B-18）・各 `SKILL.md` frontmatter・hook 実行権限・トークン参照・未置換プレースホルダ・**デリバリ成果物のスキーマ検証**（`sample-outputs/` / `delivery/` 配下の requirements/design/implementation-plan ほか）を一括チェックする。

### プレースホルダ一覧

`skills/SKILL.md.template`（フェーズ別 Skill の骨格）は実体化されず残るので、各 Skill を増やすときに手動でコピーして使う。

| プレースホルダ | 置換内容 | 出現ファイル |
|---|---|---|
| `{{usecase}}` | ユースケース名（例: `auth`） | plugin.json / plugin-guide / SKILL ほか共通 |
| `{{description}}` / `{{author_name}}` | プラグイン説明・作者 | `.claude-plugin/plugin.json` |
| `{{applicable_domains}}` | 適用ドメイン（T-008 ドメインタクソノミーから選択） | `skills/<usecase>-plugin-guide/SKILL.md` |
| `{{dependent_modules}}` | 依存モジュール（MOD-XXX） | `skills/<usecase>-plugin-guide/SKILL.md` |
| `{{phase}}` / `{{skill_name}}` / `{{Skill Title}}` | フェーズ別 Skill 用（手動置換） | `skills/SKILL.md.template` |

## 中核設計原則

- **人間判断をスルーさせない**: 未決は `docs/pending-decisions.md` に記録し pending-watcher が可視化（4チャネル）。
- **warn_and_document（T-002）**: すべて警告のみ・ブロックなし。
- **Single Source of Truth（CONV-14）**: `schemas/` ／ `skills/implementation/tech-version-check/`（B-17） ／ `skills/implementation/implementation-skill-planner/`（B-18）は symlink。コピーしない。

## 関連

- `../CLAUDE.md` — ai-delivery 全体の作業ガイド
- `../docs/notion-db-catalog.md` — Notion DB 一覧
- `../docs/mcp-setup-guide.md` — MCP 接続手順
