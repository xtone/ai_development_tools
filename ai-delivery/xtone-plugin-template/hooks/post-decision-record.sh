#!/usr/bin/env bash
# SCH-16 / TPL-22 — /decide 後に ADR の存在を検証し、トレーサビリティを促す。
# 起動: Claude Code PostToolUse(matcher: SlashCommand)。/decide のみ処理。
# 方針: warn_and_document（T-002）。必ず exit 0（ブロックしない）。
# 依存: jq。

input="$(cat 2>/dev/null || true)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"

case "$cmd" in
  *"/decide"*) ;;
  *) exit 0 ;;
esac

root="${CLAUDE_PLUGIN_ROOT:-.}"
adr_count="$(find "$root/docs/adr" -name 'ADR-*.md' 2>/dev/null | wc -l | tr -d ' ' || echo 0)"

if [ "${adr_count:-0}" -eq 0 ]; then
  echo "⚠️ [post-decision-record] /decide 後に ADR ファイル(docs/adr/ADR-NNN.md)が見つかりません。" >&2
  echo "   decision_record の decided_by/decided_at/rationale トリオと ADR を確認してください（warn_and_document, T-002）。" >&2
fi
exit 0
