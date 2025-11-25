# Prompt Reviewer Hook

Claude Codeに送信するプロンプトを自動的に評価し、品質スコアと改善提案を提供するプラグインです。

## 機能

### 1. プロンプト品質評価

ユーザーがプロンプトを送信する際、自動的に以下の観点で評価します：

- **明確性** (1-10点): 要求が具体的で理解しやすいか
  - 曖昧な表現がないか
  - 期待する成果物が明確か
  - 専門用語が適切に使用されているか

- **完全性** (1-10点): 必要な情報が含まれているか
  - コンテキストが十分に提供されているか
  - 制約条件が明示されているか
  - 期待する出力形式が指定されているか

- **構造** (1-10点): 適切にフォーマットされているか
  - 論理的な順序で記述されているか
  - 重要な情報が強調されているか
  - 読みやすく整理されているか

### 2. プロンプト改善提案

- 総合スコアが8未満の場合、具体的な改善案を提示
- スコアが6未満の場合は、改善されたプロンプト例も提供
- プロンプトは常に送信されます（ブロックしません）

### 3. プロンプト履歴ログ

すべてのプロンプトと評価結果を自動的にログファイルに記録：

- **保存先**: `~/.claude-code/prompt-logs/YYYY-MM-DD.jsonl`
- **形式**: JSONL（1行1レコード）
- **記録内容**:
  - タイムスタンプ
  - オリジナルプロンプト
  - 評価スコア（総合・項目別）
  - 改善提案
  - 改善プロンプト例（該当する場合）

## セットアップ

### Plugin Marketplaceからインストール（推奨）

1. Claude Codeでマーケットプレイスにリポジトリを追加（未追加の場合）:

```bash
/plugin marketplace add xtone/ai_development_tools
```

2. プラグインをインストール:

```bash
/plugin install prompt-reviewer@xtone-ai-development-tools
```

### 手動インストール

1. このディレクトリ全体を任意の場所にコピー

2. Claude Codeの設定に以下を追加:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "<hooks.json内のプロンプト内容>",
            "timeout": 30000,
            "output_as": "json",
            "model": "haiku"
          },
          {
            "type": "command",
            "command": "/path/to/log_prompt.sh"
          }
        ]
      }
    ]
  }
}
```

## 動作イメージ

### 評価結果の表示例

プロンプトを送信すると、以下のような評価結果が表示されます：

```json
{
  "score": 7,
  "scores": {
    "clarity": 8,
    "completeness": 6,
    "structure": 7
  },
  "feedback": "プロンプトは明確ですが、期待する出力形式が明示されていません。また、制約条件（例：使用技術、パフォーマンス要件など）を追加すると、より良い結果が得られます。",
  "improved_prompt": null,
  "decision": "allow"
}
```

### ログファイルの例

`~/.claude-code/prompt-logs/2025-01-15.jsonl`:

```jsonl
{"timestamp":"2025-01-15T10:30:45Z","user_prompt":"Reactコンポーネントを作成して","evaluation":{"score":5,"scores":{"clarity":4,"completeness":3,"structure":6},"feedback":"プロンプトが曖昧です。どのようなコンポーネントを作成したいか、具体的な要件を追加してください。","improved_prompt":"TypeScript + React で、ユーザープロフィール表示用のコンポーネントを作成してください。\n\n要件:\n- 名前、メールアドレス、アバター画像を表示\n- props で情報を受け取る\n- Tailwind CSS でスタイリング\n- レスポンシブ対応","decision":"allow"}}
{"timestamp":"2025-01-15T10:35:22Z","user_prompt":"TypeScript + React で、ユーザー一覧表示用のテーブルコンポーネントを作成してください。ソート機能とページネーション機能を含めてください。","evaluation":{"score":9,"scores":{"clarity":9,"completeness":9,"structure":9},"feedback":"優れたプロンプトです。要件が明確で具体的です。","improved_prompt":null,"decision":"allow"}}
```

## ログファイルの活用

ログファイルは以下のように活用できます：

```bash
# 今日のログを確認
cat ~/.claude-code/prompt-logs/$(date +%Y-%m-%d).jsonl

# スコアが低いプロンプトを抽出
cat ~/.claude-code/prompt-logs/*.jsonl | jq 'select(.evaluation.score < 6)'

# 平均スコアを計算
cat ~/.claude-code/prompt-logs/*.jsonl | jq -s 'map(.evaluation.score) | add / length'
```

## Notion 連携（オプション）

プロンプト評価結果を Notion データベースに保存することができます。

### セットアップ

1. **Notion データベースの準備**

   以下のスクリプトを実行して、Notion データベースをセットアップします：

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/hooks/setup_notion_db.sh
   ```

   このスクリプトは以下の2つのオプションを提供します：
   - 新しい Notion データベースを作成（手動で Claude Code 経由で作成）
   - 既存の Notion データベースを使用（データベース ID を指定）

2. **Notion データベースのスキーマ**

   データベースには以下のプロパティが必要です：

   | プロパティ名 | 型 | 説明 |
   |------------|-----|------|
   | Name | Title | プロンプト評価のタイトル |
   | Score | Number | 総合スコア (1-10) |
   | Clarity | Number | 明確性スコア (1-10) |
   | Completeness | Number | 完全性スコア (1-10) |
   | Structure | Number | 構造スコア (1-10) |
   | Date | Date | 評価日 |
   | Preview | Rich Text | プロンプトのプレビュー |

3. **Notion への同期**

   ログファイルから Notion へ同期するには、以下のコマンドを実行します：

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/hooks/sync_to_notion.sh
   ```

   このスクリプトは：
   - 未同期のログエントリを検出
   - 各エントリを Notion データベースに追加
   - 同期状態を記録（重複を防止）

### 自動同期の設定（オプション）

定期的に自動同期するには、cron を使用します：

```bash
# crontab を編集
crontab -e

# 例: 毎時0分に同期（プラグインのパスを適切に設定してください）
0 * * * * ~/.claude-code/plugins/prompt-reviewer@xtone-ai-development-tools/hooks/sync_to_notion.sh
```

### Notion API との統合

`sync_to_notion.sh` スクリプトは Notion API を直接呼び出して、評価結果をデータベースに保存します。

#### Notion Integration Token の取得

1. [Notion Integrations](https://www.notion.so/my-integrations) にアクセス
2. "New integration" をクリック
3. Integration に名前を付けて作成
4. "Internal Integration Token" をコピー
5. データベースがあるページで、"..." メニューから "Connections" → 作成した Integration を追加

#### 環境変数の設定

Notion Token を環境変数として設定します：

```bash
# ~/.bashrc または ~/.zshrc に追加
export NOTION_TOKEN="secret_xxxxxxxxxxxxxxxxxxxxx"
```

設定後、シェルを再起動するか `source ~/.bashrc` を実行してください。

#### 同期の実行

Token を設定後、同期スクリプトを実行すると、実際に Notion にデータが保存されます：

```bash
${CLAUDE_PLUGIN_ROOT}/hooks/sync_to_notion.sh
```

#### デバッグモード

同期がうまくいかない場合は、デバッグモードで実行してください：

```bash
DEBUG=1 ${CLAUDE_PLUGIN_ROOT}/hooks/sync_to_notion.sh
```

#### 代替方法: Claude Code の Notion MCP を使用

Notion API の代わりに、Claude Code の Notion MCP を使用することもできます。この場合は `sync_to_notion.sh` をカスタマイズして、Claude Code の MCP エンドポイントを呼び出すように変更してください。

詳細は [Notion MCP ドキュメント](https://code.claude.com/docs/en/mcp-servers) を参照してください。

## カスタマイズ

### 評価基準の調整

`hooks/hooks.json` 内のプロンプトを編集することで、評価基準を調整できます。

### ログ保存先の変更

`hooks/log_prompt.sh` 内の `LOG_DIR` 変数を変更してください：

```bash
LOG_DIR="${HOME}/custom/path/to/logs"
```

### モデルの変更

デフォルトは Haiku ですが、より詳細な評価が必要な場合は Claude Sonnet に変更できます：

```json
{
  "type": "prompt",
  "model": "sonnet"
}
```

注意: Sonnet を使用すると評価時間が長くなります。

## 前提条件

- Claude Code がインストールされていること
- `jq` コマンドが利用可能であること（ログスクリプト用）

## 注意事項

- プロンプトは常に送信されます（ブロックされません）
- 評価には数秒かかる場合があります
- ログファイルは自動的に日付ごとに分割されます
- プライベートな情報を含むプロンプトもログに記録されるため、ログファイルの取り扱いに注意してください

## トラブルシューティング

### 評価が表示されない

- Claude Code の hooks 設定が正しく読み込まれているか確認してください
- プラグインが正しくインストールされているか確認してください

### ログファイルが作成されない

- `jq` コマンドがインストールされているか確認してください
- ログディレクトリ (`~/.claude-code/prompt-logs/`) への書き込み権限があるか確認してください

## ライセンス

Released under the MIT license
