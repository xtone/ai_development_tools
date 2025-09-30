#!/bin/bash

# 対象ファイル拡張子のリスト
TARGET_EXTENSIONS=("ts" "tsx" "js" "jsx")

# 標準入力からJSONデータを読み取り
input_data=$(cat)

# ファイルパスを取得
file_path=$(echo "$input_data" | jq -r '.tool_input.file_path')

# 対象ファイル拡張子かチェック
is_target_file=false
for ext in "${TARGET_EXTENSIONS[@]}"; do
    if [[ "$file_path" == *".$ext" ]]; then
        is_target_file=true
        break
    fi
done

if [ "$is_target_file" = false ]; then
    echo "Not a target file extension: $file_path"
    exit 0
fi

# ファイルパスを絶対パスに変換
if [[ "$file_path" != /* ]]; then
    file_path="$(pwd)/$file_path"
fi

# ファイルが存在するかチェック
if [ ! -f "$file_path" ]; then
    echo "File not found: $file_path"
    exit 1
fi

# ファイルのディレクトリから上位ディレクトリへ遡ってbiome.jsonを探す
find_biome_config() {
    local current_dir="$1"

    while [ "$current_dir" != "/" ]; do
        if [ -f "$current_dir/biome.json" ]; then
            echo "$current_dir"
            return 0
        fi
        current_dir=$(dirname "$current_dir")
    done

    return 1
}

# ファイルのディレクトリを取得
file_dir=$(dirname "$file_path")

# biome.jsonを探す
config_dir=$(find_biome_config "$file_dir")

if [ -z "$config_dir" ]; then
    echo "biome.json not found in any parent directory of: $file_path"
    exit 0
fi

echo "Found biome.json in: $config_dir"
echo "Formatting $file_path with Biome"

# biome formatを実行（--config-pathで明示的に設定ファイルの場所を指定）
npx @biomejs/biome format --config-path="$config_dir" --write "$file_path"