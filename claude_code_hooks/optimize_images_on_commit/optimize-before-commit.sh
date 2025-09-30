#!/bin/bash

# ============================================
# git commit時の画像最適化Hook
# ============================================

set -euo pipefail

# カラー定義
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RESET='\033[0m'

# 設定
readonly OPTIMIZE_SCRIPT="$HOME/.claude/hooks/optimize-images.sh"
readonly LOG_FILE="$HOME/.claude/logs/commit-optimization.log"

# ログディレクトリ作成
mkdir -p "$(dirname "$LOG_FILE")"

# 標準入力からJSONデータを読み取り
input_data=$(cat)

# コマンドを取得
COMMAND=$(echo "$input_data" | jq -r '.tool_input.command' 2>/dev/null || echo "")

# デバッグ用ログ
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Command: $COMMAND" >> "$LOG_FILE"

# git commitの場合のみ実行
if [[ "$COMMAND" == *"git commit"* ]]; then
    echo -e "${COLOR_BLUE}🎨 Optimizing images before commit...${COLOR_RESET}"

    # ステージング済みの画像を取得
    IMAGES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(jpg|jpeg|png|gif|svg)$' || true)

    if [ -n "$IMAGES" ]; then
        # 画像リスト表示
        echo -e "${COLOR_YELLOW}📸 Found staged images:${COLOR_RESET}"
        echo "$IMAGES" | while read -r image; do
            echo "  - $image"
        done

        # 最適化実行
        OPTIMIZED_COUNT=0
        echo "$IMAGES" | while read -r image; do
            if [ -f "$image" ]; then
                echo -e "${COLOR_BLUE}  Processing: $image${COLOR_RESET}"

                # 最適化スクリプトを実行
                if "$OPTIMIZE_SCRIPT" "$image"; then
                    ((OPTIMIZED_COUNT++))
                    # 最適化後、再ステージング
                    git add "$image"
                fi
            fi
        done

        echo -e "${COLOR_GREEN}✨ Optimization complete!${COLOR_RESET}"
    else
        echo -e "${COLOR_YELLOW}ℹ️  No images to optimize${COLOR_RESET}"
    fi
fi

# 常にコマンドを続行（エラーでも止めない）
exit 0
