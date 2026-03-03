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

### Notion同期の初期設定
`setup` 引数で Notion 設定ファイルを作成します。

```bash
${CLAUDE_PLUGIN_ROOT}/bin/skill-stats.js setup <skill_usage_db_id> <slash_command_db_id>
```

data_source_id は Notion MCP の `mcp__notion__notion-fetch` で取得できます。

### Notionへの同期
`sync` 引数で未同期のイベントを Notion データベースに同期します。

以下の手順で同期を実行してください：

1. Bash で `${CLAUDE_PLUGIN_ROOT}/bin/skill-stats.js sync` を実行して未同期データを取得

2. 出力されたJSONの `skill_usage_events` を `mcp__notion__notion-create-pages` で
   `config.skill_usage_db_id` に書き込み

3. 出力されたJSONの `slash_command_events` を `mcp__notion__notion-create-pages` で
   `config.slash_command_db_id` に書き込み

4. 書き込み完了後、sync_state.json を new_sync_state の内容で更新

#### Notion データベースのスキーマ

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
