---
name: aid-skill-creator-plugin-guide
description: xtone-aid-skill-creator-plugin の作業ガイド。AIデリバリシステム自身のプラグインを「型に則って中身ごと」起こすときに使う。新規ユースケース（T-023〜T-045 の Rollout）プラグインの設計・骨格生成・Skill/Subagent/Command/references/DP 起稿・パイロットまでをガイドする。Notion DB（TPL/SKL/CONV/DP/SCH/MCS）参照前提。
---

# xtone-aid-skill-creator-plugin 作業ガイド

このプラグインは Xtone AIデリバリシステムの **メタプラグイン**。23 本の Rollout プラグイン（T-023〜T-045）を「**AIデリバリの型に則って中身ごと**」起こすための助手として動く。マスターテンプレ `xtone-plugin-template`（T-019）から生成し、メタ特化の Subagent / Command / Skill を追加したもの。プロジェクト全体のルールはリポジトリの `ai-delivery/CLAUDE.md` を参照。

> このプラグインの運用 context は（ルート CLAUDE.md ではなく）本スキルに置く。Claude Code ではプラグインルートの `CLAUDE.md` は project context として読み込まれないため（DP-27 / CONV-06）。

## プラグイン概要（CONV-06）

| 項目 | 値 |
|---|---|
| **Plugin Description** | AIデリバリ用プラグインを「中身ごと」起こすメタプラグイン。`generate-plugin.sh` / `validate-plugin.sh` をラップし、Notion 16 DB を引いて Skill / `<usecase>-architect.md` / references / DP を対話的に起稿する |
| **モジュール** | MOD-AID（AIデリバリ自身） |
| **Applicable Domains** | クロスドメイン（全プラグイン横断・全ドメイン共通） |
| **Dependent Modules** | なし（メタ層・他モジュールに依存しない） |
| **MVP スコープ** | (B) プラグイン丸ごとの実装支援（scaffold → architect 起稿 → 各フェーズ Skill 起稿 → references → DP 起票 → sample-case 紐付け → validate）まで。パイロット駆動（C）はバックログ |
| **Related Plugins** | `xtone-shared-plugin`（スキーマ共有, CONV-14・symlink） / `xtone-plugin-template`（骨格供給元） / `xtone-auth-plugin`（学習用リファレンス実装） |

`.claude-plugin/plugin.json` は Claude Code 標準フィールド（name / version / description / author）のみ。モジュール・適用ドメイン・依存などの Xtone メタデータは本表で管理する。

## 鉄則（ai-delivery 共通）

1. **実装の根拠は Notion。** コードに「なぜ」を書かず、ID（CONV- / SKL- / DP- / SCH- / TPL- 等）を参照する。
2. **判断ポイントは気づいたその場で記録。** 後でまとめない。未決は `docs/pending-decisions.md` と判断ポイントカタログDB（DP-XXX）へ。
3. **warn_and_document（T-002 本決定）。** CI / Hook / Subagent はすべて警告のみ・ブロックなし。
4. **スキーマは編集しない。** `schemas/` は xtone-shared-plugin への symlink（Single Source of Truth, CONV-14）。
5. **本プラグイン固有：** メタゆえに循環参照（自分自身を直す）が起きる。ADR-AID-001 に記録し、自己更新時は **必ずドッグフード（自プラグインを自分で再生成）** で検証する。

## このプラグインのフロー（Phase Skills）

通常の `/req-collect → /design → /implement` に加え、本プラグイン特化の `/aid-*` コマンド群を順に使う：

```
# 通常フェーズ
/req-collect                       新規プラグインの scope / モジュール / ドメインをヒアリングし plugin-scope.json を生成
/aid-skill-creator-design          メタ architect が必要 Skill / Subagent / Command / Hook / 横断機能候補を提示
/implement                         以下を順に実行

# 実装フェーズ（本プラグイン特化コマンド）
/aid-scaffold <usecase>            generate-plugin.sh をラップして骨格生成
/aid-architect-author <usecase>    <usecase>-architect.md を authentication-architect.md を参照に起稿
/aid-skill-new <phase> <skill>     対象プラグインに新 Skill を SKL-12 / SKL-20 準拠で追加
/aid-references-new <skill> <stack>  references/<stack>.md スキャフォールド
/aid-dp-register                   検出した未起票 DP を Notion DP DB に起票
/aid-sample-case-binding           sample-cases から symlink（B-21）
/aid-validation-runner             validate-plugin.sh を呼び、警告を pending-decisions.md に整形追記
```

補助コマンドは基盤共通：`/decide`（判断記録）/ `/status`（進捗）/ `/next`（次アクション）/ `/pending-list`（未決一覧）/ `/skip-review`（AIレビュー）。

### 想定ユースフロー（実プロンプト例：T-027 決済プラグインを立ち上げる）

```text
/req-collect                                       # 「決済モジュール、EC/D2C と LP で使う、Stripe・GMO 候補」
/aid-skill-creator-design                          # 必要 Skill: payment-design / payment-stripe-setup / payment-frontend ... を提示
/aid-scaffold payment --domain "決済" --domains "EC・D2C,イベントLP" --modules "MOD-007"
/aid-architect-author payment                      # payment-architect.md（DP比較表・差し替え可能設計）
/aid-skill-new design payment-design
/aid-references-new payment-design rails
/aid-references-new payment-design nextjs
/aid-skill-new implementation payment-stripe-setup
/aid-dp-register                                   # 未起票の DP を Notion に一括起票
/aid-sample-case-binding payment ec-d2c-app
/aid-sample-case-binding payment event-campaign-lp
/aid-validation-runner                             # 仕上げ
/status
```

## 既存資産との関係

| 既存資産 | 本プラグインの扱い |
|---|---|
| `ai-delivery/scripts/generate-plugin.sh` | **そのまま呼ぶ**。`/aid-scaffold` がコマンド組立を支援するラッパー |
| `ai-delivery/scripts/validate-plugin.sh` | **そのまま呼ぶ**。`/aid-validation-runner` が警告を `pending-decisions.md` に整形 |
| `xtone-plugin-template/` | **編集しない**。`generate-plugin.sh` 経由で参照される |
| `xtone-shared-plugin/schemas/v1/` | **symlink で参照**（CONV-14 厳守） |
| 16 Notion DB（TPL / SKL / CONV / DP / SCH / MCS / MCP / FLD / RULE / DPS / プロセス棚卸し / ドメインタクソノミー / 既存資産インベントリ / 品質ゲート・テンプレ / サンプル骨格 / 型化タスク） | **Notion MCP 必須で読む**。書き込みは DP DB の新規起票のみ（限定的）|
| `xtone-auth-plugin/`（リファレンス実装） | **学習用に常時参照**。`aid-architect-author` / `aid-references-new` が型を写し取る |

## 判断ポイント（CONV-07・人間判断をスルーさせない）

詳細は `docs/decision-points.md`、正は判断ポイントカタログDB（DP-）。本プラグイン固有の DP は `DP-AID-XX`（DP DB 起票時にプレフィックス衝突を確認）。

| DP | 判断ポイント | 既定の推奨 |
|---|---|---|
| **DP-AID-01** | 新規Skill追加時の境界判断（既存Skillの拡張 vs 新規独立Skill, B-19） | 2つ以上の層（client/backend/iaas）にまたがる場合は独立 Skill |
| **DP-AID-02** | DP 再利用 vs 新規DP起票（既存 DP-XXX に含まれるかの線引き） | DP DB を必ず検索し、80%以上重複なら既存再利用 |
| **DP-AID-03** | sample-case の選定（カタログから選ぶ vs 新案件追加PR） | まずカタログから2件選定。該当ゼロなら新案件 PR |
| **DP-AID-04** | 言語別 references を増やすタイミング（案件で必要時 vs 先回り） | 案件で必要になった時点で追加（先回りは型のドリフトを招く） |
| **DP-AID-05** | domain-architect の責務拡大判断（基盤 designer で十分 vs 特化が必要） | 2つ以上の比較対象スタックを持つドメインは特化を作る |

AI は勝手に決めず推奨だけ提示し、未決は `docs/pending-decisions.md` に残す（T-002 warn_and_document）。

> DP-AID-* は本プラグイン起稿時点では未起票（pending）。`/aid-dp-register` で本プラグイン自身に対してドッグフードを通し、DP DB に起票する。

## 構成

| ディレクトリ | 内容 |
|---|---|
| `agents/` | 7 Subagent（基盤6 + メタ特化 **aid-skill-creator-architect**） |
| `commands/` | 8 基盤 Command + `/aid-skill-creator-design` + `/aid-*`（scaffold / architect-author / skill-new / references-new / dp-register / sample-case-binding / validation-runner）|
| `hooks/` | hooks.json + 4 Hook（pre-phase-transition / post-decision-record / pre-pr-merge / post-pr-merge）|
| `skills/aid-skill-creator-plugin-guide/` | 本ガイド |
| `skills/requirements/` | `aid-plugin-scope-extraction` |
| `skills/design/` | `aid-plugin-architecture-design` / `aid-domain-architect-design` |
| `skills/implementation/` | `aid-plugin-scaffold` / `aid-skill-authoring` / `aid-references-authoring` / `aid-decision-point-registration` / `aid-sample-case-binding` / `aid-validation-runner` + 横断 `tech-version-check`（B-17 symlink） / `implementation-skill-planner`（B-18 symlink） |
| `skills/test/` | `aid-plugin-self-check`（メタテスト：本プラグイン自身の `--plugin-dir` 起動試験） |
| `schemas/` | xtone-shared-plugin への symlink（編集不可・CONV-14）|
| `docs/` | decision-points.md / usage-guide.md / pending-decisions.md / adr/（ADR-AID-NNN）|
| `sample-inputs/` | `existing/`（既存 auth プラグインを「改修対象案件」として symlink）+ `new-usecase-briefs/`（新規ユースケースのヒアリングメモ）|

## メタゆえの留意点（本プラグイン固有）

1. **循環参照に注意。** 本プラグインを使って本プラグインを直すと、壊れた状態で自身を再生成する事故が起こる。修正前に**現状の本プラグインで他プラグイン（例: auth）の再生成が通る**ことを必ず確認する（ADR-AID-001 で運用化予定）。
2. **Notion DP DB への書き込みは限定的に。** `aid-decision-point-registration` のみが書き込み権限を使い、他 Skill は読み取りのみ。誤起票を防ぐため**プレビュー → ユーザ確認 → 起票**の3段にする。
3. **`generate-plugin.sh` の出力命名**: usecase=`aid-skill-creator` → プラグイン名は `xtone-aid-skill-creator-plugin`（接尾辞 `-plugin` がスクリプトで自動付与）。本プラグイン自身もこの命名規約に従う。
4. **`<usecase>-architect.md` の起稿責任**は本プラグインが持つ（雛形のままにしない）。auth プラグインの `authentication-architect.md` を学習リファレンスとして、DP 比較表・差し替え可能設計まで埋める。

## 関連

- マスターテンプレ: `../../../xtone-plugin-template/`
- スキーマ共有元: `../../../xtone-shared-plugin/`
- リファレンス実装: `../../xtone-auth-plugin/`
- プラグイン開発者ガイド: `../../../docs/plugin-developer-guide.md`
- Notion DB 一覧: `../../../docs/notion-db-catalog.md`
- MCP 設定: `../../../docs/mcp-setup-guide.md`
