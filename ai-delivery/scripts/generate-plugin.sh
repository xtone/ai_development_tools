#!/usr/bin/env bash
# TPL-26 — xtone-plugin-template から新規プラグインスケルトンを生成する。
# Usage:
#   ai-delivery/scripts/generate-plugin.sh <usecase> [options]
#     --description "..."        プラグイン説明
#     --author "..."             著者名
#     --domains "BtoCアプリ,..."  適用ドメイン（T-008 ドメインタクソノミー）
#     --modules "MOD-001,..."    依存モジュール
#     --force                    既存ディレクトリを上書き
#   例:
#     ai-delivery/scripts/generate-plugin.sh auth \
#       --description "認証モジュール" --author "Xtone"
#
# 方針: warn_and_document（T-002）— 未置換プレースホルダ等は警告のみ・exit 0。

set -euo pipefail

usage() {
  sed -n '2,15p' "$0" >&2
  exit 1
}

if [ "$#" -lt 1 ]; then usage; fi

USECASE="$1"
shift || true

case "$USECASE" in
  -h|--help) usage ;;
  -*) echo "❌ usecase 名が必要です（'-' で始まる引数）" >&2; usage ;;
esac

if ! printf '%s' "$USECASE" | grep -qE '^[a-z][a-z0-9-]*$'; then
  echo "❌ usecase は小文字英数とハイフンのみ: '$USECASE'" >&2
  exit 1
fi

DESCRIPTION=""
AUTHOR_NAME=""
APPLICABLE_DOMAINS=""
DEPENDENT_MODULES=""
FORCE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --description) DESCRIPTION="${2:-}"; shift 2 ;;
    --author) AUTHOR_NAME="${2:-}"; shift 2 ;;
    --domains) APPLICABLE_DOMAINS="${2:-}"; shift 2 ;;
    --modules) DEPENDENT_MODULES="${2:-}"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage ;;
    *) echo "❌ 未知のオプション: $1" >&2; usage ;;
  esac
done

# このスクリプトは ai-delivery/scripts/ 配下にある想定
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AI_DELIVERY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$AI_DELIVERY_DIR/xtone-plugin-template"
PLUGIN_NAME="xtone-${USECASE}-plugin"
PLUGIN_DIR="$AI_DELIVERY_DIR/plugins/$PLUGIN_NAME"

if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "❌ テンプレが見つかりません: $TEMPLATE_DIR" >&2
  exit 1
fi

if [ -e "$PLUGIN_DIR" ]; then
  if [ "$FORCE" -ne 1 ]; then
    echo "❌ 既存のディレクトリがあります: $PLUGIN_DIR （--force で上書き）" >&2
    exit 1
  fi
  echo "⚠️  既存ディレクトリを削除して再生成: $PLUGIN_DIR" >&2
  rm -rf "$PLUGIN_DIR"
fi

echo "🛠  Generating $PLUGIN_NAME from template ..."
mkdir -p "$(dirname "$PLUGIN_DIR")"

# 1. テンプレを丸ごとコピー。シンボリックリンクは再作成のため `-L` を使わない。
cp -R "$TEMPLATE_DIR/" "$PLUGIN_DIR/"

# テンプレ自身の説明書 README はプラグイン側には不要なので削除し、後段で最小雛形を生成。
rm -f "$PLUGIN_DIR/README.md"

# 2. schemas symlink を再作成（cp で実体化される場合があるため）。
SCHEMAS_LINK="$PLUGIN_DIR/schemas"
rm -rf "$SCHEMAS_LINK"
ln -s ../../xtone-shared-plugin/schemas/v1 "$SCHEMAS_LINK"

# 3. .template ファイルを実体化。
#    - plugin.json.template → plugin.json
#    - skills/plugin-guide/SKILL.md.template → skills/<usecase>-plugin-guide/SKILL.md
#      （ディレクトリ名も usecase で改名）
#    - skills/SKILL.md.template はフェーズ別 Skill の骨格なので .template のまま残す。
mv "$PLUGIN_DIR/.claude-plugin/plugin.json.template" "$PLUGIN_DIR/.claude-plugin/plugin.json"

GUIDE_DIR_SRC="$PLUGIN_DIR/skills/plugin-guide"
GUIDE_DIR_DST="$PLUGIN_DIR/skills/${USECASE}-plugin-guide"
mv "$GUIDE_DIR_SRC" "$GUIDE_DIR_DST"
mv "$GUIDE_DIR_DST/SKILL.md.template" "$GUIDE_DIR_DST/SKILL.md"

# 4. プレースホルダを置換（macOS / GNU sed どちらでも動くよう .bak 経由）。
replace_in_file() {
  local pattern="$1" replacement="$2" file="$3"
  # replacement 中の sed 特殊文字（デリミタ `|`、後方参照 `&`、エスケープ `\`）を
  # エスケープしないと `--description "BtoC & BtoB"` 等でマッチ文字列が挿入される。
  local safe_replacement
  safe_replacement="$(printf '%s' "$replacement" | sed -e 's/[&\\|]/\\&/g')"
  sed -i.bak "s|${pattern}|${safe_replacement}|g" "$file"
  rm -f "${file}.bak"
}

while IFS= read -r -d '' f; do
  replace_in_file '{{usecase}}' "$USECASE" "$f"
  [ -n "$DESCRIPTION" ]        && replace_in_file '{{description}}'         "$DESCRIPTION"        "$f" || true
  [ -n "$AUTHOR_NAME" ]        && replace_in_file '{{author_name}}'         "$AUTHOR_NAME"        "$f" || true
  [ -n "$APPLICABLE_DOMAINS" ] && replace_in_file '{{applicable_domains}}'  "$APPLICABLE_DOMAINS" "$f" || true
  [ -n "$DEPENDENT_MODULES" ]  && replace_in_file '{{dependent_modules}}'   "$DEPENDENT_MODULES"  "$f" || true
done < <(find "$PLUGIN_DIR" -type f \
  \( -name '*.json' -o -name '*.md' -o -name '*.yaml' -o -name '*.yml' -o -name '*.sh' -o -name '*.template' \) \
  -print0)

# 5. プラグイン用の最小 README 雛形を生成（テンプレの説明書とは別物）。
cat > "$PLUGIN_DIR/README.md" <<EOF
# $PLUGIN_NAME

Xtone AIデリバリシステムの **${USECASE}** プラグイン。マスターテンプレ \`xtone-plugin-template\`（T-019）から生成。

> 運用 context は \`skills/${USECASE}-plugin-guide/SKILL.md\` を参照（DP-27 / CONV-06: ルート CLAUDE.md は置かない）。
> プロジェクト全体のルールは \`ai-delivery/CLAUDE.md\` を参照。

## 構成

- \`agents/\` — Subagent（基盤6 ＋ ユースケース特化を追加可能）
- \`commands/\` — Slash Command（基盤8 ＋ 必要に応じて拡張）
- \`hooks/\` — hooks.json + 4 Hook（warn_and_document）
- \`skills/${USECASE}-plugin-guide/\` — 本プラグインの作業ガイド
- \`skills/<phase>/<skill>/\` — フェーズ別 Skill（テンプレは \`skills/SKILL.md.template\`）
- \`schemas/\` — \`xtone-shared-plugin/schemas/v1\` への symlink（編集不可・CONV-14）
- \`docs/\` — pending-decisions / adr 等

## はじめかた

\`\`\`bash
cp .env.example .env   # トークンを設定
ai-delivery/scripts/validate-plugin.sh .   # 品質ゲート
claude                  # Claude Code を起動し、/req-collect で開始
\`\`\`
EOF

# 6. hook を実行可能に。
find "$PLUGIN_DIR/hooks" -name '*.sh' -type f -exec chmod +x {} +

# 7. 未置換プレースホルダの検出（warn_and_document, exit 0 を維持）。
#    実体化済みファイル（*.template を除く）を対象。
REMAIN="$(grep -rln '{{' "$PLUGIN_DIR" --exclude='*.template' 2>/dev/null || true)"
if [ -n "$REMAIN" ]; then
  echo "⚠️  未置換のプレースホルダが残っています（必須項目は手動置換または再生成で対応）:" >&2
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    echo "   - $line" >&2
  done <<EOF
$REMAIN
EOF
fi

echo "✅ Plugin generated: $PLUGIN_DIR"
echo
echo "次の手順:"
echo "  1. cd $PLUGIN_DIR"
echo "  2. cp .env.example .env && トークンを設定"
echo "  3. ai-delivery/scripts/validate-plugin.sh $PLUGIN_DIR で品質ゲートを実行"
echo "  4. claude で起動し、/req-collect で要件収集を開始"
