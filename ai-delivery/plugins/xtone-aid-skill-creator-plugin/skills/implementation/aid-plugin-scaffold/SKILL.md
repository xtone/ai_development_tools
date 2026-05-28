---
name: aid-plugin-scaffold
description: ai-delivery/scripts/generate-plugin.sh を安全にラップして新規 AIデリバリプラグインの骨格を生成するスキル。プラグインの実装フェーズで delivery/plugin-architecture.json から CLI 引数を組み立て、対話的に確認したうえで実行する。生成後の post-checks（symlink 整合・未置換警告・validate-plugin.sh 起動）まで一気通貫で行う。
---

# AID Plugin Scaffold Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`ai-delivery/scripts/generate-plugin.sh`（TPL-26）をラップする実装系 Skill。**スクリプト自体は変更せず**、`delivery/plugin-architecture.json` から CLI 引数を組み立て、人間に確認を取って実行し、生成後の post-checks をまとめて行う。

> 設計方針: スクリプトは TPL-26 の責任範囲、本スキルは「引数組立 + 対話確認 + 後処理」の責任範囲。スクリプトを直接 `bash` で呼ぶこともできるが、本スキル経由だと architecture.json 由来のメタデータが反映され、生成後の post-checks が漏れない。

## 入出力

- **入力:**
  - `delivery/plugin-architecture.json`（`aid-plugin-architecture-design` の出力・必須）
  - （オプション）`--force`（既存プラグインを上書き）/ `--no-domain-architect`（domain-architect 雛形を実体化しない）
- **出力:**
  - `ai-delivery/plugins/<plugin_name>/`（新規プラグインの骨格・generate-plugin.sh 経由）
  - `delivery/scaffold-log.md`（実行コマンド・生成結果・post-checks の証跡）
  - 警告があれば `docs/pending-decisions.md` へ追記（warn_and_document）

## CLI 引数の組み立て（plugin-architecture.json → generate-plugin.sh）

| `generate-plugin.sh` 引数 | 由来フィールド | 必須 | 備考 |
|---|---|---|---|
| `<usecase>` | `usecase` | ✓ | 第1位置引数。`[a-z][a-z0-9-]*` を満たすこと |
| `--description "<text>"` | `description`（無ければ `usecase` から生成） | 推奨 | plugin.json に入る。長すぎないこと |
| `--author "<name>"` | 既定 `Xtone` | 推奨 | `--author` 指定がなければ `Xtone` を使う |
| `--domains "<csv>"` | `applicable_domains.join(",")` | 推奨 | T-008 ドメインタクソノミーから選定済みの前提 |
| `--modules "<csv>"` | `module_candidates.join(",")` | 推奨 | MCS-DB 参照済みの前提 |
| `--domain "<label>"` | `domain_label`（自然言語ラベル・例: `決済` `通知`） | 推奨 | `<usecase>-architect.md` 内の二重波括弧プレースホルダ `｛｛domain｝｝` 置換に使う |
| `--no-domain-architect` | `subagents` に `<usecase>-architect` が無い場合 | 任意 | DP-AID-05 で「不要」判定の場合のみ付与 |
| `--force` | 人間が明示的に許可した場合のみ | 任意 | **既存上書きは確認必須**（事故防止） |

> `plugin-architecture.json` に `description` / `domain_label` が無ければ、本スキルが**ユーザに質問して埋める**（自動補完しない）。

## 手順

1. **前提チェック**:
   - `delivery/plugin-architecture.json` の存在確認。無ければ「先に `/aid-skill-creator-design` を実行」と促す（warn_and_document・ブロックしない）。
   - `ai-delivery/scripts/generate-plugin.sh` の実行権限を確認。
   - 生成先 `ai-delivery/plugins/xtone-<usecase>-plugin/` が**既存でないか**確認。既存なら `--force` 許可をユーザに必ず取る。
2. **CLI 引数組立**:
   - 上表に従い `plugin-architecture.json` から値を取り出す。
   - 不足項目はユーザに質問（descriptions / domains / modules / domain_label）。AI が勝手に埋めない。
   - 組み立てたコマンドを**実行前にプレビュー表示**して確認を取る。
3. **実行**:
   - `bash ai-delivery/scripts/generate-plugin.sh <args>` を実行。
   - stdout / stderr を `delivery/scaffold-log.md` に記録。
4. **post-checks**:
   - **symlink 整合**: `schemas/` / `skills/implementation/tech-version-check/` / `skills/implementation/implementation-skill-planner/` が xtone-shared-plugin への symlink で**実体到達可能**か確認（`readlink` + `-e`）。
   - **未置換プレースホルダ**: generate-plugin.sh が出力した警告（`⚠️ 未置換のプレースホルダが残っています`）をそのまま `pending-decisions.md` 形式に変換して追記。
   - **`<usecase>-architect.md` / `<usecase>-design.md` の実体化確認**（`--no-domain-architect` 未指定時）。雛形のままなら「次に `/aid-architect-author <usecase>` を実行してください」と促す。
   - **`validate-plugin.sh` を呼ぶ**: `/aid-validation-runner` を起動するか、または `bash ai-delivery/scripts/validate-plugin.sh <plugin-dir>` を直接実行。`--strict` は使わない（warn_and_document）。
5. **次アクション提示**: 以下を `delivery/scaffold-log.md` の末尾に書く（人間レビュー用）：
   ```
   ## 次の手順
   1. /aid-architect-author <usecase>          # <usecase>-architect.md の中身を埋める
   2. /aid-skill-new design <usecase>-design    # 設計 Skill を起稿
   3. /aid-skill-new implementation <usecase>-<setup-name>  # 実装 Skill を起稿
   4. /aid-references-new <skill> <stack>       # 言語別 references を追加
   5. /aid-dp-register                          # 検出した DP-DRAFT を Notion 起票
   6. /aid-sample-case-binding <usecase> <case> # sample-cases から symlink
   7. /aid-validation-runner                    # 仕上げの品質ゲート
   ```

## 既知の制約・落とし穴

- **プラグイン名の接尾辞は自動付与**: `generate-plugin.sh` が `usecase=payment` を渡すと出力は `xtone-payment-plugin`（自動で `-plugin` が付く）。`plugin-architecture.json` の `plugin_name` は確認用であり、`usecase` 単体だけを引数に渡す。両者が食い違っていれば警告して人間判断を仰ぐ。
- **`--force` は危険**: 既存プラグインの全削除 → 再生成になる。**手で書いた SKILL.md / agent.md がすべて消える**。本スキルでは `--force` は**ユーザが明示的に文字列で許可した場合のみ**付与する（誤クリック防止）。
- **`｛｛domain｝｝` 未置換の警告は意図的**: `--domain` を渡さないと `<usecase>-architect.md` 内の二重波括弧プレースホルダ `domain` が未置換で残る。これは generate-plugin.sh の warn_and_document 出力なのでブロックしない。`/aid-architect-author` が後段で埋める（本ドキュメントで実例を示す際は全角の `｛｛…｝｝` を使い、validate の grep に自己マッチさせない）。
- **macOS / GNU sed 両対応**: generate-plugin.sh は `.bak` 経由で sed 差を吸収済み。本スキルから sed を直接呼ばない。
- **`schemas/v1/` 内のテンプレ表記は誤検出対象外**: validate-plugin.sh は `schemas/v1/` を grep 除外する設計。本スキルから schemas 内を別途 grep しない。

## 判断ポイント（人間判断をスルーさせない）

- **DP-AID-01**（横断 Skill 切り出し）: `plugin-architecture.json` の `cross_cutting_candidates` を見て、scaffold 時点では何もしない（後段 `/aid-skill-new` で対処）。
- **`--force` の許可**: AI が自動で付与しない。ユーザに明示確認を取り、`decision_record` 相当を `delivery/scaffold-log.md` に残す（誰がいつ何を上書きしたかを追跡可能に）。
- **`--no-domain-architect` の付与**: `plugin-architecture.json` の `subagents` に `<usecase>-architect` が無いことが根拠。DP-AID-05 を引いた判断記録を log に残す。

未決があれば `docs/pending-decisions.md` に追記し、`scaffold-log.md` から該当行へリンクする（T-002 warn_and_document）。

## メタゆえの留意点

- **本プラグイン自身の scaffold には使わない**: 本プラグインは `xtone-aid-skill-creator-plugin` として既に生成済み（Step 1）。再生成は循環参照リスク（ADR-AID-001 予定）。**自プラグインの再生成は手動 + ドッグフード前提**で運用する。
- **scaffold-log.md は git に含める**: 誰がいつ何を生成したかの履歴。`docs/scaffold-log/<plugin>-<YYYYMMDD>.md` に分けて保存することも検討。
- **dry-run モードは generate-plugin.sh に未実装**: 本スキルでは「組み立てたコマンドのプレビュー」を dry-run の代わりにする（実行前に必ず人間確認）。
