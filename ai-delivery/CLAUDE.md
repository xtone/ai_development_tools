# AIデリバリシステム — Claude Code 作業ガイド

> 背景・ディレクトリ構造は @README.md / Notion DB 一覧は @docs/notion-db-catalog.md / MCP 設定・運用・トラブルシューティングは @docs/mcp-setup-guide.md / 実行環境・バージョン方針は @docs/environment-setup.md を参照。

> **バージョン方針**: 言語・FW のバージョンは固定せず、公式の最新安定版を使う。特定バージョンが必要な場合のみ人間に確認（判断ポイント）。詳細は @docs/environment-setup.md。

## このリポジトリ（`ai-delivery/`）でやること

Xtone の開発プロセスを Claude Code プラグインで型化する。中核価値は **「人間の判断を要するポイントをスルーさせない」**。24ユースケース × 1プラグイン構成で展開する。

## 鉄則

### 1. 実装の根拠は Notion にある。コードに「なぜ」を書かず Notion の ID を参照する

仕様・規約・判断記録はすべて Notion DB（Notion MCP 経由）に蓄積されている。**実装前に必ず該当エントリを参照**し、コメントには理由を書く代わりに ID（例: `CONV-14`, `TPL-07`, `DP-03`）を記す。コード作業で主に叩く DB:

| DB | プレフィックス | data_source_id |
|---|---|---|
| 型化タスクDB | T- | `1356bc46-749e-43dd-b809-7deaf7af8383` |
| 共通テンプレ実装DB | TPL- | `e610ba21-8bff-4629-98d9-8592a64b8da2` |
| プラグイン共通規約DB | CONV- | `28849207-2a7e-46ed-a35d-d153a8329447` |
| 判断ポイントカタログDB | DP- | `64248f5c-b2f5-4c90-8ccb-7f53692b59b2` |

全16 DB の一覧と data_source_id は @docs/notion-db-catalog.md。

### 2. 判断ポイントは「気づいたその場で」記録する。後でまとめてはいけない

実装中に「これは人間判断が要る」と気づいたら即記録する:

- **既存** の判断ポイント → 判断ポイントカタログDB（DP-XXX）に decision_record を追加
- **新規** の判断ポイント → 新規エントリを追加（DP-25, DP-26, …）

「実装してから後でまとめて記録」は禁止。これは T-002 本決定「人間判断をスルーさせない」と pending-watcher Subagent（T-016）の存在理由そのもの。判断が下りていない未決事項は @docs/pending-decisions.md に明示する。

### 3. CI / Hook / Subagent はすべて warn_and_document（T-002 本決定）

警告のみ・ブロックなし。検証は止めず、未決はドキュメントに残して人間が判断する時間を確保する。

### 4. スキーマは1箇所だけ（Single Source of Truth, CONV-14）

スキーマは `xtone-shared-plugin/schemas/v1/` のみに置き、各プラグインは symlink で参照する。Breaking change 時は `schemas/v1/` と `schemas/v2/` を並行保持する。

## 作業の進め方

### タスク着手

1. 型化タスクDB で該当 T-XXX を fetch
2. 「インプット」フィールドの前提タスク成果物 DB を参照
3. 「DoD」フィールドの達成条件を確認
4. 実装
5. 完了時に型化タスクDB の「ステータス」を「完了」に更新し、下記「進捗があったら Notion を更新する」を実施

### 進捗があったら Notion を更新する（依存グラフ含む）

タスクの完了・着手・依存変更など進捗が出たら、コードだけでなく Notion 側も同期させる。Notion が真実の源（鉄則1）なので、更新漏れはそのまま「設計と実装の乖離」になる。最低限、次を更新する:

- **型化タスクDB**（T-XXX）— ステータス。進捗の一次ソース
- **[依存グラフ](https://www.notion.so/365ceb782fa38108a733d180386bf950)** — 完了タスクを Mermaid 図で ✓・緑（`:::done`）に変更、進捗サマリ表の件数（NN/50・フェーズ進捗）を更新、更新履歴に1行追記。依存関係そのものが変わった場合は矢印（`-->`）も修正する
- **[全体俯瞰サマリ](https://www.notion.so/368ceb782fa38155a578c151d5b2a115)** — プロジェクト現在地・フェーズ進捗。**進捗の数値はここを正とし、二重管理しない**
- **各種実装トラッカー**（TPL- / SCH- など）— 該当エントリの検証ステータス

依存グラフは型化タスクDB の `前提タスク` を正とするスナップショット。**DB を先に直してから Mermaid を合わせる**（依存グラフ末尾の「更新ルール」を参照）。

### PR 作成

- ブランチ名: `feat/T-XXX-<usecase>`
- description に T-XXX タスクページの URL を必ず記載
- 関連する CONV / SKL / SCH / MCP / RULE の ID を本文に列挙
- レビュアー: 豊田（T-005 本決定で1名体制）

## 検証

プラグイン生成と品質ゲート＋スキーマ検証は `scripts/` 配下のシェルで行う（TPL-26 / TPL-27, B-07）。両スクリプトとも warn_and_document（T-002）— 既定では警告を出しても exit 0、`--strict` で CI 用に exit 1。

```bash
# 新規プラグイン生成（usecase は小文字英数とハイフンのみ）
ai-delivery/scripts/generate-plugin.sh <usecase> \
  --description "<説明>" --author "<著者>" \
  --domains "<適用ドメイン>" --modules "<MOD-XXX>"

# 既存プラグインの品質ゲート＋デリバリ成果物のスキーマ検証
ai-delivery/scripts/validate-plugin.sh ai-delivery/plugins/<plugin> [--strict] [--no-schema]
```

`validate-plugin.sh` は以下を一括チェックする:

1. `.claude-plugin/plugin.json` 必須フィールド・命名規約（CONV-01）
2. `schemas/` symlink（CONV-14: Single Source of Truth）
3. `skills/implementation/tech-version-check/` symlink（B-17: 横断スキル）／ `skills/implementation/implementation-skill-planner/` symlink（B-18: 横断スキル）
4. `skills/<usecase>-plugin-guide/SKILL.md` と各 `SKILL.md` の frontmatter（SKL-20 / CONV-06 / DP-27）
5. `hooks/hooks.json` ＋ シェルの実行権限
6. `.mcp.json.sample` のトークン参照（MCP-08）
7. テンプレ未置換プレースホルダ `{{...}}` の残存
8. **デリバリ成果物のスキーマ検証**（`sample-outputs/` / `delivery/` 配下の `requirements*.json`／`design*.yaml`／`implementation-plan*.json` ほか）

依存: `bash`, `jq`, `python3`, `jsonschema`, `PyYAML`。jsonschema/PyYAML は `pip3 install --user jsonschema PyYAML` で導入。

## ID プレフィックス体系（CONV-19）

| プレフィックス | 対象 | プレフィックス | 対象 |
|---|---|---|---|
| RULE | 品質ゲートルール（T-014） | DPS | 判断ポイントスキーマ（T-012） |
| DP | 判断ポイント（T-007） | MCS | モジュールスキーマ（T-013） |
| MOD | モジュール（T-013） | SCH | Subagent/Command/Hook（T-016） |
| ADR | Architecture Decision Record | MCP | MCP 統合設計（T-017） |
| FLD | I/O スキーマフィールド（T-011） | SKL | Skill MD 骨格（T-018） |
| CONV | プラグイン規約（T-015） | TPL | 共通テンプレ実装（T-019） |
