#!/usr/bin/env bash
# SCH-18 / TPL-24 — PR マージ後に型化資産インベントリへ同期し、リリースノートを生成する。
# 注意: PR マージは Claude Code 外（リモート）イベントのため hooks.json には登録しない（判断ポイント DP 記録済み）。
#       GitHub Actions（CI）または手動・定期実行で呼び出す。
# 方針: warn_and_document（T-002）。必ず exit 0。
# 依存: git。

root="${CLAUDE_PLUGIN_ROOT:-.}"
last_merge="$(git -C "$root" log --merges -1 --pretty=format:'%H %s' 2>/dev/null || true)"

if [ -n "$last_merge" ]; then
  echo "ℹ️ [post-pr-merge] 直近のマージ: ${last_merge}"
  echo "ℹ️ 型化資産インベントリDB(T-009)へのエントリ追加とリリースノート生成を行ってください（手動/CI）。"
fi
exit 0
