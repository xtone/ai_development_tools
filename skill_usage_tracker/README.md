# Skill Usage Tracker

Claude Code用のスキル使用状況トラッキングプラグインです。スキルの使用を自動的に記録し、セッション終了時にサマリーを表示します。Notionデータベースへの同期機能も備えています。

## 機能

### 1. 自動スキル使用記録（PostToolUse フック）

スキル呼び出し時に以下の情報を自動記録します：

- スキル名
- タイムスタンプ
- ユーザー情報（git config の name, email）
- コンテキスト情報（プロジェクト名、ブランチ、リモートURL、ホスト名）

**保存先**: `~/.claude/hooks/logs/skill_usage.jsonl`

### 2. セッション終了時のサマリー表示（Stop フック）

セッション終了時に使用されたスキルの一覧と回数を表示します：

```
📊 Skill Usage Summary
────────────────────────────────────────
  greeting-skill:greeting: 3
  backend-development:orchestrating-api-implementation: 2
────────────────────────────────────────
  Total: 5 invocations
```

**注意**: Stop フックは `/exit` コマンドで正常終了した場合に動作します。`Ctrl+C` で強制終了した場合は動作しません。

### 3. カスタムコマンド

#### `/skill-stats` - 統計表示

任意のタイミングでスキル使用状況を確認できます。

#### `/skill-stats reset` - データリセット

ローカルに保存されたスキル使用データをクリアします。

#### `/skill-stats setup` - Notion同期設定

Notionデータベースへの同期に必要な設定ファイルを作成します。

```bash
# 使用方法
skill-stats.js setup <skill_usage_db_id> <slash_command_db_id>

# 例
skill-stats.js setup b787567d-9565-49ac-89d4-fd2569497d15 a24187ec-c81b-4853-a6ae-d8139abffc0b
```

data_source_id は Notion MCP の `mcp__notion__notion-fetch` で取得できます。

#### `/skill-stats sync` - Notionへの同期

未同期のイベントをNotionデータベースに同期します。事前に `setup` で設定ファイルを作成してください。

### 4. Notion データベース同期

チーム全体の使用状況を集計・可視化するために、Notionデータベースへの同期機能を提供します。

#### セットアップ手順

1. Notionで2つのデータベースを作成（スキーマは下記参照）
2. `/skill-stats setup` でデータベースIDを設定
3. `/skill-stats sync` で同期を実行

#### データベーススキーマ

**Skill Usage Events**:
| プロパティ名 | 型 | 説明 |
|------------|---|------|
| Skill | title | スキル名 |
| Timestamp | date | 実行日時 |
| User Name | rich_text | git config user.name |
| User Email | email | git config user.email |
| System User | rich_text | システムユーザー名 |
| Project | rich_text | プロジェクト名 |
| Branch | rich_text | ブランチ名 |
| Remote | url | リモートリポジトリURL |
| Hostname | rich_text | ホスト名 |

**Slash Command Events**:
| プロパティ名 | 型 | 説明 |
|------------|---|------|
| Command | title | コマンド名 |
| Full Command | rich_text | フルコマンド文字列 |
| Source | select | user_prompt / slash_command_tool |
| Timestamp | date | 実行日時 |
| User Name | rich_text | git config user.name |
| User Email | email | git config user.email |
| System User | rich_text | システムユーザー名 |
| Project | rich_text | プロジェクト名 |
| Branch | rich_text | ブランチ名 |
| Remote | url | リモートリポジトリURL |
| Hostname | rich_text | ホスト名 |

## インストール

### Claude Code Marketplaceから

```bash
# マーケットプレイスにリポジトリを追加
/plugin marketplace add xtone/ai_development_tools

# プラグインをインストール
/plugin install skill-usage-tracker@xtone-ai-development-tools
```

## 収集データ

### 収集される情報

| カテゴリ | 項目 | 取得元 |
|---------|------|--------|
| **スキル** | スキル名 | Skill ツールの入力 |
| | タイムスタンプ | システム時刻 |
| **ユーザー** | name | `git config user.name` |
| | email | `git config user.email` |
| | system_user | 環境変数 `USER` |
| **コンテキスト** | project | カレントディレクトリ名 |
| | branch | `git branch --show-current` |
| | remote | `git remote get-url origin` |
| | hostname | `os.hostname()` |
| | cwd | カレントディレクトリのフルパス |

### データ形式（JSONL）

データは JSONL（JSON Lines）形式で保存されます。1行1イベントで、追記操作が効率的です。

**skill_usage.jsonl**:
```json
{"skill":"greeting-skill:greeting","timestamp":"2025-12-03T02:38:45.218Z","user":{"name":"Pregum","email":"pregum.y@gmail.com","system_user":"y.hino"},"context":{"project":"ai_development_tools","branch":"feature/xxx","remote":"ssh://git@github.com/xtone/ai_development_tools.git","hostname":"XTONE-0089-YHINO.local"}}
```

## ファイル構成

| ファイル | 説明 |
|---------|------|
| `~/.claude/hooks/logs/skill_usage.jsonl` | スキル使用イベント |
| `~/.claude/hooks/logs/slash_command.jsonl` | スラッシュコマンド使用イベント |
| `~/.claude/hooks/logs/sync_state.json` | Notion同期状態 |
| `~/.claude/hooks/logs/notion_config.json` | Notion設定（DB ID） |

## プライバシーとデータの取り扱い

### データの保存場所

収集されたデータは **ローカルマシンのみ** に保存されます。外部サーバーへの自動送信は行いません。

- 保存先: `~/.claude/hooks/logs/`
- 送信: なし（ローカル保存のみ、Notion同期は手動実行）

### データの使用目的

- スキル使用状況の可視化・分析
- 開発ワークフローの改善
- チーム全体での使用傾向の把握（Notion同期時）

### データの削除

```bash
# 全データを削除
/skill-stats reset

# 手動で削除
rm ~/.claude/hooks/logs/skill_usage.jsonl
rm ~/.claude/hooks/logs/slash_command.jsonl
```

### プライバシーに関する注意

- Git設定のユーザー名・メールアドレスが記録されます
- リモートURLにはリポジトリ情報が含まれます
- 機密プロジェクトで使用する場合は、データファイルの管理に注意してください
- `notion_config.json` にはデータベースIDが含まれるため、`.gitignore` に追加することを推奨

## ディレクトリ構造

```
skill_usage_tracker/
├── .claude-plugin/
│   ├── plugin.json           # プラグイン設定
│   └── marketplace.json      # マーケットプレイス情報
├── hooks/
│   ├── hooks.json            # フック設定
│   ├── skill_usage_counter.js # PostToolUse: スキル使用記録
│   ├── slash_command_counter.js # PostToolUse: コマンド使用記録
│   ├── user_prompt_command_counter.js # UserPromptSubmit: プロンプト内コマンド検出
│   └── skill_usage_sender.js  # Stop: サマリー表示
├── commands/
│   └── skill-stats.md        # カスタムコマンド
├── bin/
│   ├── skill-stats.js        # 統計/同期スクリプト
│   └── migrate-to-jsonl.js   # JSON→JSONL移行スクリプト
├── CHANGELOG.md
└── README.md
```

## トラブルシューティング

### ローカルデータの確認

```bash
# 最新10件のスキル使用を表示
tail -10 ~/.claude/hooks/logs/skill_usage.jsonl

# 最新10件のコマンド使用を表示
tail -10 ~/.claude/hooks/logs/slash_command.jsonl
```

### データのリセット

```bash
/skill-stats reset
```

### 実行権限エラー（permission denied）

フックスクリプトに実行権限がない場合：

```bash
chmod +x ~/.claude/plugins/skill_usage_tracker/hooks/*.js
chmod +x ~/.claude/plugins/skill_usage_tracker/bin/*.js
```

### Stop フックが動作しない

- `/exit` コマンドで終了してください
- `Ctrl+C` での強制終了時は Stop フックは実行されません
- `/skill-stats` コマンドで手動確認できます

### 旧形式（JSON）からの移行

v0.2.0 より前のバージョンからアップグレードする場合：

```bash
# ドライラン（確認のみ）
node ~/.claude/plugins/skill-usage-tracker/bin/migrate-to-jsonl.js --dry-run

# 実際の移行
node ~/.claude/plugins/skill-usage-tracker/bin/migrate-to-jsonl.js
```

## 必要な環境

- Claude Code 0.1.0 以上
- Node.js 18.0.0 以上
- Git（ユーザー情報取得用）
- Notion MCP（同期機能を使用する場合）

## 作成者

**HINO, Yasushi**
- Organization: XTONE

## ライセンス

MIT License
