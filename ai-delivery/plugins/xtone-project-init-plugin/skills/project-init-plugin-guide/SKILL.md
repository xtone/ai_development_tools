---
name: project-init-plugin-guide
description: xtone-project-init-plugin（案件初期化メタプラグイン・T-051）の作業ガイド。実案件を立ち上げる際に、/project-* 横断コマンドのフロー・土台セットアップ（モノレポ/フロント/バック/ローカル基盤）・スタック選択制・判断ポイント（DP-PINIT-*）・構成の全体像を把握したいときに使う。土台は project-init が完結し機能は各モジュールが上に載せる（DP-PINIT-11 境界）。
---

# xtone-project-init-plugin 作業ガイド

このプラグインは Xtone AIデリバリシステムの **案件初期化（プロジェクトブートストラップ）** を担う独立メタプラグイン（T-051）。`xtone-aid-skill-creator-plugin`（プラグインを「作る」側メタ）と対称の「案件を「立ち上げる」側メタ」。マスターテンプレ `xtone-plugin-template`（T-019）から生成。プロジェクト全体のルールはリポジトリの `ai-delivery/CLAUDE.md` を参照。

> 運用 context は（ルート CLAUDE.md ではなく）本スキルに置く。Claude Code ではプラグインルートの `CLAUDE.md` は project context として読み込まれず `--strict` で警告になるため（DP-27 本決定 / CONV-06）。人間向けの概要は `README.md` に置く（任意）。

## プラグイン概要（CONV-06）

CONV-06 の6項目をここに記載する（Plugin Description / Applicable Domains / Dependent Modules / Phase Skills / Decision Points / Related Plugins）。

| 項目 | 値 |
|---|---|
| モジュール | 横断メタ（特定 MOD 非依存） |
| 適用ドメイン | 全ドメイン共通（T-008 ドメインタクソノミー） |
| 依存モジュール | なし（横断メタプラグイン） |
| 依存プラグイン | xtone-shared-plugin（スキーマ共有, CONV-14）／各モジュールプラグイン（ロード対象） |
| 境界（DP-PINIT-11） | **土台＝project-init**（モノレポ＋フロント/バック雛形＋共有設定＋ローカル基盤）／**機能＝各モジュール**が土台の上に載せる |

`.claude-plugin/plugin.json` は Claude Code 標準フィールド（name/version/description/author/keywords）のみに絞る。モジュール・適用ドメイン・依存などの Xtone メタデータは本表で管理する。

## 鉄則（ai-delivery 共通）

1. **実装の根拠は Notion。** コードに「なぜ」を書かず、ID（CONV- / SKL- / DP- / SCH- 等）を参照する。
2. **判断ポイントは気づいたその場で記録。** 後でまとめない。未決は `docs/pending-decisions.md` と判断ポイントカタログDB（DP-XXX）へ。
3. **warn_and_document（T-002 本決定）。** CI / Hook / Subagent はすべて警告のみ・ブロックなし。
4. **スキーマは編集しない。** `schemas/` は xtone-shared-plugin への symlink（Single Source of Truth, CONV-14）。

## このプラグインのフロー（案件横断 /project-* 群）

```
/project-init        案件のドメイン・規模・制約をヒアリング → project-scope.json 生成
/project-modules     必要モジュール候補を MCS/タクソノミーから提示（module-advisor・人間確定）
/project-scaffold    スタック選択（最新版併記・tech-version-check）→ 土台セットアップ（モノレポ/フロント/バック/ローカル基盤）→ delivery 横断索引初期化
/project-load-guide  選定モジュールプラグインのロード手順・共存設定を出力（should）
/project-status      案件全体（複数モジュール横断）の進捗・未決を集約表示（should）
```

- 補助コマンドは基盤共通: `/decide` `/status` `/next` `/pending-list` `/skip-review`。
- 以降、各モジュールは `/<plugin>:<command>` 名前空間で進める（DP-PINIT-03。本プラグインは衝突回避機構を持たない薄い層）。
- **スタックは選択制**（DP-PINIT-09 / ADR-PINIT-003）: サポート済み（初期 Rails/Next.js/docker-compose/モノレポ方式）から候補提示・人間確定。バージョンは tech-version-check で最新安定版を提示（固定は人間判断）。新スタックは references 追加で拡張（契約不変）。

### Skill 構成（フェーズ別）

| フェーズ | Skill | 役割 |
|---|---|---|
| requirements | `project-scope-extraction` | /project-init のヒアリング |
| design | `project-module-recommendation` / `project-stack-select` | モジュール推奨 / スタック選択（最新版併記） |
| implementation | `project-scaffold`（統合）/ `project-monorepo-scaffold` / `project-frontend-init` / `project-backend-init` / `project-local-infra` / `project-load-guide` | 土台セットアップ・横断索引・ロード手順 |
| test | `project-status-aggregation` | 横断ステータス集約 |

> setup 系の言語別レシピは `references/<stack>.md`（初期は nextjs/rails/hotwire/docker-compose/turborepo-pnpm/rails-js-hybrid/nx のスタブ。本実装は `/aid-references-new`・DP-AID-04 需要ドリブン）。

## 判断ポイント（CONV-07・人間判断をスルーさせない）

判断ポイント（DP-PINIT-01〜11）は `docs/decision-points.md` と判断ポイントカタログDB（DP-）で管理し、DP-ID と Notion URL を保持する（CONV-07）。**DP-PINIT-01〜11 はすべて accepted**（2026-06-01）。AI は勝手に決めず推奨だけ提示し、未決は各スキーマの `undecided` と `docs/pending-decisions.md` に残す（T-002 warn_and_document）。

## 構成

| ディレクトリ | 内容 |
|---|---|
| `agents/` | Subagent（基盤6 ＋ ユースケース特化を追加可能） |
| `commands/` | Slash Command（基盤8 ＋ ユースケース特化を追加可能） |
| `hooks/` | hooks.json ＋ 4 Hook（warn_and_document） |
| `skills/` | 本ガイド（project-init-plugin-guide）＋ フェーズ別 Skill |
| `schemas/` | xtone-shared-plugin への symlink（編集不可, CONV-14） |
| `docs/` | decision-points / pending-decisions / adr |

## 関連プラグイン（Related Plugins）

- **xtone-shared-plugin** — スキーマ共有（symlink 参照元）
