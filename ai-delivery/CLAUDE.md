# AIデリバリシステム — Claude Code 作業ガイド

> 背景・ディレクトリ構造は @README.md / Notion DB 一覧は @docs/notion-db-catalog.md / MCP 設定・運用・トラブルシューティングは @docs/mcp-setup-guide.md を参照。

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
5. 完了時に型化タスクDB の「ステータス」を「完了」に更新

### PR 作成

- ブランチ名: `feat/T-XXX-<usecase>`
- description に T-XXX タスクページの URL を必ず記載
- 関連する CONV / SKL / SCH / MCP / RULE の ID を本文に列挙
- レビュアー: 豊田（T-005 本決定で1名体制）

## 検証

> ⚠️ 現状、検証スクリプトは未整備。`scripts/validate-plugin.sh`（TPL-27）作成後、実行コマンドをこのセクションに追記すること。
> プラグイン実装時は `xtone-shared-plugin/schemas/v1/` の JSON Schema に対するバリデーションを必ず通す（CI の 18 ルール検証 = T-014 と整合させる）。

## ID プレフィックス体系（CONV-19）

| プレフィックス | 対象 | プレフィックス | 対象 |
|---|---|---|---|
| RULE | 品質ゲートルール（T-014） | DPS | 判断ポイントスキーマ（T-012） |
| DP | 判断ポイント（T-007） | MCS | モジュールスキーマ（T-013） |
| MOD | モジュール（T-013） | SCH | Subagent/Command/Hook（T-016） |
| ADR | Architecture Decision Record | MCP | MCP 統合設計（T-017） |
| FLD | I/O スキーマフィールド（T-011） | SKL | Skill MD 骨格（T-018） |
| CONV | プラグイン規約（T-015） | TPL | 共通テンプレ実装（T-019） |
