#!/bin/bash

# プロンプト評価結果をログファイルに記録するスクリプト

# ログディレクトリの設定
LOG_DIR="${HOME}/.claude-code/prompt-logs"
mkdir -p "$LOG_DIR"

# 今日の日付でログファイル名を生成
LOG_FILE="${LOG_DIR}/$(date +%Y-%m-%d).jsonl"

# 標準入力からJSONデータを読み取り
input_data=$(cat)

# タイムスタンプを追加
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ユーザープロンプトを取得
user_prompt=$(echo "$input_data" | jq -r '.user_input // empty')

# 前のhookの評価結果を取得（存在する場合）
evaluation=$(echo "$input_data" | jq -c '.hook_results[-1].output // empty' 2>/dev/null)

# ログエントリを作成
log_entry=$(jq -n \
  --arg timestamp "$timestamp" \
  --arg user_prompt "$user_prompt" \
  --argjson evaluation "$evaluation" \
  '{
    timestamp: $timestamp,
    user_prompt: $user_prompt,
    evaluation: $evaluation
  }')

# ログファイルに追記
echo "$log_entry" >> "$LOG_FILE"

# 成功メッセージを出力
echo "Prompt evaluation logged to: $LOG_FILE"
