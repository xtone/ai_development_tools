# Skill Reviewer Hook

Claude Code でツールやスキルを使用する際に、自動的に使用品質を評価し、改善提案を提供するプラグインです。

## 🎯 このプラグインは何をするのか？

Claude Code で**ツール（Read, Write, Bash など）やスキル（Task）を使用するたびに**、その使い方を自動的に評価し、より効率的な方法を提案します。

## ⚡ 自動で動くタイミング

プラグインをインストールすると、**すべてのツール使用後に自動的に評価**されます：

- ✅ ファイルを読み込んだ時（`Read` ツール）
- ✅ ファイルを編集・作成した時（`Edit`, `Write` ツール）
- ✅ コマンドを実行した時（`Bash` ツール）
- ✅ スキルを実行した時（`Task` ツール）
- ✅ その他、すべてのツール使用時

**ユーザーが何もする必要はありません**。自動的に評価され、フィードバックが表示されます。

## 📊 評価内容

### 評価される3つの観点（各1-10点）

1. **適切性 (Appropriateness)**
   - タスクに対して最適なツールを選択しているか
   - ツールのパラメータが適切に設定されているか
   - より効率的な代替手段がないか

2. **効率性 (Efficiency)**
   - 必要最小限のツール呼び出しで済んでいるか
   - 並列実行可能な場合に活用しているか
   - 不要なツール呼び出しがないか

3. **結果品質 (Result Quality)**
   - 期待される結果が得られているか
   - エラーハンドリングが適切か
   - 結果の検証が行われているか

### 評価結果の表示例

ツール使用後、以下のような評価結果が自動的に表示されます：

```json
{
  "score": 7,
  "scores": {
    "appropriateness": 8,
    "efficiency": 6,
    "result_quality": 7
  },
  "feedback": "Read ツールの使用は適切ですが、複数のファイルを読む場合は並列で Read を実行すると効率的です。",
  "suggested_approach": null,
  "decision": "allow"
}
```

## 📁 評価結果の保存

### 自動表示
評価結果は**ツール使用直後に自動的に表示**されます。コマンドを打って確認する必要はありません。

### バックグラウンドログ
すべての評価結果は自動的にログファイルに記録されます：

**保存場所:**
```
~/.claude-code/tool-use-logs/YYYY-MM-DD.jsonl
```

**用途:**
- Notion への同期用データソース
- 長期的な使用傾向の分析
- デバッグ時の確認用

**注意:** ログファイルは手動で確認することを想定していません。Notion 連携で可視化することを推奨します。

## 🚀 セットアップ

### インストール（推奨方法）

**Step 1: マーケットプレイスを追加（初回のみ）**
```bash
/plugin marketplace add xtone/ai_development_tools
```

**Step 2: プラグインをインストール**
```bash
/plugin install skill-reviewer@xtone-ai-development-tools
```

**Step 3: Claude Code を再起動**

これで完了です！次回からツールを使用すると自動的に評価されます。

### 動作確認

インストール後、適当なファイルを読み込んでみてください：

```
src/index.ts の内容を確認してください
```

ファイルが読み込まれた後、評価結果が表示されれば正常に動作しています。

## 📊 評価結果の確認方法

### リアルタイム表示
**ツール使用直後に自動的に表示されます。**

例：
```json
{
  "score": 7,
  "scores": {
    "appropriateness": 8,
    "efficiency": 6,
    "result_quality": 7
  },
  "feedback": "Read ツールの使用は適切ですが、複数のファイルを読む場合は並列で Read を実行すると効率的です。"
}
```

### 長期的な分析
**Notion 連携を使用して可視化します（次のセクション参照）。**

ログファイルは Notion への同期用のデータソースとして自動的に使用されます。

## 🔗 Notion 連携（オプション）

ツール使用の評価結果を Notion データベースに保存することができます。

### Notion MCP を使用（推奨）

このプラグインには Notion MCP サーバーの設定が含まれています。

**セットアップ:**

1. Claude Code を再起動（プラグインインストール時に自動設定済み）

2. Notion MCP の初回使用時に OAuth 認証が自動的に開始されます
   - ブラウザで Notion のログイン画面が開きます
   - アクセスを許可してください
   - 認証情報は自動的に保存されます

3. Notion データベースを準備:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/hooks/setup_notion_db.sh
   ```

4. ログを Notion に同期:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/hooks/sync_to_notion.sh
   ```

### Notion データベースのスキーマ

データベースには以下のプロパティが必要です：

| プロパティ名 | 型 | 説明 |
|------------|-----|------|
| Name | Title | ツール使用評価のタイトル |
| Score | Number | 総合スコア (1-10) |
| Appropriateness | Number | 適切性スコア (1-10) |
| Efficiency | Number | 効率性スコア (1-10) |
| Result Quality | Number | 結果品質スコア (1-10) |
| Date | Date | 評価日 |
| Tool Name | Text | 使用したツール名 |
| Preview | Rich Text | ツール入力のプレビュー |

### 自動同期の設定（オプション）

定期的に自動同期するには、cron を使用します：

```bash
# crontab を編集
crontab -e

# 例: 毎時0分に同期
0 * * * * ~/.claude-code/plugins/skill-reviewer@xtone-ai-development-tools/hooks/sync_to_notion.sh
```

## ⚙️ カスタマイズ

### 評価基準の調整

`hooks/hooks.json` 内のプロンプトを編集することで、評価基準を調整できます：

```bash
${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json
```

変更例：
- スコアの配点を変更
- 評価項目を追加
- フィードバックの詳細度を調整

### ログ保存先の変更

`hooks/log_tool_use.sh` 内の `LOG_DIR` 変数を変更してください：

```bash
LOG_DIR="${HOME}/custom/path/to/logs"
```

### モデルの変更

デフォルトは Haiku（高速）ですが、より詳細な評価が必要な場合は Sonnet に変更可能：

```json
{
  "type": "prompt",
  "model": "sonnet"
}
```

⚠️ **注意**: Sonnet を使用すると評価時間が長くなります。

## 📋 前提条件

- Claude Code がインストールされていること
- `jq` コマンドが利用可能であること（ログスクリプト用）
- Notion 連携を使用する場合: Notion へのアクセス権限（OAuth 認証）

## ⚠️ 注意事項

- ツール使用は常にブロックされません（評価のみ）
- 評価には数秒かかる場合があります
- ログファイルは自動的に日付ごとに分割されます
- ツールの入出力もログに記録されるため、機密情報の取り扱いに注意してください

## 🔧 トラブルシューティング

### 評価が表示されない

- Claude Code の hooks 設定が正しく読み込まれているか確認
- プラグインが正しくインストールされているか確認
- Claude Code を再起動してみてください

### ログファイルが作成されない

- `jq` コマンドがインストールされているか確認:
  ```bash
  which jq
  ```
- ログディレクトリへの書き込み権限があるか確認:
  ```bash
  ls -la ~/.claude-code/tool-use-logs/
  ```

### Notion 同期がうまくいかない

- Notion MCP の OAuth 認証が完了しているか確認
- データベース ID が正しく設定されているか確認:
  ```bash
  cat ~/.claude-code/skill-reviewer/config.json
  ```
- デバッグモードで実行:
  ```bash
  DEBUG=1 ${CLAUDE_PLUGIN_ROOT}/hooks/sync_to_notion.sh
  ```

## 🎓 使用例

### 例1: 効率的なツール使用

**ユーザーの指示:**
```
src/ ディレクトリ内のすべての .ts ファイルを確認してください
```

**Claude の動作:**
- Glob ツールでファイルを検索
- 並列で複数の Read ツールを実行

**評価結果:**
```json
{
  "score": 9,
  "feedback": "適切なツール選択と並列実行により、効率的にファイルを確認できました。"
}
```

### 例2: 非効率なツール使用

**ユーザーの指示:**
```
src/index.ts の内容を cat コマンドで確認してください
```

**Claude の動作:**
- Bash ツールで cat コマンドを実行

**評価結果:**
```json
{
  "score": 5,
  "feedback": "cat コマンドではなく Read ツールを使用した方が効率的です。Read ツールは構文ハイライトや行番号表示などの機能を提供します。",
  "suggested_approach": "Read ツールを使用: Read(file_path='src/index.ts')"
}
```

## 📚 詳細情報

- [Claude Code 公式ドキュメント](https://code.claude.com/docs)
- [Hooks リファレンス](https://code.claude.com/docs/en/hooks)
- [Notion MCP ドキュメント](https://code.claude.com/docs/en/mcp-servers)

## ライセンス

Released under the MIT license
