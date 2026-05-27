#!/usr/bin/env bash
# TPL-27 — プラグインの品質ゲート＋デリバリ成果物のスキーマ検証。
# Usage:
#   ai-delivery/scripts/validate-plugin.sh [<plugin-dir>] [options]
#     --strict           1件でも警告があれば exit 1 で終了する（CI 用）
#     --no-schema        スキーマ検証を行わない（構造チェックのみ）
#     --deliverable-dir  デリバリ成果物の探索先（既定: <plugin-dir>/sample-outputs と <plugin-dir>/delivery）
#   例:
#     ai-delivery/scripts/validate-plugin.sh ai-delivery/plugins/xtone-auth-plugin
#
# 方針: warn_and_document（T-002）。既定では警告を出しても **exit 0**（ブロックしない）。
#       CI で「警告ゼロ」を強制したい時のみ --strict を付ける。
# 検証項目:
#   1. .claude-plugin/plugin.json の必須フィールド（CONV-01）
#   2. schemas/ が symlink で xtone-shared-plugin を指している（CONV-14）
#   2b. skills/implementation/tech-version-check/ が symlink で xtone-shared-plugin を指している（B-17）
#   2c. skills/implementation/implementation-skill-planner/ が symlink で xtone-shared-plugin を指している（B-18）
#   3. skills/<usecase>-plugin-guide/SKILL.md と他 skills/**/SKILL.md の frontmatter（SKL-20）
#      ※ プラグインルートの CLAUDE.md は CONV-06 改訂（B-05 / DP-27）で不要
#   4. hooks/hooks.json + hooks/*.sh の実行権限
#   5. .mcp.json.sample のトークン参照（MCP-08）
#   6. プレースホルダ {{...}} の未置換チェック
#   7. デリバリ成果物（sample-outputs/ / delivery/ 配下）の JSON Schema 検証（B-01/B-13 対応）

set -uo pipefail

PLUGIN_DIR=""
STRICT=0
SCHEMA_CHECK=1
DELIVERABLE_DIRS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --strict) STRICT=1; shift ;;
    --no-schema) SCHEMA_CHECK=0; shift ;;
    --deliverable-dir) DELIVERABLE_DIRS+=("${2:-}"); shift 2 ;;
    -h|--help) sed -n '2,20p' "$0" >&2; exit 0 ;;
    --) shift; break ;;
    -*) echo "❌ 未知のオプション: $1" >&2; exit 2 ;;
    *)
      if [ -z "$PLUGIN_DIR" ]; then
        PLUGIN_DIR="$1"
      else
        echo "❌ 位置引数は1つだけです" >&2; exit 2
      fi
      shift ;;
  esac
done

PLUGIN_DIR="${PLUGIN_DIR:-.}"

if [ ! -d "$PLUGIN_DIR" ]; then
  echo "❌ プラグインディレクトリが見つかりません: $PLUGIN_DIR" >&2
  exit 2
fi

PLUGIN_DIR="$(cd "$PLUGIN_DIR" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

WARN=0
warn() {
  echo "⚠️  $*" >&2
  WARN=$((WARN + 1))
}

echo "🔍 Validating $PLUGIN_DIR"

# --- 1. plugin.json の必須フィールド (CONV-01) ------------------------------
PLUGIN_JSON="$PLUGIN_DIR/.claude-plugin/plugin.json"
if [ ! -f "$PLUGIN_JSON" ]; then
  warn ".claude-plugin/plugin.json がありません（CONV-01）"
elif ! command -v jq >/dev/null 2>&1; then
  warn "jq が見つからず plugin.json の検証をスキップ"
else
  for field in name version description; do
    if ! jq -e --arg f "$field" 'has($f)' "$PLUGIN_JSON" >/dev/null; then
      warn "plugin.json: $field がありません（CONV-01）"
    fi
  done
  if jq -e 'has("author")' "$PLUGIN_JSON" >/dev/null; then
    if ! jq -e '.author.name? // empty' "$PLUGIN_JSON" >/dev/null; then
      warn "plugin.json: author.name がありません（CONV-01）"
    fi
  else
    warn "plugin.json: author がありません（CONV-01）"
  fi
  # name は xtone-*-plugin 形式（CONV-01 命名規約）
  name="$(jq -r '.name // ""' "$PLUGIN_JSON")"
  if ! printf '%s' "$name" | grep -qE '^xtone-[a-z0-9-]+-plugin$'; then
    warn "plugin.json: name '$name' は xtone-<usecase>-plugin 形式にしてください（CONV-01）"
  fi
fi

# --- 2. schemas/ が symlink (CONV-14) ---------------------------------------
SCHEMAS_PATH="$PLUGIN_DIR/schemas"
if [ ! -e "$SCHEMAS_PATH" ]; then
  warn "schemas/ がありません（CONV-14: xtone-shared-plugin/schemas/v1 への symlink を作成）"
elif [ ! -L "$SCHEMAS_PATH" ]; then
  warn "schemas/ が symlink ではありません（CONV-14: スキーマは Single Source of Truth）"
else
  target="$(readlink "$SCHEMAS_PATH")"
  case "$target" in
    *xtone-shared-plugin/schemas/v1*) ;;
    *) warn "schemas/ の symlink 先が不正です: $target（CONV-14）" ;;
  esac
fi

# --- 2b. 横断スキル tech-version-check が symlink (CONV-14 / B-17) -----------
TECH_VERSION_PATH="$PLUGIN_DIR/skills/implementation/tech-version-check"
if [ ! -e "$TECH_VERSION_PATH" ]; then
  warn "skills/implementation/tech-version-check がありません（B-17: xtone-shared-plugin への symlink を作成）"
elif [ ! -L "$TECH_VERSION_PATH" ]; then
  warn "skills/implementation/tech-version-check が symlink ではありません（CONV-14: 横断スキルは Single Source of Truth）"
else
  target="$(readlink "$TECH_VERSION_PATH")"
  case "$target" in
    *xtone-shared-plugin/skills/implementation/tech-version-check*) ;;
    *) warn "skills/implementation/tech-version-check の symlink 先が不正です: $target（CONV-14 / B-17）" ;;
  esac
fi

# --- 2c. 横断スキル implementation-skill-planner が symlink (CONV-14 / B-18) -
SKILL_PLANNER_PATH="$PLUGIN_DIR/skills/implementation/implementation-skill-planner"
if [ ! -e "$SKILL_PLANNER_PATH" ]; then
  warn "skills/implementation/implementation-skill-planner がありません（B-18: xtone-shared-plugin への symlink を作成）"
elif [ ! -L "$SKILL_PLANNER_PATH" ]; then
  warn "skills/implementation/implementation-skill-planner が symlink ではありません（CONV-14: 横断スキルは Single Source of Truth）"
else
  target="$(readlink "$SKILL_PLANNER_PATH")"
  case "$target" in
    *xtone-shared-plugin/skills/implementation/implementation-skill-planner*) ;;
    *) warn "skills/implementation/implementation-skill-planner の symlink 先が不正です: $target（CONV-14 / B-18）" ;;
  esac
fi

# --- 3. SKILL.md frontmatter (SKL-20) ---------------------------------------
SKILLS_DIR="$PLUGIN_DIR/skills"
if [ ! -d "$SKILLS_DIR" ]; then
  warn "skills/ がありません"
else
  # plugin-guide skill の存在（CONV-06 / DP-27: ルート CLAUDE.md ではなく skill に集約）
  guide_count=$(find "$SKILLS_DIR" -maxdepth 2 -type f -name 'SKILL.md' -path '*-plugin-guide/SKILL.md' 2>/dev/null | wc -l | tr -d ' ')
  if [ "${guide_count:-0}" -eq 0 ]; then
    warn "skills/<usecase>-plugin-guide/SKILL.md がありません（CONV-06 / DP-27）"
  fi
  while IFS= read -r -d '' skill; do
    rel="${skill#$PLUGIN_DIR/}"
    # 先頭の YAML frontmatter を抽出してフィールドを検証
    if ! head -1 "$skill" | grep -q '^---$'; then
      warn "$rel: frontmatter (---) で始まっていません（SKL-20）"
      continue
    fi
    fm="$(awk 'NR==1 && /^---$/ {f=1; next} f && /^---$/ {exit} f' "$skill")"
    for field in name description; do
      if ! printf '%s\n' "$fm" | grep -qE "^${field}:[[:space:]]"; then
        warn "$rel: frontmatter に $field がありません（SKL-20）"
      fi
    done
  done < <(find "$SKILLS_DIR" -type f -name 'SKILL.md' -print0)
fi

# --- 4. hooks ---------------------------------------------------------------
HOOKS_DIR="$PLUGIN_DIR/hooks"
if [ -d "$HOOKS_DIR" ]; then
  if [ ! -f "$HOOKS_DIR/hooks.json" ]; then
    warn "hooks/hooks.json がありません"
  fi
  while IFS= read -r -d '' hook; do
    if [ ! -x "$hook" ]; then
      warn "hook が実行可能ではありません: ${hook#$PLUGIN_DIR/}（chmod +x で付与）"
    fi
  done < <(find "$HOOKS_DIR" -type f -name '*.sh' -print0)
fi

# --- 5. .mcp.json.sample の認証トークン参照 (MCP-08) ------------------------
MCP_SAMPLE="$PLUGIN_DIR/.mcp.json.sample"
if [ -f "$MCP_SAMPLE" ]; then
  for token in FIGMA_TOKEN GITHUB_TOKEN NOTION_TOKEN; do
    if ! grep -q "\${${token}}" "$MCP_SAMPLE"; then
      warn ".mcp.json.sample: \${${token}} 参照がありません（MCP-08）"
    fi
  done
fi

# --- 6. 未置換プレースホルダ -----------------------------------------------
# .template ファイルは除外（生成元として残してよい）
REMAIN="$(grep -rln '{{' "$PLUGIN_DIR" --exclude='*.template' 2>/dev/null \
  | grep -v -E '(/\.git/|/node_modules/|/schemas/v1/)' || true)"
if [ -n "$REMAIN" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    warn "未置換プレースホルダ '{{...}}': ${line#$PLUGIN_DIR/}"
  done <<EOF
$REMAIN
EOF
fi

# --- 7. デリバリ成果物のスキーマ検証 ---------------------------------------
if [ "$SCHEMA_CHECK" -eq 1 ]; then
  SCHEMA_ROOT="$PLUGIN_DIR/schemas"
  if [ ! -e "$SCHEMA_ROOT" ]; then
    warn "schemas/ がないためデリバリ成果物のスキーマ検証をスキップ"
  elif ! command -v python3 >/dev/null 2>&1; then
    warn "python3 が見つからずスキーマ検証をスキップ"
  else
    if [ "${#DELIVERABLE_DIRS[@]}" -eq 0 ]; then
      DELIVERABLE_DIRS=("$PLUGIN_DIR/sample-outputs" "$PLUGIN_DIR/delivery")
    fi

    declare_schema_for() {
      # ファイル名から対応スキーマ名を推定する。
      local file="$1" base
      base="$(basename "$file")"
      case "$base" in
        requirements*.json|requirements*.yaml|requirements*.yml)
          echo "requirements.schema.json"; return 0 ;;
        design*.json|design*.yaml|design*.yml)
          echo "design.schema.json"; return 0 ;;
        implementation-plan*.json|implementation-plan*.yaml|implementation-plan*.yml)
          echo "implementation-plan.schema.json"; return 0 ;;
        modules*.json) echo "modules.schema.json"; return 0 ;;
        module*.json)  echo "module.schema.json"; return 0 ;;
        risks*.json)   echo "risks.schema.json"; return 0 ;;
        decision-point*.json|decision-points*.json)
          echo "decision-point.schema.json"; return 0 ;;
        *) return 1 ;;
      esac
    }

    found_any=0
    for dir in "${DELIVERABLE_DIRS[@]}"; do
      [ -d "$dir" ] || continue
      while IFS= read -r -d '' file; do
        schema_name="$(declare_schema_for "$file" || true)"
        if [ -z "$schema_name" ]; then
          continue
        fi
        schema_path="$SCHEMA_ROOT/$schema_name"
        if [ ! -f "$schema_path" ]; then
          warn "スキーマが見つかりません: $schema_name（対象: ${file#$PLUGIN_DIR/}）"
          continue
        fi
        found_any=1
        label="${file#$PLUGIN_DIR/}"
        rc=0
        python3 "$SCRIPT_DIR/lib/validate_schema.py" "$schema_path" "$file" --label "$label" || rc=$?
        # validate_schema.py: 0=OK, 1=スキーマ違反, 2=依存欠如（warn にカウントしない）
        if [ "$rc" -eq 1 ]; then
          WARN=$((WARN + 1))
        fi
      done < <(find "$dir" -maxdepth 2 -type f \
        \( -name '*.json' -o -name '*.yaml' -o -name '*.yml' \) -print0)
    done

    if [ "$found_any" -eq 0 ]; then
      echo "ℹ️  デリバリ成果物（requirements/design/implementation-plan 等）が見つかりませんでした"
    fi
  fi
fi

# --- 結果出力 ---------------------------------------------------------------
if [ "$WARN" -gt 0 ]; then
  echo "⚠️  $WARN 件の警告がありました。docs/pending-decisions.md に記録するか修正してください（warn_and_document, T-002）" >&2
  if [ "$STRICT" -eq 1 ]; then
    exit 1
  fi
  exit 0
fi

echo "✅ Validation passed"
exit 0
