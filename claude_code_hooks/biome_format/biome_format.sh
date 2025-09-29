#!/bin/bash

# 対象プロジェクトディレクトリのリスト
# ルートディレクトリを加えたい場合は"."を追加してください。
PROJECT_DIRS=(
    "."
)

# 対象ファイル拡張子のリスト
TARGET_EXTENSIONS=("ts" "tsx")

# 標準入力からJSONデータを読み取り
input_data=$(cat)

# ファイルパスを取得
file_path=$(echo "$input_data" | jq -r '.tool_input.file_path')

# プロジェクトのルートディレクトリを取得
project_root=$(pwd)

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

# 対象プロジェクトディレクトリを検索
project_dir=""
for dir in "${PROJECT_DIRS[@]}"; do
    if [ "$dir" = "." ]; then
        # rootディレクトリの場合は、他のサブディレクトリに含まれないファイルかチェック
        is_in_subdir=false
        for subdir in "${PROJECT_DIRS[@]}"; do
            if [ "$subdir" != "." ] && [[ "$file_path" == *"$subdir"* ]]; then
                is_in_subdir=true
                break
            fi
        done
        if [ "$is_in_subdir" = false ]; then
            project_dir="$dir"
            break
        fi
    elif [[ "$file_path" == *"$dir"* ]]; then
        project_dir="$dir"
        break
    fi
done

# プロジェクトディレクトリが特定された場合のみ処理
if [ -n "$project_dir" ]; then
    # biome.jsonが存在するかチェック
    if [ -f "$project_dir/biome.json" ]; then
        echo "Formatting $file_path with Biome in $project_dir"
        cd "$project_dir"

        # 相対パスを計算
        if [[ "$file_path" == /* ]]; then
            # 絶対パスの場合
            relative_path=$(echo "$file_path" | sed "s|^$project_root/$project_dir/||")
        else
            # 相対パスの場合
            relative_path=$(echo "$file_path" | sed "s|^$project_dir/||")
        fi

        # ファイルが存在する場合のみフォーマット実行
        if [ -f "$relative_path" ]; then
            npx @biomejs/biome format --write "$relative_path"
        else
            echo "File not found: $relative_path"
        fi
    else
        echo "biome.json not found in $project_dir, skipping format"
    fi
else
    echo "No matching project directory found for: $file_path"
fi

