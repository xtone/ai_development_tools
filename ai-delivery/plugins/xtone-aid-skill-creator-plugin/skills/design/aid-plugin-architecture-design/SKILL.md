---
name: aid-plugin-architecture-design
description: plugin-scope.json から新規 AIデリバリプラグインのメタ設計（必要 Skill / Subagent / Command / Hook / DP 候補 / references 見立て / sample-cases 紐付け案）を生成するスキル。プラグインの設計フェーズ（/aid-skill-creator-design）で aid-skill-creator-architect Subagent を呼ぶときに使う。出力は plugin-architecture.md（人間レビュー用）+ plugin-architecture.json（後続スキル機械可読）。xtone-auth-plugin をリファレンスとし、Notion 16 DB を引く。
---

# AID Plugin Architecture Design Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

`delivery/plugin-scope.json`（`aid-plugin-scope-extraction` の出力）を入力に、**新規プラグインの構造設計**を生成する。`aid-skill-creator-architect` Subagent が本スキルを使う。出力は後続スキル `/aid-scaffold` `/aid-architect-author` `/aid-skill-new` `/aid-references-new` `/aid-dp-register` `/aid-sample-case-binding` の指示書になる。

> **注意**: 通常の `design.schema.json`（エンドユーザ向けソフトウェア設計）ではなく、**プラグインそのもののメタ設計**を出力する。スキーマ検証の対象外であるため `delivery/plugin-architecture.md` / `delivery/plugin-architecture.json` という別名で出力する（validate-plugin.sh の `design*.{yaml,json}` パターンに合致させない）。

## 入出力

- **入力:**
  - `delivery/plugin-scope.json`（必須・前段 Skill 出力）
  - `plugins/xtone-auth-plugin/`（リファレンス実装・必ず参照）
  - Notion 16 DB（Notion MCP 経由・読み取り）：SKL / CONV / DP / SCH / MCS / MCP / TPL
- **出力:**
  - `delivery/plugin-architecture.md`（人間レビュー用・本スキル §出力フォーマット 4 チャネル）
  - `delivery/plugin-architecture.json`（構造化抜粋・後続 Skill 入力）
  - 必要に応じ `docs/adr/ADR-AID-NNN.md`（メタアーキ判断記録）

## 出力フォーマット（4 チャネル必須）

`aid-skill-creator-architect.md` で定義した 4 チャネルをそのまま埋める。本スキルはその雛形と手順を提供する。

### Channel 1: 必要 Skill リスト（フェーズ別・responsibility_split 付）

| Skill 名 | フェーズ | 責務 | 責務分担 | 主参照 Notion |
|---|---|---|---|---|
| `<usecase>-requirements-extraction` | requirements | 要件抽出 | shared | SKL-XX, FLD-XX |
| `<usecase>-design` | design | 設計生成 | shared | SKL-XX, CONV-06 |
| `<usecase>-<setup-name>` | implementation | セットアップ | backend/iaas | SKL-XX, MCS-XX |
| `<usecase>-frontend` | implementation | UI 実装 | client | SKL-XX |
| `<usecase>-e2e-verify` | test | E2E 検証 | shared | SKL-XX, RULE-XX |

- 横断機能は別行として独立 Skill 候補に切り出す（B-19）
- 各行に **言語別 references が必要かのフラグ**を併記する（implementation 系は通常 yes）
- 横断 Skill は `cross_cutting: true` ＋ `kind`（`feature-spanning` / `environment-spanning` / `concern-spanning`）を併記（FINDING-01 / ADR-AID-003 候補）。リファレンス例: auth の `firebase-auth-mfa`（feature-spanning）/ `firebase-auth-emulator`（environment-spanning）

### Channel 2: Subagent / Command の拡張提案

| 種別 | 名前 | 役割 | 起動コマンド | 必要性の根拠 |
|---|---|---|---|---|
| Subagent | `<usecase>-architect` | ドメイン特化設計・DP 比較・差し替え可能設計担保 | `/<usecase>-design` | 比較スタック 2 つ以上なら必須（DP-AID-05） |
| Command | `/<usecase>-design` | 上記 architect 起動 | — | 基盤 `/design` で十分なら省略可 |
| Hook 追加 | （通常は不要） | — | — | 基盤 4 Hook で足りる場合は追加しない |

### Channel 3: 判断ポイント候補

#### 既存 DP 再利用候補（DP-AID-02 80% 重複ルール）

| 既存 DP | 当該ユースケースでの解釈 | 流用根拠 |
|---|---|---|

#### 新規 DP 起票候補（`/aid-dp-register` で起票）

| 仮 ID | タイトル | 選択肢 | 判断軸 | 誤判断リスク | MVP 推奨 |
|---|---|---|---|---|---|
| `DP-<USECASE>-DRAFT-01` | `<usecase>` スタック選択 | A / B / C | セキュリティ / コスト / スケジュール | 後段でスタック交代 | A（差し替え可能設計を維持） |

> DP 候補の命名は `DP-<USECASE>-DRAFT-NN` を仮 ID とし、Notion 起票時に正規 `DP-NNN` に置換する。

### Channel 4: 言語別 references 見立て + sample-cases 該当度

#### references 初期スタック（DP-AID-04 適用）

| Skill | 必要スタック（初期） | 追加予定 | 注意 |
|---|---|---|---|
| `<usecase>-<setup-name>` | rails / nextjs / hotwire | laravel / fastapi | 案件で必要になるまで先回りしない |

#### sample-cases 紐付け案（DP-AID-03）

| 案件 | 該当度 | 採用理由 |
|---|---|---|
| `ec-d2c-app` | ⭐⭐⭐ | … |

## 手順

1. **入力読取**: `delivery/plugin-scope.json` を読む。なければエラーではなく**「先に `/req-collect` で scope 抽出を行ってください」と促す**（warn_and_document：ブロックしない）。
2. **リファレンス読取**:
   - `plugins/xtone-auth-plugin/agents/authentication-architect.md`（DP 比較構造）
   - `plugins/xtone-auth-plugin/skills/auth-plugin-guide/SKILL.md`（CONV-06 6項目）
   - `plugins/xtone-auth-plugin/skills/design/firebase-auth-design/`（design Skill の契約 + templates 分離）
   - `plugins/xtone-auth-plugin/skills/implementation/firebase-auth-mfa/`（横断機能を独立 Skill にした型）
3. **Notion 16 DB を引く**（Notion MCP 必須）:
   - SKL-DB（当該フェーズで Skill 雛形候補）
   - CONV-DB（命名規約・ガイドライン）
   - DP-DB（既存 DP の再利用判定・DP-AID-02 80% ルール）
   - SCH-DB（Subagent / Command / Hook 拡張要否）
   - MCS-DB（モジュール跨ぎ参照点）
   - MCP-DB（外部 MCP の必要性：Figma / GitHub / Notion / 社内ナレッジ）
   - TPL-DB（共通テンプレ実装からの再利用候補）
4. **横断機能の判定**: `plugin-scope.json` の `cross_cutting_candidates` を見て、`spans` が 2 層以上なら独立 Skill に確定（B-19）。
5. **DP 比較**: 主要 DP は **2 つ以上のスタック**を並べ、MVP 推奨と**差し替え可能設計**（T-004 本決定）の担保を書く。直接 SDK を全層で呼ぶ案は MVP 推奨にしない。
6. **既存 DP 再利用判定**（DP-AID-02）:
   - DP-DB を `usecase` 関連語で全文検索
   - 80% 以上重複する DP があれば `reuse: true`、それ以外は新規候補（`DP-<USECASE>-DRAFT-NN`）
   - 起票自体は本スキルでは行わない（`/aid-dp-register` が担当）
7. **出力生成**:
   - `delivery/plugin-architecture.md`（人間レビュー用・4 チャネル全部）
   - `delivery/plugin-architecture.json`（後続 Skill が消費する構造化抜粋・後述スキーマ）
8. **重要な決定は ADR 化**: `docs/adr/ADR-AID-NNN.md` を起票（メタアーキ判断・例：「決済プラグインの DP 命名は `DP-PAYMENT-*` プレフィックスで分ける」）。
9. **未決の明示**: `undecided` に残し `docs/pending-decisions.md` に追記。

## `delivery/plugin-architecture.json` フィールド

```jsonc
{
  "usecase": "payment",
  "plugin_name": "xtone-payment-plugin",
  "skills": [
    {
      "name": "payment-design",
      "phase": "design",
      "responsibility": "決済設計（プロバイダ比較・PCI DSS スコープ判定）",
      "responsibility_split": ["shared"],
      "needs_references": false,
      "references_stacks": []
    },
    {
      "name": "payment-stripe-setup",
      "phase": "implementation",
      "responsibility": "Stripe 初期セットアップ・webhook 受け口",
      "responsibility_split": ["backend", "iaas"],
      "cross_cutting": true,
      "kind": "feature-spanning",
      "needs_references": true,
      "references_stacks": ["rails", "nextjs"]
    }
  ],
  "subagents": [
    { "name": "payment-architect", "trigger_command": "/payment-design", "required": true, "rationale": "Stripe/GMO/Komoju の比較が必要（DP-AID-05）" }
  ],
  "commands": [
    { "name": "/payment-design", "kind": "domain-design" }
  ],
  "hooks_extension": [],
  "dp_candidates": [
    { "id": "DP-007", "reuse": false, "reason": "認証用なので決済には流用しない" },
    { "id": "DP-PAYMENT-DRAFT-01", "reuse": false, "title": "決済プロバイダ選択", "mvp_recommendation": "Stripe（abstraction layer で差し替え可能設計）" }
  ],
  "sample_case_bindings": ["ec-d2c-app", "event-campaign-lp"],
  "sample_case_legacy": null,                              // 既存プラグインの後追い起稿時のみ（FINDING-02 / B-21 以前の独自案件）
                                                           // 例: { "name": "bookclub-app", "location": "sample-inputs/bookclub-app.requirements-input.md", "rationale": "B-21 以前の独自案件・経緯保存" }
  "design_extension_schema": "design.payment.schema.json",
  "external_mcps": ["github", "notion"],
  "undecided": []
}
```

## 差し替え可能設計の指針（T-004 本決定）

新規プラグインの主要 DP には必ず以下を含める：

- 処理（主要 API 呼び出し）は **アダプタインターフェース**越しに呼ぶ
- ベンダー固有 SDK 呼び出しはアダプタ実装に閉じ込め、アプリ本体は抽象に依存
- 別ベンダー追加時はアダプタ実装の差し替えのみで済む構造（Rollout で実証）

`responsibility_split` 表に `iaas` を含む Skill では特に必須。

## 判断ポイント（人間判断をスルーさせない）

メタ設計段階で確定しない方針は AI が決めない：

- **DP-AID-01**: 横断 Skill 切り出し → 推奨だけ提示
- **DP-AID-02**: DP 再利用判定 → 80% 重複ルールで判定、迷ったら人間
- **DP-AID-05**: domain-architect の要否 → 比較スタック 2 つ以上で「必要」推奨

未決は `delivery/plugin-architecture.json` の `undecided` と `docs/pending-decisions.md` に残す（T-002 warn_and_document）。

## 後続スキルへの引き渡し

| 後続 Command/Skill | 入力 |
|---|---|
| `/aid-scaffold <usecase>` | `plugin_name` / `applicable_domains` / `module_candidates` / `commands` 拡張要否 |
| `/aid-architect-author <usecase>` | `subagents[*]` の `<usecase>-architect` + `dp_candidates` |
| `/aid-skill-new <phase> <skill>` | `skills[*]` の各行 |
| `/aid-references-new <skill> <stack>` | `skills[*].references_stacks` |
| `/aid-dp-register` | `dp_candidates[?reuse == false]` |
| `/aid-sample-case-binding` | `sample_case_bindings[*]` |

## メタゆえの留意点

- 本スキルは **`design.schema.json` を生成しない**。出力はプラグインそのものの構造設計であり、`delivery/plugin-architecture.{md,json}` という別フォーマット。validate-plugin.sh のスキーマ検証対象外。
- 出力 `plugin-architecture.json` は **スキーマ化候補**（DP-AID 議論中）。安定したら `xtone-shared-plugin/schemas/v1/plugin-architecture.schema.json` 起票を検討する（ADR 化）。
- リファレンスは常に `xtone-auth-plugin`。型を写し取るが、過剰に縛らない（B-19 が示すように、独立 Skill 切り出しの判断はドメイン依存）。
