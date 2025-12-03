# Skill Usage Tracker

Claude Code用のスキル使用状況トラッキングプラグインです。スキルの使用を自動的に記録し、セッション終了時にサマリーを表示します。

## 機能

### 1. 自動スキル使用記録（PostToolUse フック）

スキル呼び出し時に以下の情報を自動記録します：

- スキル名
- タイムスタンプ
- ユーザー情報（git config の name, email）
- コンテキスト情報（プロジェクト名、ブランチ、リモートURL、ホスト名）

**保存先**: `~/.claude/hooks/state/skill_usage_events.json`

### 2. セッション終了時のサマリー表示（Stop フック）

セッション終了時に使用されたスキルの一覧と回数を表示します：

```
📊 Skill Usage Summary
────────────────────────────────────────
  greeting-skill:greeting: 3
  backend-development:orchestrating-api-implementation: 2
────────────────────────────────────────
  Total: 5 invocations
  Data: /Users/xxx/.claude/hooks/state/skill_usage_events.json
```

**注意**: Stop フックは `/exit` コマンドで正常終了した場合に動作します。`Ctrl+C` で強制終了した場合は動作しません。

### 3. カスタムコマンド `/skill-stats`

任意のタイミングでスキル使用状況を確認できます：

```
/skill-stats
```

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

### データ形式（skill_usage_events.json）

```json
{
  "events": [
    {
      "skill": "greeting-skill:greeting",
      "timestamp": "2025-12-03T02:38:45.218Z",
      "user": {
        "name": "Pregum",
        "email": "pregum.y@gmail.com",
        "system_user": "y.hino"
      },
      "context": {
        "project": "ai_development_tools",
        "branch": "feature/xxx",
        "remote": "ssh://git@github.com/xtone/ai_development_tools.git",
        "hostname": "XTONE-0089-YHINO.local",
        "cwd": "/Users/y.hino/..."
      }
    }
  ],
  "summary": {
    "greeting-skill:greeting": 2
  },
  "pending_sync": true
}
```

## プライバシーとデータの取り扱い

### データの保存場所

収集されたデータは **ローカルマシンのみ** に保存されます。外部サーバーへの自動送信は行いません。

- 保存先: `~/.claude/hooks/state/skill_usage_events.json`
- 送信: なし（ローカル保存のみ）

### データの使用目的

- スキル使用状況の可視化・分析
- 開発ワークフローの改善

### データの削除

収集されたデータを削除するには、以下のコマンドを実行してください：

```bash
rm ~/.claude/hooks/state/skill_usage_events.json
```

### プライバシーに関する注意

- Git設定のユーザー名・メールアドレスが記録されます
- リモートURLにはリポジトリ情報が含まれます
- 機密プロジェクトで使用する場合は、データファイルの管理に注意してください

## ディレクトリ構造

```
skill_usage_tracker/
├── .claude-plugin/
│   ├── plugin.json           # プラグイン設定
│   └── marketplace.json      # マーケットプレイス情報
├── hooks/
│   ├── hooks.json            # フック設定
│   ├── skill_usage_counter.js # PostToolUse: イベント記録
│   └── skill_usage_sender.js  # Stop: サマリー表示
├── commands/
│   └── skill-stats.md        # カスタムコマンド
├── bin/
│   └── skill-stats.js        # サマリー表示スクリプト
└── README.md
```

## トラブルシューティング

### ローカルデータの確認

```bash
cat ~/.claude/hooks/state/skill_usage_events.json
```

### データのリセット

```bash
rm ~/.claude/hooks/state/skill_usage_events.json
```

### 実行権限エラー（permission denied）

フックスクリプトに実行権限がない場合、以下のエラーが発生します：

```
permission denied: /path/to/skill_usage_counter.js
```

**解決方法:**

```bash
chmod +x ~/.claude/plugins/skill_usage_tracker/hooks/*.js
chmod +x ~/.claude/plugins/skill_usage_tracker/bin/*.js
```

### Stop フックが動作しない

- `/exit` コマンドで終了してください
- `Ctrl+C` での強制終了時は Stop フックは実行されません
- `/skill-stats` コマンドで手動確認できます

## 今後の拡張予定

- 外部サービス（Google Spreadsheet等）への送信機能
- MCP サーバー経由での集約

## 必要な環境

- Claude Code 0.1.0 以上
- Node.js 18.0.0 以上
- Git（ユーザー情報取得用）

## 作成者

**HINO, Yasushi**
- Organization: XTONE

## ライセンス

MIT License
