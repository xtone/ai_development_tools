---
name: project-stack-select
description: 案件の土台技術スタックを「サポート済みスタックのレジストリから候補提示→人間確定」で選定するスキル。design フェーズ（/project-scaffold の土台セットアップ直前）で、project-scope.json のドメイン・規模・制約をもとに monorepo / frontend / backend / local_infra の各レイヤーの推奨を提示し、ユーザーが確定したスタックを project-scope.json に保持したいときに使う。初期サポートは Rails / Next.js / docker-compose、拡張は references 追加のみ（契約不変・DP-PINIT-09 / ADR-PINIT-003）。
---

# Project Stack Select Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

実案件の土台で使う技術スタックを **「サポート済みスタックの中から AI が候補を提示し、人間が確定する」** 選択制で決める（DP-PINIT-09 accepted / ADR-PINIT-003）。AI は案件タイプに応じた推奨を出すのみで、確定は人間が行う（DP-PINIT-02 と同型・warn_and_document）。**候補提示の際は、各フレームワーク/言語の最新安定版を `tech-version-check`（B-17）で取得して併せて提示する**（バージョンを把握したうえで人間が選べるようにする）。

## 前提（バージョン取得・tech-version-check / B-17 連携）

候補提示の前に、横断スキル `tech-version-check`（`skills/implementation/tech-version-check/`・symlink）を呼び、**候補スタックの言語/FW の公式最新安定版・要求ランタイム・既知の非互換**を取得して `delivery/version-matrix.md` に記録する。

- 取得手段は tech-version-check の規定（context7 → WebFetch → WebSearch）に従う。根拠 URL を必ず残す。
- `version-matrix.md` が既存かつ fresh（プロジェクト基準内・例 30 日以内）なら再取得を skip 可（B-13）。
- **バージョンは固定しない**（env-setup 方針）。既定は「公式最新安定版」を提示。特定バージョン固定が要るときは判断ポイント（後述）。
- ここで作成した `version-matrix.md` は、後続の setup 系実装 Skill（`project-monorepo-scaffold` / `project-frontend-init` / `project-backend-init` / `project-local-infra`）が再利用する（fresh なら再チェック不要）。

## 入出力（スキーマ）

- 入力: `schemas/v1/project-scope.schema.json`（`domain` / `scale` / `constraints` / `selected_modules`）＋ `tech-version-check` の `delivery/version-matrix.md`
- 出力:
  - 同 `project-scope.json` の `stack` を更新（各レイヤー `{choice, status, rationale, version, runtime_required, version_source}`）。`status` は `recommended`（AI推奨）→ 人間確定で `confirmed`。`version` は tech-version-check で取得した最新安定版（採用日時点）。
  - `delivery/version-matrix.md`（採用候補のバージョン採用根拠）
- スキーマは編集しない（`schemas/` は xtone-shared-plugin への symlink, CONV-14）。

## サポート済みスタックレジストリ（references = レジストリ）

「サポート済み」は setup 系 Skill の `references/<stack>.md` の有無で表す。新スタック追加は references を1枚足すだけ（契約不変）。

| レイヤー | 初期ロールアウト（references あり） | 将来拡張（references を追加） |
|---|---|---|
| monorepo | `turborepo-pnpm` / `rails-js-hybrid` / `nx` | 追加方式 |
| frontend | `nextjs` | `vuejs` ほか |
| backend | `rails` / `hotwire` | `express` / `hono`（TS）/ `aws-managed` |
| local_infra | `docker-compose` | クラウド直結ほか |
| native（将来） | （なし） | `swift` / `kotlin` |
| multiplatform（将来） | （なし） | `flutter` |

> 将来スタックは DP-AID-04 に従い、案件で必要になった時点で `/aid-references-new` でレシピを追加する（先回りで全部作らない）。

## 手順

1. `project-scope.json` の `domain` / `scale` / `constraints` を読む。
2. **`tech-version-check` を呼び**、候補スタックの言語/FW の最新安定版・要求ランタイム・既知の非互換を取得して `delivery/version-matrix.md` に記録する（fresh なら skip 可）。
3. 各レイヤーについて**サポート済みスタックから候補を提示**し、案件タイプに応じた既定推奨を**取得した最新バージョンと併せて**添える:
   - モノレポ方式（DP-PINIT-08）: JS 重心 → `turborepo-pnpm` / Rails 重心 → `rails-js-hybrid` / 大規模 → `nx`。**要件で別指定があれば要件優先**。
   - frontend: 既定 `nextjs`（例: 提示時に「Next.js <最新版> / Node <Active LTS>」を併記）。backend: 既定 `rails`（SSR/管理画面中心なら `hotwire` を併記。「Rails <最新版> / Ruby <要求最小以上の最新>」）。local_infra: 既定 `docker-compose`（DB イメージ版を併記）。
   - 提示はあくまで候補＋推奨＋最新バージョン情報。**選択も固定も人間が決める**。
4. 各候補を `status: "recommended"`・`version`（最新安定版）・`runtime_required`・`version_source`（根拠 URL）付きで `project-scope.json.stack` に書き、**人間に確定を仰ぐ**（AI は決めない）。
5. 人間が選んだものを `status: "confirmed"` に更新。未確定のレイヤーは warn_and_document で残す。
6. 確定スタック（と version-matrix.md）を後続 setup 系 Skill（`project-monorepo-scaffold` / `project-frontend-init` / `project-backend-init` / `project-local-infra`）が参照する。

## 差し替え可能設計（拡張ポイント・T-004 適応）

スタックは references で表現される。プラグイン本体（契約・project-scope のスタック項目）は言語非依存に保つため、未サポートのスタックを要求されても **references を追加するだけ**で対応でき、契約改変は不要。

## 判断ポイント（人間判断をスルーさせない）

- **DP-PINIT-09**（スタック選択制）: AI は候補提示のみ・確定は人間。既定推奨を画一固定しない。
- **DP-PINIT-08**（モノレポ方式）: 案件ごと選択。単一固定しない。
- **バージョン固定（env-setup 方針）**: 既定は tech-version-check で取得した**最新安定版**を提示する。クライアント制約・レガシー互換などで特定バージョン固定が要る場合は、AI が勝手に古いバージョンを採らず `docs/pending-decisions.md` に DP として起票し人間が確定する。
- **既知の非互換**: tech-version-check が最新版に非互換を検出した場合（要求ランタイム不一致・間接依存の制約等）は、採用バージョン調整 or 代替の判断を pending-decisions に起票する。
- 未サポートのスタックを案件が要求した場合は、勝手に近いもので代替せず、未決として `docs/pending-decisions.md` に記録し references 追加（`/aid-references-new`）を提案する（warn_and_document）。

## responsibility_split

| 項目 | owner |
|---|---|
| スタック候補提示・選択結果の project-scope 保持（オーケストレーション） | shared |
