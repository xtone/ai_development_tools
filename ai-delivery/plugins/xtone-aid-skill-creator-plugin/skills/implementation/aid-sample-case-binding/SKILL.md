---
name: aid-sample-case-binding
description: 対象プラグインの sample-inputs/ に xtone-shared-plugin/sample-cases/ カタログ案件を symlink で取り込むスキル（B-21 / Issue #174）。pilot 入力の紐付け・plugin-architecture.json との整合・validate-plugin.sh の sample-inputs symlink 整合チェック通過までを一気通貫で行う。--legacy-only モードで B-21 以前の独自案件並存（auth プラグインの bookclub-app 等）にも対応し、sample_case_legacy フィールドで経緯を記録する（FINDING-02 / DP-AID-03）。
---

# AID Sample Case Binding Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

対象プラグインの `sample-inputs/` に、共通カタログ `xtone-shared-plugin/sample-cases/` から案件を **symlink で取り込む** 実装系スキル（B-21）。pilot 入力として案件を紐付け、`validate-plugin.sh` の **sample-inputs symlink 整合チェック（#174 / B-21）** を通すまでが本スキルの責任範囲。

> 設計方針: sample-cases カタログは AIデリバリ全体の真実の源（Single Source of Truth）。プラグイン側はカタログ案件への参照のみを持ち、案件本体は編集しない。プラグイン固有の追加メモが必要な場合は `sample-inputs/<name>.notes.md` を**並置**する（カタログ本体は触らない）。

## 入出力

- **入力:**
  - `target_plugin_path`（例: `ai-delivery/plugins/xtone-payment-plugin`。省略時は `ai-delivery/plugins/xtone-<usecase>-plugin`）
  - `sample_case_name`（カタログ内のディレクトリ名: `ec-d2c-app` / `event-campaign-lp` / `business-saas` / `media-content` / `corporate-site` / `education-voucher` / `maas-carshare` 等）
  - フラグ: `--legacy-only`（既存プラグインの後追い起稿時のみ・B-21 以前の独自案件並存の表現）
  - `target_plugin_path/delivery/plugin-architecture.json`（`sample_case_bindings` / `sample_case_legacy` を参照・更新）
- **出力:**
  - **通常モード**: `<target>/sample-inputs/<sample_case_name>` symlink（カタログ案件を指す）
  - **必要なら**: `<target>/sample-inputs/<sample_case_name>.notes.md`（プラグイン固有の追加ヒアリング項目）
  - **legacy_only モード**: symlink は作らず、`plugin-architecture.json.sample_case_legacy` にメタデータ記録
  - `delivery/sample-case-binding-log.md`（採用したカタログ案件名 / 採用理由 / 追加した notes.md / legacy 記録の有無）
  - **`plugin-architecture.json` の更新**: `sample_case_bindings` 配列への追記（通常モード）/ `sample_case_legacy` への記録（legacy_only モード）

## 動作モードの選択（重要）

| モード | 適用条件 | 動作 |
|---|---|---|
| **通常（symlink 作成）** | 新規 Rollout プラグイン / 既存プラグインで B-21 カタログ案件を取り込む | カタログから symlink 作成 + `sample_case_bindings` に追記 |
| **`--legacy-only`** | 既存プラグインの**後追い起稿**で、B-21 以前の独自案件（例: auth プラグインの `bookclub-app`）が既に置かれている | symlink を作らず `sample_case_legacy` に経緯を記録するのみ |

> **legacy_only モードは新規 Rollout プラグインでは使わない**（DP-AID-03 / FINDING-02）。新規はカタログ案件を 1〜2 件選定するのが既定。カタログに該当案件がない場合は、`xtone-shared-plugin/sample-cases/` への**新案件追加 PR を別途立てる**（カタログ更新は plugin-developer-guide §1 Step 5 の責務）。

## 通常モードの手順

1. **前提チェック**:
   - `xtone-shared-plugin/sample-cases/<sample_case_name>/` が存在するか確認
   - 存在しなければ「カタログへの新案件追加 PR が必要」とユーザに通知（DP-AID-03）。本スキルは新案件追加 PR の起票までは行わない（カタログ更新は別フロー）
   - `target_plugin_path/sample-inputs/` ディレクトリが存在するか確認（無ければ作成）
   - 既存 `sample-inputs/<sample_case_name>` が**ない**ことを確認（上書きは `--force` 明示確認）
2. **plugin-architecture.json との整合**:
   - `delivery/plugin-architecture.json.sample_case_bindings` に `<sample_case_name>` が含まれているか確認
   - 含まれていなければ「`/aid-skill-creator-design` で選定された候補にないが、追加するか？」とユーザに確認
   - 確認 OK なら `sample_case_bindings` 配列に追記（本スキルが書き込み）
3. **symlink 作成**:
   ```bash
   cd <target_plugin_path>/sample-inputs
   ln -s ../../../xtone-shared-plugin/sample-cases/<sample_case_name> <sample_case_name>
   ```
   - **リンク名はカタログ側のディレクトリ名と一致させる**（validate-plugin.sh の #174 / B-21 チェック対象）
   - 相対パス（`../../../`）で張る（プラグイン移動時の整合維持のため）
4. **プラグイン固有の追加メモが必要なら並置**:
   - `sample-inputs/<sample_case_name>.notes.md` を作成（**カタログ本体は編集しない**）
   - 内容: 当該プラグインで追加のヒアリングが必要な事項・案件固有の前提（例: 決済プラグインで `ec-d2c-app` 案件の決済プロバイダ希望、配送区分の前提など）
   - notes.md は validate-plugin.sh の symlink チェック対象外（`*.notes.md` は除外パターン）
5. **検証**:
   - `bash ai-delivery/scripts/validate-plugin.sh <target_plugin_path>` を実行
   - sample-inputs の symlink 整合チェック（#174 / B-21）に通ることを確認
   - 警告が出たら `aid-validation-runner` 経由で `pending-decisions.md` 同期
6. **記録**:
   - `delivery/sample-case-binding-log.md` に「symlink 先 / 採用理由 / 追加した notes.md」を残す
   - 採用理由は `plugin-architecture.json` 上の `sample_case_bindings[*].rationale` と整合させる

## legacy_only モードの手順

B-21（共通カタログ運用）**以前**に独自 `sample-inputs/` を持つプラグイン（例: auth プラグインの `bookclub-app.requirements-input.md`）の場合に使う。

1. **前提チェック**:
   - 対象プラグインの `sample-inputs/` に既に独自案件ファイル（`*.requirements-input.md` 等）が存在するか確認
   - 存在しなければ legacy_only モードは不要（通常モードを使うか、何もしない）
2. **`sample_case_legacy` 記録**:
   - `delivery/plugin-architecture.json` の `sample_case_legacy` フィールドに以下を記録（既存があれば上書き確認）:
     ```json
     {
       "name": "bookclub-app",
       "location": "sample-inputs/bookclub-app.requirements-input.md",
       "rationale": "B-21 以前の独自案件。経緯保存のため新規プラグインでは sample-cases/ カタログ運用に切替（DP-AID-03）"
     }
     ```
3. **symlink は作らない**:
   - カタログ案件ではないため、`sample-inputs/<name>` symlink は**作成しない**
   - 既存の独自案件ファイル（`*.requirements-input.md` 等）はそのまま残す
4. **検証**:
   - `bash ai-delivery/scripts/validate-plugin.sh <target_plugin_path>` を実行
   - 独自ファイル（`.md` 拡張子）は validate-plugin.sh で除外されるため、警告は出ない想定
5. **記録**:
   - `delivery/sample-case-binding-log.md` に「legacy_only 記録 / 対象ファイル / 経緯」を残す

## カタログ案件選定の判断軸（DP-AID-03）

`/aid-skill-creator-design`（または `aid-plugin-architecture-design`）が `sample_case_candidates` を絞り込んだあと、本スキルで紐付ける案件を最終決定する。判断軸：

| 軸 | 説明 |
|---|---|
| **適用ドメイン** | プラグインの `applicable_domains` と案件のドメインが一致するか（例: 決済プラグイン → EC/D2C / イベント LP は適合、教育バウチャーは隣接） |
| **モジュール網羅性** | 案件で使われるモジュール（MOD-XXX）が本プラグインの `module_id` を含むか |
| **判断ポイント露出度** | 本プラグインの主要 DP（例: DP-PAYMENT-001 プロバイダ選択）が案件で**問われる**か。問われない案件は pilot 入力として弱い |
| **規模感** | MVP スコープと案件規模の親和性（小さすぎる/大きすぎる案件は pilot 検証の S/N が悪化） |

> **既定: カタログから 2 件選定**（多様性確保）。1 件のみは pilot 検証としては不十分・3 件以上は本スキルでは捌かず `/aid-skill-creator-design` で絞り込み直す。

## plugin-architecture.json のスキーマ（書き込むフィールド）

`delivery/plugin-architecture.json` に書き込むフィールド：

| フィールド | 例 | モード |
|---|---|---|
| `sample_case_bindings[]` | `[{"name": "ec-d2c-app", "rationale": "EC/D2C ドメイン適合・決済プロバイダ選択 DP が露出"}]` | 通常 |
| `sample_case_legacy` | `{"name": "bookclub-app", "location": "sample-inputs/bookclub-app.requirements-input.md", "rationale": "..."}` | legacy_only |

> 本スキルは `plugin-architecture.json` の**この 2 フィールドのみ**を書き換える。他フィールド（skills / dp_candidates 等）には触らない（責任分界の遵守）。

## 既知の制約・落とし穴

- **絶対パス symlink は使わない**: `ln -s /home/...` のような絶対パスで張ると、リポジトリ移動・他環境で壊れる。**必ず相対パス**（`../../../xtone-shared-plugin/sample-cases/<name>`）で張る。
- **リンク名の不一致**: `sample-inputs/<sample_case_name>` の `<sample_case_name>` がカタログ側のディレクトリ名と**ずれる**と、validate-plugin.sh の #174 チェックは通っても運用上の参照が壊れる（plugin-architecture.json 側の `bindings[].name` とも乖離）。リンク名は**カタログ側と必ず一致**させる。
- **`notes.md` でカタログ本体を上書きしようとする事故**: プラグイン固有メモは**並置**（`<name>.notes.md`）であり、`<name>/` ディレクトリ内に書き戻してはいけない。本スキルは出力前に対象パスがカタログ実体内に侵入していないか確認する。
- **legacy_only モードを新規プラグインで誤用**: 新規 Rollout プラグインで `--legacy-only` を使うと、本来カタログから引くべき案件をスキップしてしまう。**legacy_only は既存プラグインの後追い起稿のみ**（DP-AID-03 / FINDING-02）。
- **カタログに該当案件がない場合の処理**: 「該当ゼロ → 仕方なく既存案件を選ぶ」はアンチパターン。本スキルは「カタログへの新案件追加 PR が必要」とユーザに通知して停止し、新案件追加 PR の完了後に再実行する運用を促す。
- **`sample_case_bindings` の二重起票**: 同一案件を 2 回紐付ける誤操作で、配列に重複が入る可能性がある。本スキルは追記前に既存配列を grep して重複チェックする。
- **symlink を作ったのに `plugin-architecture.json` 更新を忘れる**: validate-plugin.sh の #174 は通るが、後段スキル（`/aid-validation-runner` 等）が `sample_case_bindings` を見たとき不整合に気付かない。**symlink 作成と JSON 更新を同手順で必ずペア実行**。

## 判断ポイント（人間判断をスルーさせない）

- **DP-AID-03**（sample-case の選定）: カタログから選ぶ vs 新案件追加 PR。既定は「カタログから 2 件選定。該当ゼロなら新案件 PR」。AI は推奨だけ提示し、最終選定はユーザ判断。
- **legacy_only モードの適用判定**: B-21 以前の既存独自案件があるかは、`sample-inputs/` の中身を見て判断。既存ファイルが `.requirements-input.md` 形式で、`sample_case_legacy` がまだ未記録の場合のみ legacy_only 適用を提案。
- **notes.md の必要性**: 案件にプラグイン固有の追加ヒアリングが必要かはユーザ判断。本スキルは「カタログ案件に書かれていない前提が必要か？」を質問し、必要なら notes.md 雛形を提示。
- **`sample_case_bindings` 候補外の案件を取り込むか**: `plugin-architecture.json.sample_case_bindings` に未掲載の案件をユーザが指定した場合、「設計時に絞り込まれた候補にないが追加するか？」を必ず確認（勝手に追加しない）。

未決は `delivery/sample-case-binding-log.md` に明示し、`docs/pending-decisions.md` に追記する（T-002 warn_and_document）。

## 検証カテゴリとの対応（validate-plugin.sh）

本スキルが直接関わるのは validate-plugin.sh の **カテゴリ 8（sample-inputs symlink）**：

| チェック | 失敗時の症状 | 本スキルでの対処 |
|---|---|---|
| symlink が壊れている | `⚠️ sample-inputs の symlink が壊れています: ...` | カタログ側のディレクトリ実在を確認・相対パス見直し |
| symlink 先がカタログ外 | `⚠️ sample-inputs の symlink 先がカタログ外です: ...` | 通常モードで張り直すか、許容する場合は `pending-decisions.md` に記録（DP-AID-03 例外起票） |
| symlink ではない通常ファイル（`*.md` / `*.notes.md` 以外） | warn なし（除外パターン外なら警告対象） | notes.md は `.notes.md` 拡張子を厳守 |

> カテゴリ 8 以外の警告（plugin.json 必須欠落・schemas symlink 等）が出た場合は **本スキルの責任範囲外**。`aid-validation-runner` に渡す。

## メタゆえの留意点

- **本スキルは sample-cases カタログを編集しない**。カタログへの新案件追加は plugin-developer-guide §1 Step 5 の責務（別フロー・PR ベース）。
- **`<name>.notes.md` の運用**: プラグイン固有の追加メモは並置で、案件本体は不変。これにより**同一案件を複数プラグインから参照しても干渉が起きない**（CONV-14 の SSoT 原則と整合）。
- **本プラグイン自身に対する適用**: メタプラグイン（`xtone-aid-skill-creator-plugin`）は通常の意味での「案件」がないため、本スキルの主対象は Rollout プラグイン（T-023〜T-045）。本プラグインへの適用は legacy_only でもなく、`sample_case_bindings: []` のままで問題ない。
- **既存 auth プラグインの bookclub-app は legacy_only の正典**: FINDING-02 / `dogfood/auth/plugin-architecture.json` で `sample_case_legacy` フィールドが既に確立されている。新規 Rollout で類似の独自案件が必要になることは原則ない（あるなら DP-AID-03 の例外として `pending-decisions.md` に明示）。

## 参考

- `xtone-shared-plugin/sample-cases/` — 共通カタログ（B-21 / Issue #174）
- `plugins/xtone-auth-plugin/sample-inputs/bookclub-app.requirements-input.md` — legacy 並存の唯一の正典
- `scripts/validate-plugin.sh` — sample-inputs symlink チェック（カテゴリ 8）
- `docs/plugin-developer-guide.md` §1 Step 5 — カタログへの新案件追加 PR の起票責務
- 本プラグインの `delivery/dogfood/auth/plugin-architecture.json` — `sample_case_legacy` の参考形
