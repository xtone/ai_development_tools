#!/usr/bin/env bash
# SCH-15 / TPL-21 — フェーズ移行前に未決判断ポイントを検出して警告する。
# 起動: Claude Code PreToolUse(matcher: SlashCommand)。フェーズ移行系コマンド(/design /implement /test)のみ処理。
# 方針: warn_and_document（T-002）。検出しても必ず exit 0（ブロックしない）。
# 依存: jq（Hook 言語は Bash + jq に決定）。

input="$(cat 2>/dev/null || true)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"

# フェーズ移行系コマンドのみ対象。それ以外は何もしない。
case "$cmd" in
  *"/design"*|*"/implement"*|*"/test"*) ;;
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
