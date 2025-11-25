#!/bin/bash

# Notion にプロンプト評価用データベースをセットアップするスクリプト

echo "===================================="
echo "Prompt Reviewer - Notion Database Setup"
echo "===================================="
echo ""
echo "This script will guide you through setting up a Notion database for storing prompt evaluations."
echo ""

# 設定ディレクトリの作成
CONFIG_DIR="${HOME}/.claude-code/prompt-reviewer"
CONFIG_FILE="${CONFIG_DIR}/config.json"
mkdir -p "$CONFIG_DIR"

# 既存の設定を確認
if [ -f "$CONFIG_FILE" ]; then
    echo "Existing configuration found:"
    cat "$CONFIG_FILE" | jq '.'
    echo ""
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [ "$reconfigure" != "y" ] && [ "$reconfigure" != "Y" ]; then
        echo "Configuration unchanged."
        exit 0
    fi
fi

echo "Setup Options:"
echo "1) Create a new Notion database automatically"
echo "2) Use an existing Notion database (provide database ID)"
echo ""
read -p "Select an option (1 or 2): " option

case $option in
    1)
        echo ""
        echo "Creating a new Notion database..."
        echo ""
        echo "Database Schema:"
        echo "- Name (Title): Prompt evaluation title"
        echo "- Score (Number): Overall quality score (1-10)"
        echo "- Clarity (Number): Clarity score (1-10)"
        echo "- Completeness (Number): Completeness score (1-10)"
        echo "- Structure (Number): Structure score (1-10)"
        echo "- Date (Date): Evaluation date"
        echo "- Preview (Text): Prompt preview"
        echo ""

        # データベース作成用の JSON
        db_definition=$(cat <<'EOF'
{
  "title": [{"type": "text", "text": {"content": "Prompt Evaluations"}}],
  "properties": {
    "Name": {
      "title": {}
    },
    "Score": {
      "number": {"format": "number"}
    },
    "Clarity": {
      "number": {"format": "number"}
    },
    "Completeness": {
      "number": {"format": "number"}
    },
    "Structure": {
      "number": {"format": "number"}
    },
    "Date": {
      "date": {}
    },
    "Preview": {
      "rich_text": {}
    }
  }
}
EOF
        )

        echo "Database definition:"
        echo "$db_definition" | jq '.'
        echo ""
        echo "NOTE: To create this database, you need to use Claude Code with Notion MCP enabled."
        echo "Run the following command in Claude Code:"
        echo ""
        echo "  Create a new Notion database with the above schema"
        echo ""
        echo "After creating the database, you'll receive a database ID."
        read -p "Enter the database ID: " database_id
        ;;

    2)
        echo ""
        echo "Using existing Notion database..."
        echo ""
        echo "Your database should have the following properties:"
        echo "- Name (Title)"
        echo "- Score (Number)"
        echo "- Clarity (Number)"
        echo "- Completeness (Number)"
        echo "- Structure (Number)"
        echo "- Date (Date)"
        echo "- Preview (Rich Text)"
        echo ""
        read -p "Enter the database ID or URL: " database_input

        # URL からデータベース ID を抽出
        if [[ "$database_input" =~ https://www.notion.so/.*/([a-f0-9]{32}) ]]; then
            database_id="${BASH_REMATCH[1]}"
            echo "Extracted database ID: $database_id"
        elif [[ "$database_input" =~ ^[a-f0-9]{32}$ ]]; then
            database_id="$database_input"
        else
            # ハイフン付きの UUID も受け付ける
            database_id=$(echo "$database_input" | tr -d '-')
        fi
        ;;

    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

# 設定を保存
if [ -n "$database_id" ]; then
    jq -n \
        --arg db_id "$database_id" \
        --arg enabled "true" \
        '{
            notion_database_id: $db_id,
            notion_enabled: ($enabled == "true")
        }' > "$CONFIG_FILE"

    echo ""
    echo "✓ Configuration saved to: $CONFIG_FILE"
    echo "✓ Notion database ID: $database_id"
    echo ""
    echo "Notion integration is now enabled!"
    echo "Prompt evaluations will be automatically saved to Notion."
else
    echo ""
    echo "✗ Invalid database ID. Configuration not saved."
    exit 1
fi
