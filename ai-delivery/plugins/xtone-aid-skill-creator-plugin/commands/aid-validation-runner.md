---
description: validate-plugin.sh を実行し、警告を解析して docs/pending-decisions.md に整形追記する。aid-validation-runner スキルを起動し、8 カテゴリ分類・重大度判定（Block-worthy / Should-fix / Info-only）・修正候補の提示まで行う。
argument-hint: [target_plugin_path] [--strict] [--no-schema]
---

`aid-validation-runner` スキル（`skills/implementation/aid-validation-runner/SKILL.md`）に従って、対象プラグインの品質ゲートを実行してください。

引数: $ARGUMENTS （形式: `[target_plugin_path] [--strict] [--no-schema]`）

- `<target_plugin_path>`: 省略時は直前の `/aid-scaffold` で生成したプラグイン or 本プラグイン自身
- `--strict`: CI 用（1 件でも警告で exit 1）— **ローカル日常検証では既定で使わない**（warn_and_document）
- `--no-schema`: スキーマ検証スキップ（scaffold 直後の素状態で「ℹ️ 成果物未発見」を抑止したいときに使う）

1. **対象決定**: 引数指定 → 直前 `/aid-scaffold` 対象 → 本プラグイン自身 の順で既定。
2. **フラグ決定**: 用途に応じて選択（ローカル既定はフラグなし）。
3. **実行**:
   ```bash
   bash ai-delivery/scripts/validate-plugin.sh <target_plugin_path> [--strict] [--no-schema]
   ```
   stdout / stderr を `delivery/validation-report.md` に記録（タイムスタンプ付）。
4. **警告解析**:
   - `⚠️` 行を抽出
   - 8 カテゴリ（1: plugin.json / 2-2c: symlink / 3: SKILL.md frontmatter / 4: hooks / 5: .mcp.json.sample / 6: 未置換 / 7: スキーマ / 8: sample-inputs symlink）で集計
   - 重大度判定（Block-worthy / Should-fix / Info-only）
5. **pending-decisions.md 同期**:
   - **対象プラグインの** `docs/pending-decisions.md`（本プラグインの pending-decisions.md ではない）に Block-worthy / Should-fix を `AID-VAL-NNN` 仮 ID で追記
   - 既存 ID と重複しないよう連番採番
6. **修正候補提示**:
   - カテゴリ別「よくある原因と修正」をリスト化
   - 機械的修正（`chmod +x` 等）も**ユーザ確認を取ってから実行**（AI が勝手に修正しない）
7. **次アクション**: 警告ゼロなら `✅ Validation passed`、警告ありなら「上位 N 件を表示 → 修正 → 再実行」のループ。

> `--strict` を CI 以外で付ける場合は `decision_record` に理由を残す（warn_and_document の例外）。
> 自動修正は AI 主導で行わない。
