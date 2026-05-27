# 訂正バックログ（T-022 パイロット由来）

T-022 内部パイロット（[pilot-report.md](./pilot-report.md)）で発見した、型化の各レイヤー（Foundation / Modeling / Architecture / Tooling）への訂正タスク。

> **Rollout 判定**:
> - 2026-05-25 / 豊田 = **No-go**（High 4 件解消が条件）
> - **2026-05-26 / 豊田 = Go**（再判定）— High 4 件（B-01/B-02/B-05/B-06）すべて CLOSED、[T-021 再パイロット](./re-pilot-report.md) で訂正の効果を実機実証、新発見 RN-1/2/3 も PR #143-#149 で解消。**T-023〜の Rollout に進む**。
> - 残 **B-07 / B-09**（Med / Low）は **Rollout 並行**で順次対応（B-08 は DP-28 として正式起票で CLOSED）。

| ID | Issue | レイヤー | 優先度 | タスク | 関連 | 発見 |
|---|---|---|---|---|---|---|
| **B-01** | [#126](https://github.com/xtone/ai_development_tools/issues/126) | Modeling | High | I/O 契約スキーマ（requirements/design/implementation-plan）の **本実装**。現状スタブで検証が効かない。design の data_model/api_design 等を schema 化 | T-011〜013 / FLD- | F-2 |
| **B-02** | [#127](https://github.com/xtone/ai_development_tools/issues/127) | Architecture | High | `firebase-auth-setup` スキルに **運用詳細の節を追加**: Admin SDK（サービスアカウント鍵）による退会時ユーザー削除、公開鍵（証明書）キャッシュ、トークン失効/リフレッシュ | SCH- / SKL- | F-3 |
| **B-05** | [#128](https://github.com/xtone/ai_development_tools/issues/128) | Architecture / 規約 | High | **CONV-06 改訂**（プラグイン必須 CLAUDE.md → 運用 context は skill、人間向け README 任意）＋ テンプレ `CLAUDE.md.template` → plugin-guide skill 化（generate-plugin.sh / TPL-26 実装時） | DP-27 / CONV-06 / T-019 | F-9 |
| **B-06** | [#129](https://github.com/xtone/ai_development_tools/issues/129) | Foundation / Docs | High | **実行環境前提の明文化**: 想定 Ruby/Rails バージョン（Rails 8 = Ruby 3.1+）、rbenv 等のセットアップ手順を usage-guide / テンプレに追加。想定環境の Ruby 2.6 では Rails が動かない | T-019 / usage-guide | F-1 |
| **B-03** | [#130](https://github.com/xtone/ai_development_tools/issues/130) | Architecture | Med | `design` テンプレ（auth-section.template / design.schema）に **「責務（バックエンド/クライアント）」の仕分け**列を追加。パスワード変更等が Firebase クライアント側で完結する点を明示 | SKL- / FLD- | F-4 |
| ~~**B-04**~~ ✅ | [#131](https://github.com/xtone/ai_development_tools/issues/131) | Architecture | Med | ~~**MFA（DP-008）実装ガイド**を `firebase-auth-setup` か新スキルに追加（TOTP/SMS、管理者必須・一般オプトインの実装パターン）~~ → **新スキル `firebase-auth-mfa` を新設**（client=登録/追加認証 / backend=検証・管理者強制・失効 / iaas=第2要素検証、references: rails/hotwire/nextjs） | SCH- / DP-008 | F-5 |
| **B-07** | [#132](https://github.com/xtone/ai_development_tools/issues/132) | Tooling | Med | `validate-plugin.sh`（TPL-27）/ `generate-plugin.sh`（TPL-26）の整備。delivery 成果物の **スキーマ検証**を自動化 | TPL-26/27 | F-6 |
| ~~**B-08**~~ ✅ | [#133](https://github.com/xtone/ai_development_tools/issues/133) | Decision | Low | ~~新規 DP「**退会済みアカウントの再登録ポリシー**」を判断ポイントカタログに起票（本実装は 403 拒否で仮対応）。pending-decisions に起票済み~~ → **[DP-28](https://www.notion.so/36dceb782fa381ee9134d4f7321f8ba9) として正式起票**。選択肢 (A) 拒否 / (B) 復活 / (C) 新規作成 / (D) クールダウン、MVP 既定推奨は (A) 拒否。状態は `undecided`（案件適用時に `decision_record` 記録） | DP-28 | F-7 |
| **B-09** | [#134](https://github.com/xtone/ai_development_tools/issues/134) | Plugin（任意） | Low | **言語別の実装テンプレ**（例: Rails 向け AuthAdapter コード雛形）をスキルに同梱し実装を加速 | SKL- | F-8 |
| **B-10** | [#141](https://github.com/xtone/ai_development_tools/issues/141) | Architecture | Med | **フロントエンド認証実装スキル新設**（`firebase-auth-frontend` ＋ hotwire/nextjs レシピ）。#130 で責務分類した `client` 側の実装ガイドが欠落（firebase-auth-setup は backend 専用）。セッション戦略は判断ポイント扱い | SKL- / #130 | #130 レビュー後 |
| **B-13** | [#153](https://github.com/xtone/ai_development_tools/issues/153) | Architecture | High | **実装フェーズに skill_plan 生成を強制**。`implementation-skill-planner` スキル新設＋ `design.schema.page_access_control` / `local_dev_stack` 追加＋ `implementation-plan.schema.skill_plan` 追加（**required かつ minItems=1**。MVP 期は CONV-14 並行保持を厳格適用せず最新スキーマで型化を強制 / DP-MVP-COMPAT）。frontend / emulator スキル呼び出し漏れ防止 | SKL- / FLD- | サンプル案件 sample-auth |
| **B-14** | [#155](https://github.com/xtone/ai_development_tools/issues/155) | Documentation | Med | **`sample-outputs/` を 1 から再生成**。B-13 で削除（古いサンプルが新スキーマと不整合のため）。B-11〜B-14 一連のサンプル案件由来型化修正が完了したタイミングで、新スキーマ（page_access_control / local_dev_stack / skill_plan）と新スキル群（implementation-skill-planner 等）に沿った成果物を再構築 | SKL- / FLD- | PR #154 レビュー（豊田）|
| **B-11** | [#156](https://github.com/xtone/ai_development_tools/issues/156) | Tooling | High | **`tech-version-check` スキル新設**。context7 / WebFetch で公式最新安定版・互換性を事前取得し `delivery/version-matrix.md` に記録。Ruby/Rails 等の非互換に途中で当たる事故を防止 | SKL- / TPL- | sample-auth |
| **B-12** | [#157](https://github.com/xtone/ai_development_tools/issues/157) | Architecture | High | **Firebase Emulator + Docker をローカル開発の既定化**。B-13 で schema 側 `local_dev_stack` は導入済み。本件は **スキル中身**（docker-compose テンプレ / Adapter 分岐 / connectAuthEmulator 統合）を整備。B-14 の前提 | SKL- | sample-auth |
| **B-15** | [#158](https://github.com/xtone/ai_development_tools/issues/158) | Architecture | Med | **`auth-e2e-verify` スキル新設**。Playwright で `representative_use_cases` を全件通すまで責務化。`alert()` 禁止 等の MCP/Headless 配慮も込み。前提: B-12 | SKL- | sample-auth |
| **B-16** | [#159](https://github.com/xtone/ai_development_tools/issues/159) | Plugin | Low | hotwire レシピ細部修正（Rails singular resource / `alert()` 禁止 / Firebase v9 modular 統一） | SKL- | sample-auth |
| **B-17** | [#164](https://github.com/xtone/ai_development_tools/issues/164) | Architecture | Med | **`tech-version-check` を横断スキル化**。`xtone-shared-plugin` / `xtone-plugin-template` への移管（配置先は判断ポイント）。B-11 で auth-plugin 内に暫定配置したため、複数プラグイン展開時に複製が発生する | SKL- / CONV-14 | PR #162（B-11）|

## 優先度の考え方

- **High（Rollout 前に解消推奨）**: B-01 / B-02 / B-05 / B-06。いずれも「型の穴」で、24 ユースケース展開で繰り返しコスト化する。
- **Med（Rollout と並行可）**: B-03 / B-04 / B-07 / B-10 / B-14 / B-15 / B-17。
- **Low（任意・改善）**: ~~B-08~~ ✅（DP-28 で起票済） / B-09 / B-16。
- **Rollout 後追加 High**（24 ユースケース展開と並行で塞ぐ）: B-11（バージョン取得）/ B-12（Emulator 既定化）/ B-13（スキル呼び出し計画）。いずれもサンプル案件 sample-auth 由来。

## 次アクション

1. 豊田さんが本バックログをレビューし、Issue 化対象・優先度を選別。
2. 選別後、`xtone/ai_development_tools` に GitHub Issue として起票（ラベル: `type-ification`, レイヤー別）。
3. High 項目の解消を Rollout（T-023〜）着手の前提条件とするか判断。
