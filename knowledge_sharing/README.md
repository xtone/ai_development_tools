# Knowledge Sharing

Claude Code の利用記録から、チームで共有できる知見を抽出・検証・公開するスキル群です。

## インストール

```bash
/plugin marketplace add xtone/ai_development_tools
/plugin install knowledge-sharing@xtone-ai-development-tools
```

## スキル一覧

| スキル | 説明 |
|--------|------|
| **session-tips-digest** | 過去のセッション記録から共有できる運用 Tips を抽出し、一次情報で裏付けを取って Markdown・Artifact・Notion に公開する |

## session-tips-digest

### 使い方

```
/knowledge-sharing:session-tips-digest
/knowledge-sharing:session-tips-digest --since 7d --projects my-app
/knowledge-sharing:session-tips-digest --artifact-url https://claude.ai/artifact/<id>
/knowledge-sharing:session-tips-digest --notion <Notion ページの URL> --no-research
```

| 引数 | 既定 | 意味 |
|---|---|---|
| `--since` | `30d` | 抽出期間。`7d` や `2026-09-01` も受ける |
| `--projects` | 全部 | 対象プロジェクト名の部分一致（カンマ区切り） |
| `--out` | `tips/` | 成果物ディレクトリ |
| `--artifact-url` | なし | 既存 Artifact を更新する |
| `--notion` | なし | 指定した Notion ページの配下に書き出す |
| `--no-research` | なし | 一次情報の調査を省略する |

### 流れ

1. `~/.claude/` の履歴・セッションログ・memory を集計する（設定値やトークンは出力しない）
2. 共有できる Tips を選び、案件名や固有値を伏せて書く
3. 機密スキャンで 0 件になるまで直す
4. 公式ドキュメントや論文で各 Tips を裏付ける、修正する、範囲を狭める
5. HTML に変換して Artifact として公開する（指定があれば Notion にも書き出す）

### 成果物

| パス | 内容 |
|---|---|
| `tips/claude-code-tips.md` | Tips 本体 |
| `tips/claude-code-tips-references.md` | 一次情報との対応表 |
| `tips/dist/index.html` | Artifact の元ファイル |
| `tips/.work/` | 作業ファイル。個人の記録を含むのでコミットしない |

### 必要環境

- Python 3.10 以上（標準ライブラリのみ）
- 任意: natural-japanese プラグイン（文章の lint）、Notion MCP（Notion への書き出し）

### evaluate-session との違い

| スキル | 対象 | 目的 |
|---|---|---|
| common-development の evaluate-session | セッション 1 本 | 無駄の有無を採点する |
| session-tips-digest | 期間内の全セッション | 共有できる知見を抜き出す |

### 開発

```bash
cd knowledge_sharing/skills/session-tips-digest/scripts
uv run --no-project --with pytest python -m pytest -q -p no:cacheprovider
```
