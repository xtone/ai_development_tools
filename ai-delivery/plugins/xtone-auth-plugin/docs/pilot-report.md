# 内部パイロット報告書（T-022）— xtone-auth-plugin

- **対象プラグイン**: xtone-auth-plugin（T-021）
- **パイロット案件**: 架空案件「みんなの読書会」（BtoC コミュニティ、Web+アプリ）
- **実施日**: 2026-05-25
- **実施者**: Claude（ドッグフード実行）／**判定者**: 豊田（T-005）
- **サンプルアプリ**: `~/RubymineProjects/t-021-sample/`（Rails 8.1 API / Ruby 3.3.6 / SQLite / JWT）

> 本報告書は **たたき台**です。DoD の「パイロット担当者・オブザーバーのフィードバック収集」「Rollout 推進可否の関係者合意」は、本書をもとに豊田さんが最終判断します。

## 1. 実施サマリ

`xtone-auth-plugin` を実際に使い、架空案件を **要件定義 → 設計 → 実装** まで通した。プラグインの delivery 成果物（requirements / design / implementation-plan / ADR）を設計図として、Rails 8 の認証バックエンドを実装し、動作を検証した。

### 実施フロー
1. **要件定義**: `auth-requirements-extraction` スキルのチェックリストで認証要件を抽出 → `delivery/requirements.json`
2. **設計**: `authentication-architect` / `firebase-auth-design` で DP-007/008/015 を比較・決定 → `delivery/design.yaml` + `ADR-001`
3. **実装**: `firebase-auth-setup` スキルに沿って AuthAdapter 層・JWT 検証・User・コントローラを実装

### 検証結果（実測）
| 項目 | 結果 |
|---|---|
| `bin/rails test` | **8 runs / 20 assertions / 0 failures / 0 errors** ✅ |
| `bin/rails zeitwerk:check` | **All is good!**（本番 eager-load 健全）✅ |
| DP-007 差し替え実証 | `AUTH_ADAPTER=test` で `Auth::TestAdapter` に切替・検証成功。dev 既定（firebase）は `FIREBASE_PROJECT_ID` 未設定で安全に例外 ✅ |
| 認証フロー | セッション確立 / OIDC＋アカウント連携（provider マージ）/ 退会＋退会後再ログイン拒否(403) を結合テストで確認 ✅ |

**MVP 撤退基準（サンプルアプリ実装失敗）には該当しない**（実装成功・全テスト通過）。

## 2. 成功事例（プラグインが効いた点）

1. **フローの一貫性**: requirements → design → implementation-plan の I/O が素直につながり、delivery 成果物がそのまま実装の設計図になった。手戻りなく実装着手できた。
2. **DP-007 差し替え可能設計が実機能**: `AuthAdapter` 抽象化により、テストは実 Firebase 無しで成立（`TestAdapter`）。本番は `FirebaseAdapter`。ENV 切替が実際に動作し、「IaaS 差し替え可能」（T-004 本決定）をコードで実証できた。
3. **判断ポイントの追跡性**: DP-007/008/015 が要件→設計→ADR→実装で一貫追跡でき、`undecided → decided` の遷移（requirements の undecided=[DP-007,DP-008] → design の decision_record）が機能した。
4. **warn_and_document の型**: 「人間が決める」箇所（MFA 方針など）を AI が握りつぶさず推奨提示に留める構造が、実装段階でも守られた。
5. **authentication-architect の比較指針**: 「最低 1 つの代替スタックを比較」というルールで ADR-001 に Firebase vs Devise+OmniAuth の比較が残り、意思決定の根拠が文書化された。

## 3. 失敗・摩擦（発見事項）

| # | 重要度 | 発見事項 | 対応（→ backlog.md） |
|---|---|---|---|
| F-1 | High | **実行環境の前提が未文書化**。設計は Rails 前提だが、想定環境の Ruby は 2.6（Rails 7+ 非対応）。プラグインに Ruby/Rails バージョン前提・セットアップ手順が無く、rbenv で 3.3.6 を用意して回避した | B-06 |
| F-2 | High | **スキーマがスタブ**（T-011〜013 本実装が未）。design.yaml の data_model/api_design 等が JSON Schema で強制されず自由記述。検証が効かない | B-01 |
| F-3 | High | **firebase-auth-setup スキルが「初期セットアップ」止まり**。退会時の Admin SDK ユーザー削除、公開鍵（証明書）キャッシュ、トークン失効など**運用詳細が薄い**。`delete_user` はサービスアカウント鍵が要るためスタブ化せざるを得なかった | B-02 |
| F-4 | Med | **バックエンド/クライアントの責務境界が design に無い**。パスワード変更・リセット・メール変更は Firebase クライアント SDK 側で完結＝バックエンド対象外だが、requirements には機能として並ぶ。design で仕分けが明示されないと実装者が混乱する | B-03 |
| F-5 | Med | **MFA（DP-008）の実装ガイドが無い**。design で「オプトイン／管理者必須」と決めたが、Firebase での MFA 実装手順がスキルに無い | B-04 ✅（#131 / `firebase-auth-mfa`） |
| F-6 | Med | **成果物のスキーマ検証手段が無い**（TPL-27 validate-plugin.sh 未整備）。delivery/*.json をスキーマ検証できず手動確認 | B-07 |
| F-7 | Low | **退会済みアカウントの再登録ポリシーが判断ポイント化されていない**。実装中に「退会後の同一 UID 再ログインを許すか」を判断する必要が生じた（本実装は 403 で拒否）。DP に無い | B-08 ✅（#133 / [DP-28](https://www.notion.so/36dceb782fa381ee9134d4f7321f8ba9)） |
| F-8 | Low | **言語別の実装テンプレが無い**。AuthAdapter のコード雛形がスキルにあれば実装がさらに加速する | B-09 |
| F-9 | High | **DP-27 follow-up 未反映**（テンプレ `CLAUDE.md.template` → skill 化、CONV-06 改訂）。今回のパイロットでも改めて必要性を確認 | B-05 |

## 4. 改善提案（要約）

- **最優先（Rollout 前に対応推奨）**: F-2 スキーマ本実装 / F-3 firebase-auth-setup の運用詳細 / F-1 環境前提の明文化 / F-9 CONV-06・テンプレ skill 化。
- **Rollout と並行可**: F-4 design の責務列 / F-5 MFA ガイド / F-6 検証スクリプト。
- **任意**: ~~F-7 退会済み再登録 DP の起票~~ ✅（DP-28 で起票済 / B-08 / #133） / F-8 言語別実装テンプレ。

## 5. Rollout 推進可否判定

### 判定（最新）: **Go** — 2026-05-26 / 豊田（再判定）

- **判定**: T-023〜の Rollout（24 ユースケース展開）に**進む**。
- **再判定根拠**:
  1. **Go の条件だった High 4 件すべて CLOSED**: B-01（I/O 契約スキーマ本実装 / #126）、B-02（firebase-auth-setup 運用詳細 / #127）、B-05（CONV-06 改訂 / #128）、B-06（環境前提 / #129）。
  2. **T-021 再パイロット**（[`re-pilot-report.md`](./re-pilot-report.md)）で前回と異なる条件（医療 / MFA required / Next.js + Rails / ロール別認可 / 退会データ分離）で穴の解消を**実機で実証**: backend test **9 runs / 0 failures**、`zeitwerk:check` OK、frontend `tsc/build` 通過、docker emulator E2E **全 12 ステップ PASS**。
  3. **再パイロットでの新発見 RN-1/2/3 も対応済み**: emulator スキル新設（PR #145）で RN-3 解消、フロント 3 パターン既定化（PR #146）、**MFA 失効バグの根本対応**（PR #147、2 段階失効）まで完了。
- **着手対象**: **T-023〜**（Rollout 計画 / 24 ユースケース展開）。
- **残バックログ**（[`backlog.md`](./backlog.md)）: **B-07**（検証スクリプト / Med）、~~**B-08**（退会再登録 DP / Low）~~ ✅（DP-28 で起票済）、**B-09**（言語別実装テンプレ / Low）。いずれも型の穴ではないため **Rollout 並行で順次対応**。
- **関連 PR**: #143（MFA スキル）/ #144（再パイロット報告）/ #145（emulator スキル）/ #146（3 パターン既定化）/ #147（2 段階失効）/ #148-#149（usage-guide）。

### 判定（履歴）: No-go（条件付き保留）— 2026-05-25 / 豊田

- **判定**: 現時点で Rollout（T-023〜）には **進まない（No-go）**。**訂正バックログ（特に High 項目）を解消するまで保留**する。
- **根拠**: 型としての中核価値（一貫フロー・判断ポイント追跡・差し替え可能設計・warn_and_document）は **実アプリ構築で実用に耐えると実証**された（撤退基準には非該当）。一方で「型の穴」（B-01/B-02/B-05/B-06 等）が 24 ユースケース展開で繰り返しコスト化するため、先に塞ぐ。
- **Go の条件**: backlog の **High 4件（B-01 / B-02 / B-05 / B-06）** の解消をもって Rollout 着手を再判定する。
- **対応**: 訂正バックログ全9件を GitHub Issue 化済み（[backlog.md](./backlog.md) 参照、#126〜#134）。次の作業は Rollout ではなく **backlog High 項目の解消**。

## 6. 関連

- 訂正バックログ: [`backlog.md`](./backlog.md)
- **再検証（再パイロット）**: [`re-pilot-report.md`](./re-pilot-report.md)（2026-05-25。High 解消後に医療案件×MFA required×Next.js+Rails で再ドッグフードし、穴が塞がったことを実証）
- 未決判断ポイント: [`pending-decisions.md`](./pending-decisions.md)
- サンプルアプリ: `~/RubymineProjects/t-021-sample/`（`delivery/` にプラグイン成果物）
- 関連タスク: T-022 / T-021 / T-004 / T-002 / T-005、判断ポイント DP-007/008/015/027/028
