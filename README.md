# AI Development Tools

Claude Code用の開発支援ツールとプラグインのコレクションです。

## Claude Code Plugin Marketplace対応

このリポジトリはClaude Code Plugin Marketplaceに対応しており、公開しているプラグインを簡単にインストールして利用できます。

## 公開中のプラグイン

- **[biome-format](./claude_code_hooks/biome_format/README.md)** - JavaScript/TypeScriptファイルの編集時に自動的にBiomeフォーマッターを実行
- **[frontend-nextjs-development](./frontend_nextjs_development/README.md)** - Next.js開発向けのツール群（Figmaデザイン抽出、コンポーネント生成など）

## プラグインのインストール方法

### Method 1: Claude Code Marketplaceから直接インストール（推奨）

Claude Codeのマーケットプレイス機能を使用して、プラグインを簡単にインストールできます。

1. Claude Code上でマーケットプレイスにこのリポジトリを追加:

```
/plugin marketplace add git@github.com:xtone/ai_development_tools.git
```

または、HTTPSを使用する場合:

```
/plugin marketplace add xtone/ai_development_tools
```

2. プラグインをインストール:

インタラクティブにプラグインを選択してインストール:

```
/plugin
```

または、直接プラグイン名を指定してインストール:

```
/plugin install biome-format@xtone-ai-development-tools
/plugin install frontend-nextjs-development@xtone-ai-development-tools
```

プラグインをインストールすると、以下が自動的に行われます:
- 必要なスクリプトがインストールディレクトリにコピーされる
- Hooksの設定が自動的に読み込まれる
- 手動でのhooks設定が不要になる

### Method 2: 手動インストール

個別のプラグインを手動でセットアップする場合は、各プラグインのREADMEを参照してください。

**参考文献:**
- [Claude Code Plugins - 公式ドキュメント](https://docs.claude.com/en/docs/claude-code/plugins)

## このリポジトリをマーケットプレイスに追加する方法

自分のプラグインをClaude Code Marketplaceで公開したい場合は、以下の手順に従ってください。

### 1. リポジトリ構造の準備

```
your-repo/
├── .claude-plugin/
│   └── marketplace.json          # マーケットプレイスのメタデータ
└── your_plugin/
    ├── .claude-plugin/
    │   └── plugin.json            # プラグインの基本情報
    ├── hooks/
    │   ├── hooks.json             # Hooksの設定
    │   └── your_script.sh         # 実行スクリプト
    └── README.md                  # プラグインのドキュメント
```

### 2. marketplace.jsonの作成

リポジトリのルートに `.claude-plugin/marketplace.json` を作成します:

```json
{
  "name": "your-marketplace-name",
  "owner": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./path/to/plugin",
      "description": "プラグインの説明",
      "version": "0.1.0",
      "author": {
        "name": "Plugin Author"
      }
    }
  ]
}
```

### 3. plugin.jsonの作成

各プラグインのディレクトリ内に `.claude-plugin/plugin.json` を作成します:

```json
{
  "name": "plugin-name"
}
```

### 4. hooks.jsonの作成

プラグインのhooksディレクトリ内に `hooks/hooks.json` を作成します:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/your_script.sh"
          }
        ]
      }
    ]
  }
}
```

**重要:** スクリプトパスには `${CLAUDE_PLUGIN_ROOT}` 変数を使用してください。この変数はプラグインのインストール時に自動的にインストールディレクトリのパスに展開されます。

### 5. スクリプトファイルの準備

実行スクリプトには実行権限を付与し、gitリポジトリにその権限を記録します:

```bash
chmod +x your_plugin/hooks/your_script.sh
git add your_plugin/hooks/your_script.sh
git update-index --chmod=+x your_plugin/hooks/your_script.sh
```

### 6. リポジトリの公開

リポジトリをGitHubにプッシュすることで、他のユーザーがマーケットプレイスを追加できるようになります。

**参考文献:**
- [Claude Code Plugins - Develop More Complex Plugins](https://docs.claude.com/en/docs/claude-code/plugins#develop-more-complex-plugins)

## ライセンス

Released under the MIT license
https://opensource.org/licenses/mit-license.php