#!/usr/bin/env bash
# 新規プラグイン（xtone-plugin-template から複製したもの）に対して、
# xtone-shared-plugin への symlink を正しい相対パスで再作成する。
#
# 用途:
#   - xtone-plugin-template を `cp -r` で複製すると、symlink がコピーで
#     実体化したり、相対パスの階層が変わってリンク切れになる場合がある。
#     本スクリプトは「複製直後の整地」と「将来 generate-plugin.sh (B-07)
#     で内部呼び出しする symlink 整備ロジック」の単独実装。
#
# 対象 symlink (CONV-14 / B-17):
#   - schemas                            → xtone-shared-plugin/schemas/v1
#   - skills/implementation/tech-version-check
#                                        → xtone-shared-plugin/skills/implementation/tech-version-check
#
# 使い方:
#   ai-delivery/scripts/regenerate-symlinks.sh ai-delivery/plugins/xtone-<usecase>-plugin
#
# 終了コード:
#   0: 成功
#   1: 引数不正・対象ディレクトリ不在

set -euo pipefail

PLUGIN_DIR="${1:-}"

if [ -z "$PLUGIN_DIR" ]; then
  echo "usage: $0 <plugin-dir>" >&2
  echo "  example: $0 ai-delivery/plugins/xtone-auth-plugin" >&2
  exit 1
fi

if [ ! -d "$PLUGIN_DIR" ]; then
  echo "Error: directory not found: $PLUGIN_DIR" >&2
  exit 1
fi

# schemas (CONV-14)
rm -rf "$PLUGIN_DIR/schemas"
ln -s ../../xtone-shared-plugin/schemas/v1 "$PLUGIN_DIR/schemas"
echo "✓ $PLUGIN_DIR/schemas -> ../../xtone-shared-plugin/schemas/v1"

# skills/implementation/tech-version-check (B-17)
mkdir -p "$PLUGIN_DIR/skills/implementation"
rm -rf "$PLUGIN_DIR/skills/implementation/tech-version-check"
ln -s ../../../../xtone-shared-plugin/skills/implementation/tech-version-check \
      "$PLUGIN_DIR/skills/implementation/tech-version-check"
echo "✓ $PLUGIN_DIR/skills/implementation/tech-version-check -> ../../../../xtone-shared-plugin/skills/implementation/tech-version-check"

echo ""
echo "Done. Verify with:"
echo "  ls -la $PLUGIN_DIR/schemas $PLUGIN_DIR/skills/implementation/tech-version-check"
