---
name: auth-plugin-guide
description: xtone-auth-plugin（認証モジュール MOD-001）の作業ガイド。このプラグインで認証の要件定義〜設計〜実装を進めるとき、鉄則・コマンドフロー・判断ポイント（DP-007/008/015）・構成の全体像を把握したいときに使う。Firebase Auth が MVP、IaaS 差し替え可能設計が前提。
---

# xtone-auth-plugin 作業ガイド

このプラグインは Xtone AIデリバリシステムの **認証（MOD-001）** ユースケースを担う。マスターテンプレ `xtone-plugin-template`（T-019）から生成し、認証特化の Subagent / Command / Skill を追加したもの（T-021）。プロジェクト全体のルールは リポジトリの `ai-delivery/CLAUDE.md` を参照。

> このプラグインの運用コンテキストは（ルート CLAUDE.md ではなく）本スキルに置く。Claude Code ではプラグインルートの CLAUDE.md は context として読み込まれないため（DP-27 本決定）。

## プラグイン概要（CONV-06 相当）

| 項目 | 値 |
|---|---|
| モジュール | MOD-001 認証（ユーザー認証・セッション管理） |
| 適用ドメイン | 全ドメイン共通 |
| MVP スコープ | Firebase Auth 1パターン（T-004 本決定）。他 IaaS は **差し替え可能な設計** を前提にスコープ外 |
| 依存プラグイン | xtone-shared-plugin（スキーマ共有, CONV-14） |

`.claude-plugin/plugin.json` は Claude Code 標準フィールド（name/version/description/author/keywords）のみ。モジュール・適用ドメイン・依存などの Xtone メタデータは本表で管理する。

## 鉄則（ai-delivery 共通）

1. **実装の根拠は Notion。** コードに「なぜ」を書かず、ID（CONV- / SKL- / DP- / SCH- 等）を参照する。
2. **判断ポイントは気づいたその場で記録。** 後でまとめない。未決は `docs/pending-decisions.md` と判断ポイントカタログDB（DP-XXX）へ。
3. **warn_and_document（T-002 本決定）。** CI / Hook / Subagent はすべて警告のみ・ブロックなし。
4. **スキーマは編集しない。** `schemas/` は xtone-shared-plugin への symlink（Single Source of Truth, CONV-14）。

## このプラグインのフロー

```
/req-collect → /design（認証は /auth-design）→ /implement
```

各フェーズで補助コマンドを使う: `/decide`（判断記録）/ `/status`（進捗）/ `/next`（次アクション）/ `/pending-list`（未決一覧）/ `/skip-review`（AIレビュー）。

認証設計では `/auth-design` を使うと **authentication-architect** Subagent が起動し、認証スタックを複数提示したうえで Firebase Auth を MVP 推奨として根拠を示す（最終決定は人間）。

## 判断ポイント（CONV-07・人間判断をスルーさせない）

詳細・選択肢・誤判断リスクは [`docs/decision-points.md`](../../docs/decision-points.md)、正は判断ポイントカタログDB（DP-）。

| DP | 判断ポイント | 既定の推奨（MVP） |
|---|---|---|
| **DP-007** | 認証スタック選択（Firebase Auth / Devise+OmniAuth / Cognito / dAccount / NextAuth.js / Laravel Sanctum） | Firebase Auth（差し替え可能設計を維持） |
| **DP-008** | MFA（多要素認証）要件の振り分け（全員必須 / 管理者のみ / オプトイン / 不要） | 案件のセキュリティ要件で決定（既定なし） |
| **DP-015** | dAccount 要件の適用範囲・docomo 規約遵守チェックのタイミング | docomo 系案件のみ適用（非該当案件はスコープ外） |

AI はこれらを **勝手に決めず推奨だけ提示**し、未決は `undecided`（各スキーマ）と `docs/pending-decisions.md` に残す。

> DP-008 で MFA 方針が決まったら、実装は専用スキル `firebase-auth-mfa`（TOTP/SMS の登録・追加認証＝client、クレーム検証・管理者強制・失効＝backend）に従う。

> **ローカル検証**（実 Firebase 無しで E2E）は `firebase-auth-emulator` を使う。Docker で Auth Emulator を起動し、署名検証スキップ・`connectAuthEmulator`・SMS MFA で E2E まで可能。**TOTP はエミュレーター非対応**のため、TOTP の E2E は実 Identity Platform で行う前提を案件 ADR に明記する。

## 構成

| ディレクトリ | 内容 |
|---|---|
| `agents/` | 7 Subagent（基盤6 + 認証特化 **authentication-architect**） |
| `commands/` | 9 Slash Command（基盤8 + 認証特化 **auth-design**） |
| `hooks/` | hooks.json + 4 Hook（pre-phase-transition / post-decision-record / pre-pr-merge / post-pr-merge） |
| `skills/` | フェーズ別 Skill（requirements / design / implementation 実動、test スタブ）+ 本ガイド（auth-plugin-guide） |
| `schemas/` | xtone-shared-plugin への symlink（編集不可） |
| `docs/` | decision-points.md / usage-guide.md / pending-decisions.md / adr/ |
| `sample-inputs/`, `sample-outputs/` | 架空案件の作り込み例（要件→設計→実装の通し検証） |

## 関連

- 使い方ガイド: [`docs/usage-guide.md`](../../docs/usage-guide.md)
- スキーマ共有元: `../../../xtone-shared-plugin/`
- マスターテンプレ: `../../../xtone-plugin-template/`
