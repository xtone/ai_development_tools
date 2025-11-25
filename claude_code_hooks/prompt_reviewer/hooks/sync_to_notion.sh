#!/bin/bash

# ログファイルから Notion へ同期するスクリプト
# このスクリプトは手動実行または定期実行で使用します

LOG_DIR="${HOME}/.claude-code/prompt-logs"
CONFIG_FILE="${HOME}/.claude-code/prompt-reviewer/config.json"
SYNC_STATE_FILE="${HOME}/.claude-code/prompt-reviewer/sync_state.json"

# 設定を確認
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration not found. Run setup_notion_db.sh first."
    exit 1
fi

database_id=$(jq -r '.notion_database_id // ""' "$CONFIG_FILE")
if [ -z "$database_id" ] || [ "$database_id" = "null" ]; then
    echo "Notion database ID not configured."
    exit 1
fi

# 同期状態を読み込み
last_sync_time=""
if [ -f "$SYNC_STATE_FILE" ]; then
    last_sync_time=$(jq -r '.last_sync_time // ""' "$SYNC_STATE_FILE")
fi

echo "Syncing prompt evaluations to Notion..."
echo "Database ID: $database_id"
echo "Last sync: ${last_sync_time:-Never}"
echo ""

# ログファイルを探す
if [ ! -d "$LOG_DIR" ]; then
    echo "No log directory found: $LOG_DIR"
    exit 0
fi

# すべての JSONL ファイルを処理
total_count=0
success_count=0

for log_file in "$LOG_DIR"/*.jsonl; do
    if [ ! -f "$log_file" ]; then
        continue
    fi

    echo "Processing: $(basename "$log_file")"

    # 各行を処理
    while IFS= read -r line; do
        ((total_count++))

        # タイムスタンプを取得
        timestamp=$(echo "$line" | jq -r '.timestamp // ""')

        # 前回の同期以降のレコードのみ処理
        if [ -n "$last_sync_time" ] && [ "$timestamp" \<= "$last_sync_time" ]; then
            continue
        fi

        # 評価データを抽出
        user_prompt=$(echo "$line" | jq -r '.user_prompt // ""')
        score=$(echo "$line" | jq -r '.evaluation.score // 0')
        clarity=$(echo "$line" | jq -r '.evaluation.scores.clarity // 0')
        completeness=$(echo "$line" | jq -r '.evaluation.scores.completeness // 0')
        structure=$(echo "$line" | jq -r '.evaluation.scores.structure // 0')
        feedback=$(echo "$line" | jq -r '.evaluation.feedback // ""')
        improved_prompt=$(echo "$line" | jq -r '.evaluation.improved_prompt // ""')

        # 日付とプレビュー
        date_only=$(echo "$timestamp" | cut -d'T' -f1)
        prompt_preview="${user_prompt:0:100}"
        if [ ${#user_prompt} -gt 100 ]; then
            prompt_preview="${prompt_preview}..."
        fi

        # ページタイトル
        page_title="Prompt Evaluation - ${date_only}"

        # ページ内容
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

        echo "  - Syncing entry: $timestamp (Score: $score/10)"

        # Notion への保存コマンドを実行
        # ここで実際に Notion MCP を使用してページを作成します
        # Claude Code の場合、以下のようなコマンドが必要になります
        # TODO: 実際の Notion MCP 呼び出しを実装

        # 一時的なマーカー（実際の実装では Notion API または MCP を呼び出す）
        # echo "    [Would create Notion page with score: $score]"

        ((success_count++))

    done < "$log_file"
done

# 同期状態を更新
current_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
jq -n \
    --arg last_sync "$current_time" \
    --arg total "$total_count" \
    --arg success "$success_count" \
    '{
        last_sync_time: $last_sync,
        total_processed: ($total | tonumber),
        success_count: ($success | tonumber)
    }' > "$SYNC_STATE_FILE"

echo ""
echo "Sync completed!"
echo "Processed: $total_count entries"
echo "Synced: $success_count new entries"
echo ""
echo "NOTE: Actual Notion integration requires implementing MCP calls."
echo "This script currently only demonstrates the sync logic."
