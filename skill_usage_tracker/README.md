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

## インストール

### Claude Code Marketplaceから

```bash
# マーケットプレイスにリポジトリを追加
/plugin marketplace add xtone/ai_development_tools

# プラグインをインストール
/plugin install skill-usage-tracker@xtone-ai-development-tools
```

## データ形式

### skill_usage_events.json

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

## 今後の拡張予定

- 外部サービス（Google Spreadsheet等）への送信機能
- MCP サーバー経由での集約

## 必要な環境

- Claude Code 0.1.0 以上
- Node.js 18.0.0 以上

## 作成者

**HINO, Yasushi**
- Organization: XTONE

## ライセンス

MIT License
