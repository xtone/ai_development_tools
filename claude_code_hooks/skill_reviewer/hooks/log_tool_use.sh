#!/bin/bash

# Tool/Skill 使用評価結果をログファイルに記録するスクリプト

# ログディレクトリの設定
LOG_DIR="${HOME}/.claude-code/tool-use-logs"
mkdir -p "$LOG_DIR"

# 今日の日付でログファイル名を生成
LOG_FILE="${LOG_DIR}/$(date +%Y-%m-%d).jsonl"

# 標準入力からJSONデータを読み取り
input_data=$(cat)

# タイムスタンプを追加
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ツール情報を取得
tool_name=$(echo "$input_data" | jq -r '.tool_name // empty')
tool_input=$(echo "$input_data" | jq -c '.tool_input // {}')
tool_output=$(echo "$input_data" | jq -c '.tool_output // empty')

# 前のhookの評価結果を取得（存在する場合）
evaluation=$(echo "$input_data" | jq -c '.hook_results[-1].output // empty' 2>/dev/null)

# ログエントリを作成
log_entry=$(jq -n \
  --arg timestamp "$timestamp" \
  --arg tool_name "$tool_name" \
  --argjson tool_input "$tool_input" \
  --arg tool_output "$tool_output" \
  --argjson evaluation "$evaluation" \
  '{
    timestamp: $timestamp,
    tool_name: $tool_name,
    tool_input: $tool_input,
    tool_output: $tool_output,
    evaluation: $evaluation
  }')

# ログファイルに追記
echo "$log_entry" >> "$LOG_FILE"

# 成功メッセージを出力
echo "Tool use evaluation logged to: $LOG_FILE"
