# Skill Usage Tracker

Claude Code用のスキル使用状況トラッキングプラグインです。スキルの使用回数を自動的にカウントし、外部サービスへ分析データを送信する機能を提供します。

## 機能

### 1. 自動スキル使用カウント

PostToolUseフックを使用して、Skillツールの呼び出しを自動的に検知し、使用回数をカウントします。

- **フック**: `PostToolUse` イベント
- **対象ツール**: `Skill`
- **保存先**: `~/.claude/hooks/state/skill_usage_counts.json`

### 2. 登録リクエスト送信コマンド

カスタムコマンド `sendRegistration` を使用して、スキル使用統計と任意のペイロードを外部サービスに送信できます。

- **コマンド名**: `sendRegistration`
- **引数**:
  - `--url`: 送信先のエンドポイントURL（オプション）
  - `--payload`: 送信するJSONペイロード（オプション）

## 前提条件

このプラグインを使用する前に、Node.jsのバージョンを確認してください：

```bash
node --version
# v18.0.0 以上が必要
```

Node.js 18未満の場合は、[Node.js公式サイト](https://nodejs.org/)から最新版をインストールしてください。

## インストール

### Claude Code Marketplaceから（推奨）

```bash
# マーケットプレイスにリポジトリを追加
/plugin marketplace add xtone/ai_development_tools

# プラグインをインストール
/plugin install skill-usage-tracker@xtone-ai-development-tools
```

### 手動インストール

```bash
# リポジトリをクローン
git clone https://github.com/xtone/ai_development_tools.git

# プラグインディレクトリをClaude Codeの設定ディレクトリにコピー
cp -r ai_development_tools/skill_usage_tracker ~/.claude/plugins/

# 必要なディレクトリを作成
mkdir -p ~/.claude/hooks/state
```

## 使用方法

### スキル使用カウント

スキルを使用すると自動的にカウントされます。特別な操作は不要です。

```bash
# 例: スキルを実行
/skill orchestrating-api-implementation
```

カウントデータは `~/.claude/hooks/state/skill_usage_counts.json` に保存されます：

```json
{
  "orchestrating-api-implementation": 5,
  "figma-design-extractor": 3,
  "nextjs-component-generator": 2
}
```

### 登録リクエスト送信

#### 基本的な使用方法

```bash
# デフォルトURL（https://example.com/register）に送信
sendRegistration.js --payload '{"user":"john@example.com","project":"my-app"}'
```

#### カスタムURL指定

```bash
# カスタムURLを指定
sendRegistration.js \
  --url https://api.myservice.com/v1/register \
  --payload '{"name":"John Doe","email":"john@example.com"}'
```

#### 環境変数で設定

```bash
# 環境変数でURLを設定
export REGISTRATION_URL=https://api.myservice.com/register
sendRegistration.js --payload '{"team":"frontend"}'
```

### 送信されるデータ形式

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "skill_usage_stats": {
    "counts": {
      "orchestrating-api-implementation": 5,
      "figma-design-extractor": 3
    },
    "total_invocations": 8,
    "timestamp": "2025-12-02T10:30:45.123Z"
  }
}
```

## 設定

### 環境変数

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `REGISTRATION_URL` | 登録リクエストの送信先URL | `https://example.com/register` |

設定例（`.bashrc` または `.zshrc`）:

```bash
export REGISTRATION_URL=https://api.yourservice.com/v1/register
```

### URLの変更方法

以下の3つの方法でURLを変更できます（優先度順）:

1. **コマンドライン引数**: `--url` オプション
2. **環境変数**: `REGISTRATION_URL`
3. **デフォルト値**: `https://example.com/register`

## ディレクトリ構造

```
skill_usage_tracker/
├── .claude-plugin/
│   ├── plugin.json           # プラグイン設定
│   └── marketplace.json      # マーケットプレイス情報
├── hooks/
│   ├── hooks.json            # フック設定
│   └── skill_usage_counter.js # スキルカウンタースクリプト
├── tools/
│   └── sendRegistration.js   # 登録リクエスト送信コマンド
└── README.md                 # このファイル
```

## トラブルシューティング

### カウントが保存されない

```bash
# stateディレクトリが存在することを確認
ls -la ~/.claude/hooks/state

# ディレクトリがない場合は作成
mkdir -p ~/.claude/hooks/state
```

### スクリプトが実行できない

```bash
# 実行権限を確認
ls -l ~/.claude/plugins/skill_usage_tracker/hooks/skill_usage_counter.js
ls -l ~/.claude/plugins/skill_usage_tracker/tools/sendRegistration.js

# 実行権限を付与
chmod +x ~/.claude/plugins/skill_usage_tracker/hooks/skill_usage_counter.js
chmod +x ~/.claude/plugins/skill_usage_tracker/tools/sendRegistration.js
```

### 接続エラー

```bash
# URLが正しいか確認
echo $REGISTRATION_URL

# ネットワーク接続を確認
curl -X POST https://example.com/register \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

## 開発者向け情報

### フックの仕組み

1. Claude Codeが `Skill` ツールを実行
2. `PostToolUse` イベントが発火
3. `skill_usage_counter.js` が標準入力からツール情報を受け取る
4. `tool_input.skill` からスキル名を抽出
5. `~/.claude/hooks/state/skill_usage_counts.json` を更新

### カスタマイズ

#### 保存先を変更

`skill_usage_counter.js` の以下の行を編集:

```javascript
const STATE_DIR = path.join(os.homedir(), '.claude', 'hooks', 'state');
```

#### デフォルトURLを変更

`sendRegistration.js` の以下の行を編集:

```javascript
const DEFAULT_URL = process.env.REGISTRATION_URL || 'https://your-custom-url.com/register';
```

## 必要な環境

- Claude Code 0.1.0 以上
- Node.js 18.0.0 以上（ネイティブ fetch API サポートのため）
  - または Node.js 14.0.0 以上 + node-fetch パッケージ

## 作成者

**HINO, Yasushi**
- Email: y.hino@xtone.co.jp
- Organization: XTONE

## バージョン履歴

### v0.1.0
- 初期リリース
- スキル使用カウント機能
- 登録リクエスト送信機能

## ライセンス

MIT License

## 参考リンク

- [Claude Code公式ドキュメント](https://docs.claude.com/ja/docs/claude-code)
- [Claude Code Plugins](https://docs.claude.com/ja/docs/claude-code/plugins)
- [Claude Code Hooks](https://docs.claude.com/ja/docs/claude-code/hooks)
