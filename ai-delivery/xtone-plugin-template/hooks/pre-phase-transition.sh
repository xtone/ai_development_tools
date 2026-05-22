#!/usr/bin/env bash
# SCH-15 / TPL-21 — フェーズ移行前に未決判断ポイントを検出して警告する。
# 起動: Claude Code UserPromptSubmit。ユーザーが直接 /design /implement /test を打った時に確実に発火する。
#   ※ PreToolUse(SlashCommand) はユーザー直接タイプ時に発火しないため UserPromptSubmit を採用
#     （PR #122 レビュー Major 指摘対応 / 社内 user_prompt_command_counter.js のパターン準拠）。
# 方針: warn_and_document（T-002）。検出しても必ず exit 0（ブロックしない）。
# 依存: jq。

input="$(cat 2>/dev/null || true)"
prompt="$(printf '%s' "$input" | jq -r '.prompt // empty' 2>/dev/null || true)"

# プロンプト先頭のスラッシュコマンドを抽出（プラグイン接頭辞 /name:design にも対応）
cmd="$(printf '%s' "$prompt" | sed -n 's#^[[:space:]]*\(/[^[:space:]]*\).*#\1#p')"
case "$cmd" in
  */design|*/implement|*/test|*:design|*:implement|*:test) ;;
  *) exit 0 ;;
esac

root="${CLAUDE_PLUGIN_ROOT:-.}"
pending="$root/docs/pending-decisions.md"
count=0
if [ -f "$pending" ]; then
  count="$(grep -Eo 'DP-[0-9]+' "$pending" 2>/dev/null | sort -u | wc -l | tr -d ' ')"
fi

if [ "${count:-0}" -gt 0 ]; then
  echo "⚠️ [pre-phase-transition] 未決の判断ポイントが ${count} 件あります。" >&2
  echo "   フェーズ移行は妨げません（warn_and_document, T-002・ブロックなし）。" >&2
  echo "   /pending-list で確認し、決定できるものは /decide で記録してください。" >&2
fi
exit 0
