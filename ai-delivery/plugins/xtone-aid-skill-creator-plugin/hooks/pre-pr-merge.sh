#!/usr/bin/env bash
# SCH-17 / TPL-23 — git push 検出時に AI レビューを促す。
# 起動: Claude Code PreToolUse(matcher: Bash)。git push を含むコマンドのみ処理。
# 方針: warn_and_document（T-002）。必ず exit 0（ブロックしない）。
# 依存: jq。

input="$(cat 2>/dev/null || true)"
bash_cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"

case "$bash_cmd" in
  *"git push"*) ;;
  *) exit 0 ;;
esac

echo "⚠️ [pre-pr-merge] PR 作成/更新の前に /skip-review（reviewer Subagent）で品質ゲート(R-011〜R-013, R-018)の確認を推奨します。" >&2
echo "   未決は PR description に明示してください（warn_and_document, T-002・ブロックなし）。" >&2
exit 0
