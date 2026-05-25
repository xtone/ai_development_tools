# 訂正バックログ（T-022 パイロット由来）

T-022 内部パイロット（[pilot-report.md](./pilot-report.md)）で発見した、型化の各レイヤー（Foundation / Modeling / Architecture / Tooling）への訂正タスク。

> **Rollout 判定（2026-05-25 / 豊田）**: **No-go**。本バックログ（特に High 項目）を解消するまで Rollout（T-023〜）には進まない。全9件を GitHub Issue 化済み（下表参照）。

| ID | Issue | レイヤー | 優先度 | タスク | 関連 | 発見 |
|---|---|---|---|---|---|---|
| **B-01** | [#126](https://github.com/xtone/ai_development_tools/issues/126) | Modeling | High | I/O 契約スキーマ（requirements/design/implementation-plan）の **本実装**。現状スタブで検証が効かない。design の data_model/api_design 等を schema 化 | T-011〜013 / FLD- | F-2 |
| **B-02** | [#127](https://github.com/xtone/ai_development_tools/issues/127) | Architecture | High | `firebase-auth-setup` スキルに **運用詳細の節を追加**: Admin SDK（サービスアカウント鍵）による退会時ユーザー削除、公開鍵（証明書）キャッシュ、トークン失効/リフレッシュ | SCH- / SKL- | F-3 |
| **B-05** | [#128](https://github.com/xtone/ai_development_tools/issues/128) | Architecture / 規約 | High | **CONV-06 改訂**（プラグイン必須 CLAUDE.md → 運用 context は skill、人間向け README 任意）＋ テンプレ `CLAUDE.md.template` → plugin-guide skill 化（generate-plugin.sh / TPL-26 実装時） | DP-27 / CONV-06 / T-019 | F-9 |
| **B-06** | [#129](https://github.com/xtone/ai_development_tools/issues/129) | Foundation / Docs | High | **実行環境前提の明文化**: 想定 Ruby/Rails バージョン（Rails 8 = Ruby 3.1+）、rbenv 等のセットアップ手順を usage-guide / テンプレに追加。想定環境の Ruby 2.6 では Rails が動かない | T-019 / usage-guide | F-1 |
| **B-03** | [#130](https://github.com/xtone/ai_development_tools/issues/130) | Architecture | Med | `design` テンプレ（auth-section.template / design.schema）に **「責務（バックエンド/クライアント）」の仕分け**列を追加。パスワード変更等が Firebase クライアント側で完結する点を明示 | SKL- / FLD- | F-4 |
| **B-04** | [#131](https://github.com/xtone/ai_development_tools/issues/131) | Architecture | Med | **MFA（DP-008）実装ガイド**を `firebase-auth-setup` か新スキルに追加（TOTP/SMS、管理者必須・一般オプトインの実装パターン） | SCH- / DP-008 | F-5 |
| **B-07** | [#132](https://github.com/xtone/ai_development_tools/issues/132) | Tooling | Med | `validate-plugin.sh`（TPL-27）/ `generate-plugin.sh`（TPL-26）の整備。delivery 成果物の **スキーマ検証**を自動化 | TPL-26/27 | F-6 |
| **B-08** | [#133](https://github.com/xtone/ai_development_tools/issues/133) | Decision | Low | 新規 DP「**退会済みアカウントの再登録ポリシー**」を判断ポイントカタログに起票（本実装は 403 拒否で仮対応）。pending-decisions に起票済み | DP（新規候補）| F-7 |
| **B-09** | [#134](https://github.com/xtone/ai_development_tools/issues/134) | Plugin（任意） | Low | **言語別の実装テンプレ**（例: Rails 向け AuthAdapter コード雛形）をスキルに同梱し実装を加速 | SKL- | F-8 |
| **B-10** | [#141](https://github.com/xtone/ai_development_tools/issues/141) | Architecture | Med | **フロントエンド認証実装スキル新設**（`firebase-auth-frontend` ＋ hotwire/nextjs レシピ）。#130 で責務分類した `client` 側の実装ガイドが欠落（firebase-auth-setup は backend 専用）。セッション戦略は判断ポイント扱い | SKL- / #130 | #130 レビュー後 |

## 優先度の考え方

- **High（Rollout 前に解消推奨）**: B-01 / B-02 / B-05 / B-06。いずれも「型の穴」で、24 ユースケース展開で繰り返しコスト化する。
- **Med（Rollout と並行可）**: B-03 / B-04 / B-07。
- **Low（任意・改善）**: B-08 / B-09。

## 次アクション

1. 豊田さんが本バックログをレビューし、Issue 化対象・優先度を選別。
2. 選別後、`xtone/ai_development_tools` に GitHub Issue として起票（ラベル: `type-ification`, レイヤー別）。
3. High 項目の解消を Rollout（T-023〜）着手の前提条件とするか判断。
