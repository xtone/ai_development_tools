---
name: aid-validation-runner
description: ai-delivery/scripts/validate-plugin.sh を実行し、警告を解析して docs/pending-decisions.md に整形追記するスキル。プラグインの実装フェーズ末尾と各 Skill 追加後に使う。validate-plugin.sh の 8 種類の検証カテゴリ（plugin.json / symlink / SKILL.md frontmatter / hooks / .mcp.json.sample / 未置換 / スキーマ / sample-inputs）を分類し、修正候補をユーザに提示する。--strict / --no-schema の使い分けと warn_and_document の流儀を明示。
---

# AID Validation Runner Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`ai-delivery/scripts/validate-plugin.sh`（TPL-27）をラップする実装系 Skill。**スクリプト自体は変更せず**、実行 → 警告解析 → カテゴリ分類 → `docs/pending-decisions.md` 整形追記 → 修正候補提示までを一気通貫で行う。

> 設計方針: スクリプトは TPL-27 の責任範囲、本スキルは「実行 + 警告整形 + pending-decisions 同期 + 修正候補提示」の責任範囲。

## 入出力

- **入力:**
  - 対象プラグインのパス（既定: 本プラグイン自身、または直前の `/aid-scaffold` で生成したプラグイン）
  - フラグ: `--strict`（CI 用・1 件でも警告で exit 1） / `--no-schema`（スキーマ検証スキップ）
- **出力:**
  - `delivery/validation-report.md`（実行ログ + 警告分類 + 修正候補）
  - `docs/pending-decisions.md` への追記（未決の判断ポイントとして残るもの）
  - exit code: 既定 0（warn_and_document）。`--strict` 時のみ警告ありで 1

## 検証カテゴリ（validate-plugin.sh の 8 種類）

| # | カテゴリ | 検証内容 | よくある原因と修正 |
|---|---|---|---|
| 1 | `plugin.json` 必須フィールド | name / version / description / author.name の存在、name の `xtone-*-plugin` 形式（CONV-01） | plugin.json を直接編集。`generate-plugin.sh` 経由なら通常出ない |
| 2 | `schemas/` symlink | xtone-shared-plugin/schemas/v1 への symlink（CONV-14） | 実体コピーになっていれば削除して `ln -s` で張り直す |
| 2b | `tech-version-check` symlink | xtone-shared-plugin への symlink（B-17） | 同上 |
| 2c | `implementation-skill-planner` symlink | xtone-shared-plugin への symlink（B-18） | 同上 |
| 3 | SKILL.md frontmatter | `<usecase>-plugin-guide/SKILL.md` の存在 / 各 SKILL.md の `name` / `description`（SKL-20） | frontmatter の `---` 区切りや必須フィールド漏れを修正 |
| 4 | hooks | `hooks.json` の存在 + 各 `.sh` の実行権限 | `chmod +x hooks/*.sh` |
| 5 | `.mcp.json.sample` トークン参照 | `${FIGMA_TOKEN}` / `${GITHUB_TOKEN}` / `${NOTION_TOKEN}` 参照（MCP-08） | テンプレを書き換えてトークン参照を追加 |
| 6 | 未置換プレースホルダ（二重波括弧, 全角表記で `｛｛…｝｝`） | `*.template` を除く全ファイル、`schemas/v1/` 除外 | generate-plugin.sh 再実行 or `--domain` 引数の付け忘れを修正 |
| 7 | デリバリ成果物のスキーマ検証 | `sample-outputs/` / `delivery/` の `requirements*.{json,yaml}` / `design*.{json,yaml}` 等を JSON Schema で検証 | スキーマ違反箇所を修正（`schemas/v1/*.schema.json` 参照） |
| 8 | sample-inputs symlink | `xtone-shared-plugin/sample-cases/` への symlink 整合 | `/aid-sample-case-binding` で張り直す |

> 7 のドメイン拡張スキーマ（`design.auth.schema.json` 等）は `plugin.json` の `delivery.design_extensions` 宣言により合成検証される（B-20 / #173）。

## フラグの使い分け（`--strict` vs `--no-schema` vs 既定）

| 用途 | フラグ | 理由 |
|---|---|---|
| **ローカル日常検証** | 既定（フラグなし） | warn_and_document に沿い、警告を見つつ作業継続 |
| **CI** | `--strict` | 警告ゼロを強制（リリース前 gate） |
| **scaffold 直後の素状態確認** | `--no-schema` | デリバリ成果物がまだ無い段階で「スキーマ未発見」警告を抑止 |
| **DP / sample-case のドラフトレビュー段階** | 既定 + `--deliverable-dir <custom>` | 別ディレクトリの成果物を検証したい場合 |

> 本プラグイン自身（`xtone-aid-skill-creator-plugin`）は通常はデリバリ成果物を持たないので、`--no-schema` を既定にする選択もある（ℹ️ 情報レベルなので強制ではない）。

## 警告の解析 → `pending-decisions.md` への整形追記

`validate-plugin.sh` の警告行は `⚠️  <message>` で始まる。本スキルでは：

1. stderr / stdout を取り、`⚠️` で始まる行を抽出。
2. メッセージから上表の **カテゴリ番号**を逆引きする（先頭の主語キーワード `plugin.json` / `schemas/` / `hooks/` / `.mcp.json.sample` / `未置換` / `スキーマ` / `sample-inputs` 等で分類）。
3. **既存 `pending-decisions.md` テーブルの末尾**に以下の行を追加：

```markdown
| YYYY-MM-DD | AID-VAL-<連番> | <カテゴリ番号>: <警告メッセージ要約> | <対象プラグイン>:<該当ファイル相対パス> | aid-validation-runner | 未対応 |
```

ID は仮 ID（`AID-VAL-001`〜）。正規 DP として起票するものは `/aid-dp-register` を別途流す。同一警告が複数回出ても**起票日 + メッセージ**で重複判定し、既存があれば更新日のみ書き換える。

## 手順

1. **対象決定**: 引数で対象プラグインが指定されていればそれを使う。なければ：
   - 直前の `/aid-scaffold` で生成したプラグインがあればそれを既定にする
   - そうでなければ本プラグイン自身（`xtone-aid-skill-creator-plugin`）を既定にする
2. **フラグ決定**: ユーザに明示指定があればそれを使う。なければ用途に応じて既定（上表）。
3. **実行**:
   ```bash
   bash ai-delivery/scripts/validate-plugin.sh <plugin-dir> [--strict] [--no-schema]
   ```
   stdout / stderr を `delivery/validation-report.md` に記録（タイムスタンプ付）。
4. **警告解析**:
   - `⚠️` 行を全部抽出
   - カテゴリ番号で集計（カテゴリ別件数のサマリを出す）
   - 重大度判定（後述）
5. **`pending-decisions.md` 同期**:
   - **対象プラグインの `docs/pending-decisions.md`** に追記（本プラグインの pending-decisions.md ではない）
   - 既存 ID と重複しないよう連番採番
6. **修正候補提示**:
   - 上表「よくある原因と修正」を参考に、ユーザが取れる次アクションをリスト化
   - 自動修正できそうな項目（hooks の `chmod +x` 等）は**提案だけ**して人間に確認を取る（勝手に修正しない）
7. **次アクション**: 警告ゼロなら `✅ Validation passed`、警告ありなら「上位 N 件を表示 → 修正 → 再実行」のループを促す。

## 重大度判定（本スキル独自・warn_and_document 内のトリアージ）

`validate-plugin.sh` 自体は警告と info を区別するだけだが、本スキルでは追加で：

| 重大度 | 判定基準 | 推奨対応 |
|---|---|---|
| **Block-worthy（CI fail 推奨）** | カテゴリ 1（plugin.json 必須欠落）/ 2-2c（symlink 不整合）/ 3（plugin-guide SKILL.md 欠落）/ 6（未置換が `plugin.json` / `SKILL.md` に残存） | 即修正してから次へ |
| **Should-fix** | カテゴリ 4（hooks 実行権限）/ 5（.mcp.json.sample） / 7（スキーマ違反）/ 8（symlink 壊れ） | 次のフェーズ移行前に修正 |
| **Info-only** | ℹ️（デリバリ成果物未発見）/ カテゴリ 6（`*.template` 内の意図的プレースホルダ・誤検出） | 状況次第で `--no-schema` 等で抑止 |

> `--strict` を CI で付ける場合、Should-fix と Block-worthy の両方で exit 1 になる。CI 通過に必要な最低限のラインを `docs/usage-guide.md` で明文化する。

## 既知の制約・落とし穴

- **本プラグイン自身を対象に実行すると `--no-schema` でないと「ℹ️ デリバリ成果物が見つかりません」が出る**。これは情報レベル（警告ではない）。`exit 0` のままなので無視可。
- **未置換プレースホルダ（二重波括弧）の誤検出**: `schemas/v1/` は除外されるが、本スキルが解析する際にも同等の除外を行うこと（ある stack の `references/<stack>.md` 内のコードフェンスに偶然 ｛｛…｝｝ パターンがある場合に注意。本文で実例を書く際は全角や空白挟みで表記し、grep 自己マッチを避ける）。
- **`pending-decisions.md` の自動追記**: テーブル末尾への append は機械的に行えるが、**既存 ID とのコンフリクト**は避ける（連番は ファイル全体の grep で次の番号を決める）。
- **CI（GitHub Actions）からも本スキルを使えるが、実体は validate-plugin.sh の起動**。CI からは Skill を介さず直接 `bash validate-plugin.sh --strict` を呼ぶのが既定。本スキルは「人間が触る場面」での解析・整形補助に特化する。

## 判断ポイント（人間判断をスルーさせない）

- **`--strict` を CI 以外で付けるか**: 既定 NO（warn_and_document に反する）。例外的に付ける場合は `decision_record` に理由を残す。
- **警告の `pending-decisions.md` への追記レベル**: 全警告を機械的に追記すると **テーブルが肥大化**する。Block-worthy / Should-fix のみ追記し、Info-only はサマリのみとする運用を推奨（DP-AID 議論候補）。
- **自動修正の範囲**: hooks の `chmod +x` 等の機械的修正でも、AI が勝手に実行しない。**ユーザ確認を取ってから実行**する（誤って想定外のファイルへ権限変更しないため）。

未決は `docs/pending-decisions.md` に残し、`delivery/validation-report.md` から該当行へリンクする（T-002 warn_and_document）。

## メタゆえの留意点

- **本スキルは validate-plugin.sh を「再実装」しない**。あくまでラッパー。スクリプトの仕様変更（カテゴリ追加など）が起きたら、本スキル §検証カテゴリ表も追従して更新する（責任範囲：本スキル）。
- **本プラグイン自身のドッグフード**: `/aid-validation-runner` を本プラグイン自身に実行し、warning ゼロを維持する。これが「メタゆえの循環参照リスク」の最低限のセーフティ。
- **`--deliverable-dir` の使いどころ**: scaffold したばかりのプラグインで `delivery/plugin-architecture.json` などのメタ成果物を検証対象にしたい場合は、`--deliverable-dir <dir>` で限定できる。ただし plugin-architecture.json は通常スキーマと無関係なので、本スキルでは特別扱いしない（将来 ADR-AID で plugin-architecture.schema.json を起票するかは別議論）。
