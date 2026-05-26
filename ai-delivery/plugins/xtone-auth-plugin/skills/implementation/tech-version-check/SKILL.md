---
name: tech-version-check
description: 採用予定の言語/FW/主要ライブラリの **最新安定版と相互互換性** を実装着手の前に取得・記録するスキル。実装フェーズで firebase-auth-setup / firebase-auth-frontend / firebase-auth-mfa / firebase-auth-emulator を呼ぶ前の前提作業として、context7（または WebFetch / WebSearch fallback）で公式情報を引き、`delivery/version-matrix.md` にバージョン採用根拠と既知の非互換性を残す。バージョン固定はせず公式最新を採る方針（`docs/environment-setup.md`）の実行スキル。
---

# Tech Version Check Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

実装着手の前に、`design.yaml.architecture.stack` に列挙された採用スタック（言語 / FW / 主要ライブラリ）について **公式の最新安定版とフレームワーク要求の最小言語バージョン**を取得し、`delivery/version-matrix.md` に採用根拠と日付を残す。

サンプル案件 sample-auth で **Ruby/Rails の最新版確認が事前に行われず**、`connection_pool 3.0.2` が Ruby 3.3 非互換に当たって途中で気づく事故が発生した（B-11）。本スキルはこの種の事故を未然に塞ぐ。

> 方針: バージョンは固定しない（陳腐化回避）、基本は公式の最新安定版、特定バージョンが必要な場合は判断ポイント — [`ai-delivery/docs/environment-setup.md`](../../../../../docs/environment-setup.md)。本スキルはその「公式最新を取得する」手順の実体。

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
5. 非互換が発覚した場合は判断ポイント化（pending-decisions に「採用バージョンを下げるか / 互換ライブラリを変えるか」を起票）。
6. 取得情報を `implementation-plan.json.skill_plan` の本エントリ `called=true` に更新。

## 出力テンプレ（version-matrix.md）

```markdown
# 採用バージョン記録（tech-version-check / B-11）

- 作成日: 2026-05-26
- 案件: <project>
- design.yaml.architecture.stack: <quoted>

## 言語ランタイム
| 名前 | 採用バージョン | 公式最新 | 要求 | 根拠 URL |
|---|---|---|---|---|
| Ruby | 3.x.x (採用時点の最新安定版) | 3.x.x | — | https://www.ruby-lang.org/en/downloads/ |

## メイン FW
| 名前 | 採用 | 公式最新 | 要求ランタイム | 根拠 URL |
|---|---|---|---|---|
| Rails | 8.x.x | 8.x.x | Ruby 3.x+ | https://rubygems.org/gems/rails |

## 主要ライブラリ・SDK
| 名前 | 採用 | 公式最新 | 要求 | 根拠 URL |
|---|---|---|---|---|
| firebase (JS) | 9.x+ (modular) | 11.x.x | Node 18+ | https://www.npmjs.com/package/firebase |
| jwt (gem) | 3.x | 3.x | Ruby 3.x+ | https://rubygems.org/gems/jwt |

## ツール / コンテナ
| 名前 | 採用 | 公式最新 | 用途 | 根拠 URL |
|---|---|---|---|---|
| firebase-tools | 14.x | 14.x | Emulator (B-12) | https://github.com/firebase/firebase-tools/releases |
| node (base image) | 22-slim | 22.x | Emulator container | https://hub.docker.com/_/node |

## 既知の非互換性 / 警戒事項
- _(取得時点で問題があれば 1 行ずつ記録)_

## 採用根拠の要約
- 「公式の最新安定版」方針（environment-setup.md）に従い、`<確認日>` 時点で context7 / 公式リリースで取得した最新を採用。
- 特定バージョン固定が必要な要件は受け取っていない。
```

## 判断ポイント（人間判断をスルーさせない）

- **特定バージョン固定の要望**: クライアント制約・レガシー互換などで「最新ではない特定バージョン」を要求された場合、`docs/pending-decisions.md` に DP として起票し、確認後に固定する（AI が勝手に古いバージョンを採らない）。
- **非互換性の解消方針**: 採用最新版に既知の非互換性がある場合、代替ライブラリへの差し替えか採用バージョンの一時的な前進版採用かの選択。pending-decisions に起票。
- **取得粒度**: 全依存をスキャンするか / 主要依存のみに留めるか。プロジェクトのリスク許容度で人間が決める。

## 関連スキル

- 後続: `firebase-auth-setup` / `firebase-auth-frontend` / `firebase-auth-mfa` / `firebase-auth-emulator`（本スキルの version-matrix.md に従って Gemfile / package.json / Dockerfile を埋める）
- バージョン方針: [`ai-delivery/docs/environment-setup.md`](../../../../../docs/environment-setup.md)
- 横展開: 本スキルは現状 xtone-auth-plugin 内に配置するが、本来は **横断スキル**（複数プラグインで共通利用）。`xtone-shared-plugin` / `xtone-plugin-template` への移管は別 Issue。
