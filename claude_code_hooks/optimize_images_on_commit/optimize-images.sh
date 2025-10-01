#!/bin/bash

# ============================================
# Claude Code Image Optimization Hook
# 画像ファイルのロスレス/高品質圧縮スクリプト
# ============================================

set -euo pipefail

# ============================================
# 設定
# ============================================

readonly SCRIPT_NAME="Image Optimization Hook"
readonly VERSION="1.0.0"

# 圧縮設定
readonly MIN_SIZE_THRESHOLD=10240  # 10KB
readonly JPEG_QUALITY=85
readonly PNG_OPTIMIZATION_LEVEL=2
readonly GIF_OPTIMIZATION_LEVEL=3

# パス設定
readonly LOG_DIR="$HOME/.claude/logs"
readonly LOG_FILE="$LOG_DIR/image-optimization.log"
readonly BACKUP_SUFFIX=".backup"
readonly TEMP_SUFFIX=".tmp"

# カラーコード
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RESET='\033[0m'

# ============================================
# 初期化
# ============================================

initialize() {
    # ログディレクトリ作成
    mkdir -p "$LOG_DIR"

    # 一時ファイルのクリーンアップ設定
    trap cleanup EXIT INT TERM
}

cleanup() {
    find . -maxdepth 1 \( -name "*${BACKUP_SUFFIX}" -o -name "*${TEMP_SUFFIX}" \) -delete 2>/dev/null || true
}

# ============================================
# ロギング
# ============================================

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local color=""

    case "$level" in
        ERROR)   color="$COLOR_RED" ;;
        SUCCESS) color="$COLOR_GREEN" ;;
        WARNING) color="$COLOR_YELLOW" ;;
        INFO)    color="$COLOR_BLUE" ;;
        *)       color="$COLOR_RESET" ;;
    esac

    # ログファイルに出力（カラーコードなし）
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"

    # コンソールに出力（カラーコードあり）
    echo -e "${color}${message}${COLOR_RESET}"
}

# ============================================
# ユーティリティ関数
# ============================================

format_size() {
    local bytes="$1"

    if (( bytes > 1048576 )); then
        printf "%.2fMB" "$(echo "scale=2; $bytes / 1048576" | bc)"
    elif (( bytes > 1024 )); then
        printf "%.2fKB" "$(echo "scale=2; $bytes / 1024" | bc)"
    else
        printf "%dB" "$bytes"
    fi
}

get_file_size() {
    local file="$1"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        stat -f%z "$file" 2>/dev/null || echo 0
    else
        stat -c%s "$file" 2>/dev/null || echo 0
    fi
}

calculate_savings_percent() {
    local original="$1"
    local compressed="$2"

    if (( original > 0 )); then
        echo "scale=1; 100 - ($compressed * 100 / $original)" | bc
    else
        echo "0"
    fi
}

create_backup() {
    local file="$1"
    cp "$file" "${file}${BACKUP_SUFFIX}"
}

restore_backup() {
    local file="$1"
    if [[ -f "${file}${BACKUP_SUFFIX}" ]]; then
        mv "${file}${BACKUP_SUFFIX}" "$file"
    fi
}

remove_backup() {
    local file="$1"
    rm -f "${file}${BACKUP_SUFFIX}"
}

# ============================================
# 依存関係管理
# ============================================

check_command() {
    local cmd="$1"
    command -v "$cmd" >/dev/null 2>&1
}

ensure_dependencies() {
    local required_tools=("jpegoptim" "optipng")
    local optional_tools=("gifsicle" "svgo")
    local missing_required=()
    local missing_optional=()

    # 必須ツールのチェック
    for tool in "${required_tools[@]}"; do
        if ! check_command "$tool"; then
            missing_required+=("$tool")
        fi
    done

    # オプションツールのチェック
    for tool in "${optional_tools[@]}"; do
        if ! check_command "$tool"; then
            missing_optional+=("$tool")
        fi
    done

    # 必須ツールがない場合はエラー
    if (( ${#missing_required[@]} > 0 )); then
        log ERROR "Missing required tools: ${missing_required[*]}"
        log ERROR "Please install them manually:"

        if [[ "$OSTYPE" == "darwin"* ]]; then
            log ERROR "  brew install ${missing_required[*]}"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            log ERROR "  sudo apt-get install ${missing_required[*]}"
        fi

        return 1
    fi

    # オプションツールの警告
    if (( ${#missing_optional[@]} > 0 )); then
        log WARNING "Optional tools not found: ${missing_optional[*]} (some formats will be skipped)"
    fi

    return 0
}

# ============================================
# 画像最適化クラス
# ============================================

class_ImageOptimizer() {
    local file="$1"
    local file_type="$2"
    local original_size
    local new_size
    local savings

    # サイズチェック
    original_size=$(get_file_size "$file")
    if (( original_size < MIN_SIZE_THRESHOLD )); then
        log WARNING "⏭️  Skipping small file: $(basename "$file") ($(format_size "$original_size"))"
        return 0
    fi

    # バックアップ作成
    create_backup "$file"

    # タイプ別最適化
    case "$file_type" in
        jpeg) optimize_jpeg "$file" ;;
        png)  optimize_png "$file" ;;
        gif)  optimize_gif "$file" ;;
        svg)  optimize_svg "$file" ;;
        *)
            remove_backup "$file"
            return 1
            ;;
    esac

    # 結果確認
    new_size=$(get_file_size "$file")

    if (( new_size >= original_size )); then
        restore_backup "$file"
        log WARNING "⏭️  Already optimized: $(basename "$file")"
    else
        remove_backup "$file"
        savings=$(calculate_savings_percent "$original_size" "$new_size")
        log SUCCESS "✅ Optimized: $(basename "$file") | Saved: ${savings}% ($(format_size "$original_size") → $(format_size "$new_size"))"
    fi

    return 0
}

# ============================================
# 最適化関数（個別）
# ============================================

optimize_jpeg() {
    local file="$1"

    if check_command jpegoptim; then
        jpegoptim \
            --max="$JPEG_QUALITY" \
            --strip-all \
            --all-progressive \
            --preserve \
            --quiet \
            "$file" 2>/dev/null || return 1
    else
        log ERROR "jpegoptim not available"
        return 1
    fi
}

optimize_png() {
    local file="$1"

    if check_command optipng; then
        optipng \
            -o"$PNG_OPTIMIZATION_LEVEL" \
            -preserve \
            -quiet \
            "$file" 2>/dev/null || return 1
    else
        log ERROR "optipng not available"
        return 1
    fi
}

optimize_gif() {
    local file="$1"
    local temp_file="${file}${TEMP_SUFFIX}"

    if check_command gifsicle; then
        gifsicle \
            --optimize="$GIF_OPTIMIZATION_LEVEL" \
            --colors 256 \
            "$file" \
            -o "$temp_file" 2>/dev/null || return 1

        if [[ -f "$temp_file" ]]; then
            mv "$temp_file" "$file"
        fi
    else
        log INFO "gifsicle not available - skipping GIF optimization"
        return 1
    fi
}

optimize_svg() {
    local file="$1"
    local temp_file="${file}${TEMP_SUFFIX}"

    if check_command svgo; then
        svgo "$file" -o "$temp_file" --quiet 2>/dev/null || return 1
    elif check_command npx; then
        npx svgo "$file" -o "$temp_file" --quiet 2>/dev/null || return 1
    else
        log INFO "svgo not available - skipping SVG optimization"
        return 1
    fi

    if [[ -f "$temp_file" ]]; then
        mv "$temp_file" "$file"
    fi
}

# ============================================
# ファイル処理
# ============================================

get_file_type() {
    local file="$1"
    local extension="${file##*.}"

    case "${extension,,}" in
        jpg|jpeg) echo "jpeg" ;;
        png)      echo "png" ;;
        gif)      echo "gif" ;;
        svg)      echo "svg" ;;
        webp)     echo "webp" ;;
        *)        echo "unknown" ;;
    esac
}

process_file() {
    local file="$1"

    # ファイル存在チェック
    if [[ ! -f "$file" ]]; then
        log WARNING "File not found: $file"
        return 1
    fi

    # ファイルタイプ判定
    local file_type=$(get_file_type "$file")

    case "$file_type" in
        jpeg|png|gif|svg)
            class_ImageOptimizer "$file" "$file_type"
            return $?
            ;;
        webp)
            log INFO "WebP file skipped: $(basename "$file")"
            return 0
            ;;
        *)
            log WARNING "Unknown file type: $(basename "$file")"
            return 1
            ;;
    esac
}

# ============================================
# メイン処理
# ============================================

main() {
    log INFO "🎨 $SCRIPT_NAME v$VERSION Started"

    # 初期化
    initialize

    # 依存関係チェック
    if ! ensure_dependencies; then
        log ERROR "Dependency check failed"
        exit 1
    fi

    local files_processed=0
    local files_optimized=0

    # 引数として直接ファイルが渡された場合
    if [[ $# -gt 0 ]]; then
        for file in "$@"; do
            if process_file "$file"; then
                ((files_optimized++))
            fi
            ((files_processed++))
        done
    # Claude Codeから環境変数で渡された場合
    elif [[ -n "${CLAUDE_FILE_PATHS:-}" ]]; then
        IFS=' ' read -ra FILES <<< "$CLAUDE_FILE_PATHS"

        for file in "${FILES[@]}"; do
            if process_file "$file"; then
                ((files_optimized++))
            fi
            ((files_processed++))
        done
    else
        log WARNING "No files provided"
    fi

    # サマリー
    if (( files_processed > 0 )); then
        log SUCCESS "✨ Complete: ${files_optimized}/${files_processed} files optimized"
    else
        log INFO "No images to process"
    fi

    return 0
}

# ============================================
# エントリーポイント
# ============================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
