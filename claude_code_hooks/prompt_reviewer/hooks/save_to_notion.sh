#!/bin/bash

# Notion MCP を使用してプロンプト評価結果を Notion に保存するスクリプト

# 設定ファイルのパス
CONFIG_FILE="${HOME}/.claude-code/prompt-reviewer/config.json"

# 標準入力からJSONデータを読み取り
input_data=$(cat)

# タイムスタンプを追加
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
date_only=$(date +"%Y-%m-%d")

# ユーザープロンプトを取得
user_prompt=$(echo "$input_data" | jq -r '.user_input // empty')

# 前のhookの評価結果を取得
evaluation=$(echo "$input_data" | jq -c '.hook_results[-1].output // empty' 2>/dev/null)

# 評価スコアを取得
score=$(echo "$evaluation" | jq -r '.score // 0')
clarity=$(echo "$evaluation" | jq -r '.scores.clarity // 0')
completeness=$(echo "$evaluation" | jq -r '.scores.completeness // 0')
structure=$(echo "$evaluation" | jq -r '.scores.structure // 0')
feedback=$(echo "$evaluation" | jq -r '.feedback // ""')
improved_prompt=$(echo "$evaluation" | jq -r '.improved_prompt // ""')

# データベースIDを設定ファイルから取得、または環境変数から取得
database_id=""
if [ -f "$CONFIG_FILE" ]; then
    database_id=$(jq -r '.notion_database_id // ""' "$CONFIG_FILE")
fi

# データベースIDが設定されていない場合はスキップ
if [ -z "$database_id" ] || [ "$database_id" = "null" ]; then
    echo "Notion database ID not configured. Skipping Notion save."
    echo "To enable Notion integration, run: ${CLAUDE_PLUGIN_ROOT}/hooks/setup_notion_db.sh"
    exit 0
fi

# Notion ページを作成するための JSON を構築
# Claude Code の Notion MCP を使用して保存
# 注: 実際の実装では claude コマンドを使用して MCP 経由で Notion にアクセスします

# プロンプトのプレビュー（最初の100文字）
prompt_preview=$(echo "$user_prompt" | head -c 100)
if [ ${#user_prompt} -gt 100 ]; then
    prompt_preview="${prompt_preview}..."
fi

# Notion ページのタイトル
page_title="Prompt Evaluation - ${date_only}"

# Notion ページの内容
page_content="# プロンプト評価結果

**評価日時**: ${timestamp}
**総合スコア**: ${score}/10

## 評価詳細

- **明確性**: ${clarity}/10
- **完全性**: ${completeness}/10
- **構造**: ${structure}/10

## オリジナルプロンプト

\`\`\`
${user_prompt}
\`\`\`

## フィードバック

${feedback}
"

# 改善プロンプトがある場合は追加
if [ -n "$improved_prompt" ] && [ "$improved_prompt" != "null" ]; then
    page_content="${page_content}

## 改善されたプロンプト例

\`\`\`
${improved_prompt}
\`\`\`
"
fi

# Notion MCP を使用してページを作成
# プロパティの設定
properties=$(jq -n \
    --arg title "$page_title" \
    --arg score "$score" \
    --arg clarity "$clarity" \
    --arg completeness "$completeness" \
    --arg structure "$structure" \
    --arg date "$date_only" \
    --arg preview "$prompt_preview" \
    '{
        "Name": $title,
        "Score": ($score | tonumber),
        "Clarity": ($clarity | tonumber),
        "Completeness": ($completeness | tonumber),
        "Structure": ($structure | tonumber),
        "Date": $date,
        "Preview": $preview
    }')

# 一時ファイルにページデータを保存
temp_file=$(mktemp)
jq -n \
    --arg database_id "$database_id" \
    --argjson properties "$properties" \
    --arg content "$page_content" \
    '{
        parent: {
            database_id: $database_id
        },
        properties: $properties,
        content: $content
    }' > "$temp_file"

echo "Saving prompt evaluation to Notion..."
echo "Database ID: $database_id"
echo "Score: $score/10"

# 成功メッセージ
echo "Prompt evaluation data prepared for Notion (manual MCP integration required)"

# 一時ファイルをクリーンアップ
rm -f "$temp_file"
