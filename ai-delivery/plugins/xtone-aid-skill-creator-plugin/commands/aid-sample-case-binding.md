---
description: 対象プラグインの sample-inputs/ に xtone-shared-plugin/sample-cases/ からの symlink を張る（B-21）。pilot 入力として案件を紐付け、validate-plugin.sh の sample-inputs symlink 整合チェック（#174）を通すための運用手順。
argument-hint: <usecase> <sample_case_name> [target_plugin_path]
---

対象プラグインの `sample-inputs/` に共通カタログ `xtone-shared-plugin/sample-cases/` から案件を symlink で取り込んでください（B-21）。

引数: $ARGUMENTS （形式: `<usecase> <sample_case_name> [target_plugin_path]`）

- `<usecase>`: プラグインのユースケース（例: `payment`）
- `<sample_case_name>`: カタログ内のディレクトリ名（例: `ec-d2c-app` / `event-campaign-lp` / `business-saas` / `media-content` / `corporate-site` / `education-voucher` / `maas-carshare`）
- `<target_plugin_path>`: 省略時は `ai-delivery/plugins/xtone-<usecase>-plugin`

> **本コマンドは現状 Skill 未実装**（後段で `aid-sample-case-binding` Skill 化予定・本プラグインのバックログ）。当面は以下の手順を直接実行する。

### legacy_only モード（既存プラグインの後追い起稿時のみ）

B-21（共通カタログ運用）**以前**に独自 `sample-inputs/` を持つプラグイン（例: auth プラグインの `bookclub-app`）の場合は、**symlink は作らず** plugin-architecture.json の `sample_case_legacy` に経緯を記録するに留める：

- 引数: `<usecase> --legacy-only`
- 動作: symlink を作らず、`delivery/sample-case-binding-log.md` に「`sample_case_legacy = { name: <bookclub-app 等>, location: <path>, rationale: B-21 以前の独自案件・経緯保存 }`」を記録
- 適用条件: **既存プラグインの後追い起稿のみ**（新規 Rollout プラグインでは使わない）
- 由来: FINDING-02 / ADR は不要（運用ルールとして decision-points.md DP-AID-03 に記載）

1. **前提チェック**:
   - `xtone-shared-plugin/sample-cases/<sample_case_name>/` が存在するか確認
   - 存在しなければ「`sample-cases/` への新案件追加 PR が必要」とユーザに通知（DP-AID-03）
   - 対象プラグインの `sample-inputs/` ディレクトリが存在するか確認（無ければ作成）
   - 既存 `sample-inputs/<sample_case_name>` が**ない**ことを確認（上書きは明示確認）
2. **plugin-architecture.json との整合**:
   - `delivery/plugin-architecture.json.sample_case_bindings` に `<sample_case_name>` が含まれているか確認
   - 含まれていなければ「`/aid-skill-creator-design` で選定された候補にないが、追加するか？」とユーザに質問
3. **symlink 作成**:
   ```bash
   cd <target_plugin_path>/sample-inputs
   ln -s ../../../xtone-shared-plugin/sample-cases/<sample_case_name> <sample_case_name>
   ```
   - リンク名はカタログ側のディレクトリ名と**一致させる**（validate-plugin.sh の #174 / B-21 チェック対象）
4. **プラグイン固有の追加メモが必要なら並置**:
   - `sample-inputs/<sample_case_name>.notes.md` を作成（カタログ本体は編集しない）
   - 内容: 当該プラグインで追加のヒアリングが必要な事項・案件固有の前提
5. **検証**:
   - `bash ai-delivery/scripts/validate-plugin.sh <target_plugin_path>` を実行
   - sample-inputs の symlink 整合チェック（#174 / B-21）に通ることを確認
6. **記録**:
   - `delivery/sample-case-binding-log.md` に「symlink 先 / 採用理由 / 追加した notes.md」を残す

> 該当する案件がカタログにない場合は、`xtone-shared-plugin/sample-cases/` への新案件追加 PR を別途立てる（カタログ更新は plugin-developer-guide §1 Step 5 の責務）。
> 既存 `bookclub-app`（auth プラグイン）の扱いは plugin-developer-guide.md の通り並存。
> ブロックしない（warn_and_document, T-002）。
