---
description: 対象プラグインの sample-inputs/ に xtone-shared-plugin/sample-cases/ カタログ案件を symlink で取り込む（B-21 / Issue #174）。aid-sample-case-binding スキルを起動し、plugin-architecture.json との整合・symlink 作成・notes.md 並置・validate-plugin.sh の sample-inputs symlink 整合チェック通過までを行う。--legacy-only で B-21 以前の独自案件並存（auth プラグインの bookclub-app 等）にも対応。
argument-hint: <usecase> <sample_case_name> [target_plugin_path] | <usecase> --legacy-only
---

`aid-sample-case-binding` スキル（`skills/implementation/aid-sample-case-binding/SKILL.md`）に従って、対象プラグインに pilot 入力案件を紐付けてください。

引数: $ARGUMENTS （形式: `<usecase> <sample_case_name> [target_plugin_path]` または `<usecase> --legacy-only`）

- `<usecase>`: プラグインのユースケース（例: `payment`）
- `<sample_case_name>`: カタログ内のディレクトリ名（例: `ec-d2c-app` / `event-campaign-lp` / `business-saas` / `media-content` / `corporate-site` / `education-voucher` / `maas-carshare`）
- `<target_plugin_path>`: 省略時は `ai-delivery/plugins/xtone-<usecase>-plugin`
- `--legacy-only`: B-21 以前の独自案件並存モード（**既存プラグインの後追い起稿のみ**・新規 Rollout プラグインでは使わない）

## 通常モード（symlink 作成）

1. **前提チェック**:
   - `xtone-shared-plugin/sample-cases/<sample_case_name>/` の存在確認（無ければ「カタログへの新案件追加 PR が必要」と通知して停止・DP-AID-03）
   - `target_plugin_path/sample-inputs/` ディレクトリ存在確認（無ければ作成）
   - 既存 `sample-inputs/<sample_case_name>` が**ない**ことを確認（上書きは `--force` 明示確認）
2. **plugin-architecture.json との整合**:
   - `delivery/plugin-architecture.json.sample_case_bindings` に `<sample_case_name>` が含まれているか確認
   - 含まれていなければ「設計時の候補にないが追加するか？」とユーザに確認 → OK なら配列に追記
3. **symlink 作成**（**相対パス必須**・リンク名はカタログ側と一致）:
   ```bash
   cd <target_plugin_path>/sample-inputs
   ln -s ../../../xtone-shared-plugin/sample-cases/<sample_case_name> <sample_case_name>
   ```
4. **プラグイン固有の追加メモが必要なら並置**:
   - `sample-inputs/<sample_case_name>.notes.md` を作成（**カタログ本体は編集しない**）
   - 内容: 当該プラグインで追加のヒアリングが必要な事項・案件固有の前提
5. **検証**:
   - `bash ai-delivery/scripts/validate-plugin.sh <target_plugin_path>` を実行
   - sample-inputs symlink 整合チェック（カテゴリ 8 / #174 / B-21）に通ることを確認
6. **記録**:
   - `delivery/sample-case-binding-log.md` に「symlink 先 / 採用理由 / 追加した notes.md」を残す

## legacy_only モード（既存プラグインの後追い起稿のみ）

B-21 以前に独自 `sample-inputs/` を持つプラグイン（例: auth プラグインの `bookclub-app`）の場合：

1. **前提チェック**: 対象プラグインの `sample-inputs/` に既存独自案件ファイル（`*.requirements-input.md` 等）の存在確認
2. **`sample_case_legacy` 記録**: `delivery/plugin-architecture.json.sample_case_legacy` に以下を記録（既存があれば上書き確認）:
   ```json
   {
     "name": "<bookclub-app 等>",
     "location": "sample-inputs/<file-path>",
     "rationale": "B-21 以前の独自案件・経緯保存（DP-AID-03）"
   }
   ```
3. **symlink は作らない**（カタログ案件ではないため）
4. **検証**: `validate-plugin.sh` を実行（独自ファイルは除外パターンで警告対象外）
5. **記録**: `delivery/sample-case-binding-log.md` に「legacy_only 記録 / 対象ファイル / 経緯」を残す

> 該当する案件がカタログにない場合は、`xtone-shared-plugin/sample-cases/` への新案件追加 PR を別途立てる（カタログ更新は plugin-developer-guide §1 Step 5 の責務・本コマンドは扱わない）。
> 既存 `bookclub-app`（auth プラグイン）の扱いは plugin-developer-guide.md の通り並存（FINDING-02 / sample_case_legacy）。
> ブロックしない（warn_and_document, T-002）。
