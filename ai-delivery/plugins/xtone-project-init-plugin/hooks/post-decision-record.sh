#!/usr/bin/env bash
# SCH-16 / TPL-22 — 判断記録（ADR 生成）後にトレーサビリティを促す。
# 起動: Claude Code PostToolUse(matcher: Write|Edit)。docs/adr/ADR-*.md への書き込みのみ処理。
#   ※ /decide の直接タイプは PostToolUse(SlashCommand) で捕捉できないため、ADR 生成（Write/Edit）を検出する方式に変更
#     （PR #122 レビュー Major 指摘対応）。
# 方針: warn_and_document（T-002）。必ず exit 0（ブロックしない）。
# 依存: jq。

input="$(cat 2>/dev/null || true)"
fp="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"

case "$fp" in
  *docs/adr/ADR-*.md) ;;
  *) exit 0 ;;
esac

echo "ℹ️ [post-decision-record] ADR を記録しました: ${fp}" >&2
echo "   decision_record の decided_by / decided_at / rationale トリオが揃っているか確認してください（warn_and_document, T-002）。" >&2
exit 0
