# Skill Usage Statistics

スキル使用状況のサマリーとNotionデータベースへの同期機能を提供します。

## 使用方法

### 統計表示
引数なしで実行すると、ローカルに保存されたスキル・コマンド使用状況のサマリーを表示します。

```bash
${CLAUDE_PLUGIN_ROOT}/bin/skill-stats.js
```

### ローカルデータのリセット
`reset` 引数でローカルデータをクリアします。

```bash
${CLAUDE_PLUGIN_ROOT}/bin/skill-stats.js reset
```

### Notion同期の初期セットアップ
`setup` 引数で Notion データベースの作成と設定を行います。初回のみ実行が必要です。

```bash
${CLAUDE_PLUGIN_ROOT}/bin/skill-stats.js setup
```

上記コマンドの出力（設定情報）を確認した後、Notion MCP を使用して以下の手順を実行してください：

1. `mcp__notion__notion-create-database` で親ページ配下に2つのデータベースを作成:
   - **Skill Usage Events**: スキル使用イベント用
   - **Slash Command Events**: スラッシュコマンドイベント用

2. 作成したデータベースIDを `~/.claude/hooks/logs/notion_config.json` に保存

#### Notion データベースのスキーマ

**Skill Usage Events:**
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

**Slash Command Events:**
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

### Notionへの同期
`sync` 引数で未同期のイベントを Notion データベースに同期します。

```bash
${CLAUDE_PLUGIN_ROOT}/bin/skill-stats.js sync
```

上記コマンドの出力を確認した後、以下の手順を実行してください：

1. 出力された未同期イベントを確認
2. `mcp__notion__notion-create-pages` で各イベントを Notion に書き込み
3. 書き込み完了後、同期状態ファイルを更新
