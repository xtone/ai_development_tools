---
name: tech-version-check
description: 採用予定の言語/FW/主要ライブラリの **最新安定版と相互互換性** を実装着手の前に取得・記録するスキル。実装フェーズで firebase-auth-setup / firebase-auth-frontend / firebase-auth-mfa / firebase-auth-emulator を呼ぶ前の前提作業として、context7（または WebFetch / WebSearch fallback）で公式情報を引き、`delivery/version-matrix.md` にバージョン採用根拠と既知の非互換性を残す。バージョン固定はせず公式最新を採る方針（`docs/environment-setup.md`）の実行スキル。
---

# Tech Version Check Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

実装着手の前に、`design.yaml.architecture.stack` に列挙された採用スタック（言語 / FW / 主要ライブラリ）について **公式の最新安定版とフレームワーク要求の最小言語バージョン**を取得し、`delivery/version-matrix.md` に採用根拠と日付を残す。

サンプル案件 sample-auth で **Ruby/Rails の最新版確認が事前に行われず**、`connection_pool 3.0.2` が Ruby 3.3 非互換に当たって途中で気づく事故が発生した（B-11）。本スキルはこの種の事故を未然に塞ぐ。

> 方針: バージョンは固定しない（陳腐化回避）、基本は公式の最新安定版、特定バージョンが必要な場合は判断ポイント — [`ai-delivery/docs/environment-setup.md`](../../../../docs/environment-setup.md)。本スキルはその「公式最新を取得する」手順の実体。

## 呼び出しトリガ（B-13 連携）

`implementation-skill-planner` が以下の判定で skill_plan に列挙する（required=true 既定）:

- `design.yaml.architecture.stack` に**何らかの言語/FW が記述されている**（実装フェーズの全案件で必須）
- 既に `delivery/version-matrix.md` が存在し、かつ作成日が直近（プロジェクトの基準内、例: 30 日以内）なら **skip 可**（trigger に "version-matrix.md is fresh" を残す）

未呼び出しのまま実装フェーズが完了に到達した場合は warn_and_document に従い警告（T-002）。

> 本スキルは firebase-auth-setup / -frontend / -mfa / -emulator のいずれよりも**前**に呼ぶ。skill_plan 上の順序として最先頭に置く。

## 入出力

- 入力: `delivery/design.yaml` の `architecture.stack` / 採用ライブラリ一覧（および要件由来の制約）
- 出力: `delivery/version-matrix.md`（採用バージョン + 既知の非互換性 + 採用日 + 採用根拠 URL）

スキーマは編集しない（CONV-14）。

## 取得対象（言語非依存）

採用スタックから抽出される **最低 4 群** を必ず記録する:

1. **言語ランタイム**（Ruby / Node.js / Python / PHP / Go 等）
2. **メイン FW**（Rails / Next.js / Laravel / Django / Express / FastAPI 等）
3. **主要ライブラリ・SDK**（Firebase Admin SDK / `firebase` JS SDK / DB アダプタ / 認証関連 gem-pkg 等）
4. **ツール / コンテナ**（`firebase-tools`（CLI）/ Docker base image / Node base image 等）

> サンプル案件 sample-auth では `connection_pool` のような**間接依存**が問題化した。直接依存だけでなく、**主要ライブラリの間接依存で言語バージョン制約が出るもの**は気付いた時点で記録対象に追加する。

## 取得手段（優先順）

| 優先 | 手段 | 使い所 |
|---|---|---|
| 1 | **context7 MCP**（`mcp__plugin_context7_context7__resolve-library-id` → `query-docs`） | 公式 docs から最新版 / 要求ランタイムを構造化取得（精度高） |
| 2 | **WebFetch** | 公式リリースページ（例: https://github.com/firebase/firebase-tools/releases、https://rubygems.org/gems/rails ）を直接取得 |
| 3 | **WebSearch** | 1/2 で当たらない場合のフォールバック（曖昧検索） |

> context7 が解決しない / 結果が古い場合は WebFetch に降り、最終手段で WebSearch。**根拠 URL は必ず version-matrix.md に残す**（採用日時点の確認証跡）。

## 手順

1. `design.yaml.architecture.stack` から採用スタックを列挙（記述粒度が粗い場合は人間に確認）。
2. 上記「取得対象」4 群を順に context7 等で取得:
   - 各言語/FW/ライブラリの **最新安定版**（major.minor.patch）と **要求ランタイム**（例: Rails 8.x → Ruby 3.x 以上）
   - **既知の非互換性**（採用最新版で問題があれば公式 issue / リリースノートから抽出）
3. `delivery/version-matrix.md` に表形式で記録（[`templates/version-matrix.template.md`](./templates/version-matrix.template.md) 参照）。
4. **`Gemfile` / `package.json` / `Dockerfile`** にコメント形式で「採用根拠（B-11 で確認、日付、根拠 URL）」を残す。固定バージョン値は判断ポイントなので、AI が勝手に固定しない（明示的な要望がある場合のみ pin）。
5. **判断ポイントを `docs/pending-decisions.md` に起票する（人間判断をスルーさせない / T-002 / B-25）**。次の 2 種は AI が推奨で独断確定せず、必ず案件側の `docs/pending-decisions.md` の「未決リスト」表に **1 件 1 行**で起票する（手順は下記「複数候補が残った技術判断の DP 起票（B-25）」節）:
   - **複数候補が残った技術判断**: 公式情報源から **2 つ以上の妥当な候補**が得られ、どれを採るかが案件依存（性能・運用・互換性のトレードオフ）な場合。例: Ruby 3.3 / 3.4 並存、Sidekiq vs SolidQueue、googleauth+REST vs firebase-auth-rails gem。
   - **非互換の解消方針**: 採用最新版に既知の非互換性があり、「採用バージョンを下げるか / 互換ライブラリに替えるか」の選択が必要な場合。
6. 取得情報を `implementation-plan.json.skill_plan` の本エントリ `called=true` に更新。

## 出力テンプレ

雛形（プレースホルダ・サンプル値・Gemfile/package.json/Dockerfile のコメント例を含む完全版）は **[`templates/version-matrix.template.md`](./templates/version-matrix.template.md)** を参照。`delivery/version-matrix.md` を新規作成するときは、このテンプレートをコピーして `<...>` プレースホルダを実値で埋める。

テンプレートには次の節がある:

1. 言語ランタイム表
2. メイン FW 表
3. 主要ライブラリ・SDK 表
4. ツール / コンテナ表
5. 既知の非互換性 / 警戒事項
6. **複数候補が残った技術判断（DP 起票 / B-25）** — 候補が複数残った技術を列挙し pending-decisions と相互参照
7. 採用根拠の要約
8. **Gemfile / package.json / Dockerfile に残すコメント例**（手順 4 で各依存ファイルへ追記する形式の見本）

> SKILL.md にインライン例を二重に持たない（テンプレートとの乖離回避）。Single Source of Truth はテンプレートファイル側。

## 複数候補が残った技術判断の DP 起票（B-25）

`version-matrix.md` 生成中、公式情報源から **2 つ以上の妥当な候補**が出てどれを採るかが案件依存になる技術判断が頻出する（Ruby 3.3 / 3.4 並存、Sidekiq vs SolidQueue、googleauth+REST vs firebase-auth-rails gem 等）。ここで agent が推奨を独断で確定すると、T-002 warn_and_document（人間判断をスルーさせない）に反する。**version-matrix.md を書き終えた直後**に、残った技術判断を列挙して `docs/pending-decisions.md` に起票する。

### 起票する / しない（誤検知防止）

- **起票する**: 公式情報源から取得した候補が **2 つ以上**あり、選定基準が性能・運用・互換性・将来性などのトレードオフで、案件の事情に依存する判断。
- **起票しない（誤検知を出さない）**:
  - 候補が **1 つしかない**（公式最新が一意に定まる）。`environment-setup.md`「公式の最新安定版を採る」で機械的に決まるものは判断ポイントではない。
  - パッチバージョンだけの違い（例: 3.3.5 vs 3.3.6）など、選定に人間判断が要らないもの。
  - 既に `design.yaml.decision_record[]` で **確定済み（`chosen` あり）**の判断（重複起票しない）。

> 単一候補で起票しないことは受け入れ基準（誤検知なし）。「迷う余地があるか」を基準にする — 公式最新が一意なら起票しない、複数の安定版・複数の実装方式が並ぶなら起票する。

### DP 仮 ID の命名

確定前なので Notion 採番（DP-NNN）ではなく、**内容が分かる仮 ID** を付ける（pending-watcher / 人間が後で正式採番する）:

- バージョン選定: `DP-<TECH>-VER`（例: `DP-RUBY-VER`, `DP-RAILS-VER`, `DP-NODE-VER`）
- 実装方式・ライブラリ選定: `DP-<TOPIC>`（例: `DP-JOB-BACKEND`（Sidekiq vs SolidQueue）, `DP-AUTH-RUBY-SDK`（googleauth+REST vs firebase-auth-rails gem））

### 起票フォーマット

案件側 `docs/pending-decisions.md` の「未決リスト」表に **1 候補 1 行**で append する（複数あればマージせず DP ごとに 1 行ずつ）。表ヘッダは当該ファイルの「未決リスト」節に合わせる（プラグインにより `フェーズ` 列か `関連タスク` 列かが異なる — 既存行に倣う）。記載例:

```markdown
| <YYYY-MM-DD> | DP-RUBY-VER | 言語ランタイム Ruby のバージョン候補が複数（3.3 系 / 3.4 系）。採用 FW の required_ruby_version と運用実績で案件が選ぶ。tech-version-check が公式最新から複数候補を検出。 | 実装 | tech-version-check | 未決 |
| <YYYY-MM-DD> | DP-JOB-BACKEND | 非同期ジョブ基盤の候補が複数（Sidekiq / SolidQueue）。Redis 依存可否・運用体制で案件が選ぶ。 | 実装 | tech-version-check | 未決 |
```

起票したら `version-matrix.md` の該当行（または「7. 採用根拠の要約」）に **`DP-XXX 起票済み（pending-decisions.md 参照）`** を残し、matrix と pending の相互参照を保つ。確定前は version-matrix 上で当該技術を「未確定」と明記し、暫定採用値を断定で書かない。

### 検証シナリオ（受け入れ基準の確認手順）

スキル変更時はこのシナリオで挙動を確認する（複数候補が出る代表ケース = Rails 7.x / 8.x 並存期）:

1. `design.yaml.architecture.stack` に Rails を含む案件で本スキルを実行する。
2. 公式情報源（rubygems.org / リリースノート）に **7.x 系と 8.x 系の両安定版**が並ぶ状況を取得する。
3. **期待**: `docs/pending-decisions.md` の未決リストに `DP-RAILS-VER`（7.x / 8.x のいずれを採るか）が 1 行起票される。
4. **誤検知チェック**: 候補が一意（例: Node.js Active LTS が 1 系列のみ）な技術については **起票されない**ことを確認する。
5. 既に `decision_record[]` に `DP-RAILS-VER` が `chosen` 済みで渡された場合は **重複起票しない**ことを確認する。

## 判断ポイント（人間判断をスルーさせない）

- **特定バージョン固定の要望**: クライアント制約・レガシー互換などで「最新ではない特定バージョン」を要求された場合、`docs/pending-decisions.md` に DP として起票し、確認後に固定する（AI が勝手に古いバージョンを採らない）。
- **非互換性の解消方針**: 採用最新版に既知の非互換性がある場合、代替ライブラリへの差し替えか採用バージョンの一時的な前進版採用かの選択。pending-decisions に起票。
- **取得粒度**: 全依存をスキャンするか / 主要依存のみに留めるか。プロジェクトのリスク許容度で人間が決める。

## 関連スキル

- 後続: `firebase-auth-setup` / `firebase-auth-frontend` / `firebase-auth-mfa` / `firebase-auth-emulator`（本スキルの version-matrix.md に従って Gemfile / package.json / Dockerfile を埋める）
- バージョン方針: [`ai-delivery/docs/environment-setup.md`](../../../../docs/environment-setup.md)
- 配置（横断スキル）: 本スキルは `xtone-shared-plugin/skills/implementation/tech-version-check/` に実体を置き、各プラグイン（`plugins/xtone-*-plugin/skills/implementation/tech-version-check`）と `xtone-plugin-template/skills/implementation/tech-version-check` からは **symlink** で参照する（CONV-14 / B-17）。新規プラグイン生成時は `schemas/` と同じく symlink を再作成する（[`xtone-plugin-template/README.md`](../../../../xtone-plugin-template/README.md)）。
