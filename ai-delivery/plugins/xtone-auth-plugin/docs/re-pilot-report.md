# 再パイロット報告書（T-021 MVP 再検証）— xtone-auth-plugin

- **対象プラグイン**: xtone-auth-plugin（T-021）
- **位置づけ**: T-022 内部パイロット（[pilot-report.md](./pilot-report.md)）で発見した穴を訂正バックログ（[backlog.md](./backlog.md)）で解消した後の **再ドッグフード**。修正が効いたか・新たな穴が無いかを、前回と異なる条件で再検証する。
- **実施日**: 2026-05-25
- **実施者**: Claude（ドッグフード実行）／**判定者**: 豊田（T-005）
- **再パイロット案件**: 架空案件「オンライン診療・問診サービス」（医療 / 要配慮個人情報 / 医療従事者・患者の2ロール）
- **サンプルアプリ**: `~/RubymineProjects/t-021-repilot-telemedicine/`（`backend/` = Rails 8.1 API / Ruby 3.3.6、`frontend/` = Next.js App Router、`delivery/` = プラグイン成果物）

> 本報告書は **たたき台**です。Rollout（T-023〜）推進可否は、本書をもとに豊田さんが最終判断します。

## 1. 前回との差分（汎用性を見るための条件変更）

| 観点 | 前回 T-022（みんなの読書会） | 今回 再パイロット（オンライン診療） |
|---|---|---|
| ドメイン | BtoC コミュニティ | 医療 / 要配慮個人情報 |
| MFA 方針(DP-008) | optional（管理者必須） | **required（全員必須・TOTP 主体）** |
| フロント | 実装せず（backend のみ） | **Next.js (App Router)** を実装（ビルド/型まで） |
| 構成 | Rails backend 単体 | **Next.js + Rails API の分離**（3スキル横断） |
| ロール | 単一 | **医療従事者 / 患者のロール別認可** |
| 退会 | 403 拒否（再ログイン） | **認証アカウント削除と診療データ保存の分離**（法定保存） |

## 2. 実施フロー（プラグインのドッグフード）

`/req-collect → /design → /implement` を辿り、判断ポイントは人間（豊田）に上げた。

1. **要件定義**: `auth-requirements-extraction` のチェックリストで `delivery/requirements.json`。DP-007/008 を `undecided` で設計に引き継ぎ。
2. **設計**: `firebase-auth-design` / `authentication-architect` で `delivery/design.yaml` + ADR-001/002。DP-007（Firebase 採用・2スタック比較）、DP-008（**required** 決定）、`responsibility_split`（Next.js=client / Rails=backend / iaas / shared）、セッション戦略（BFF）。
3. **スキーマ検証**: B-01 本実装スキーマで `requirements.json` / `design.yaml` を検証。
4. **実装**: `firebase-auth-setup`(rails) + `firebase-auth-mfa`(rails) で backend、`firebase-auth-frontend`(nextjs) + `firebase-auth-mfa`(nextjs) で frontend。

## 3. 検証結果（実測）

| 項目 | 結果 |
|---|---|
| `bin/rails test`（backend 結合テスト） | **9 runs / 14 assertions / 0 failures / 0 errors** ✅ |
| `bin/rails zeitwerk:check` | **All is good!**（本番 eager-load 健全）✅ |
| frontend `tsc --noEmit` | **EXIT 0**（レシピコードの型エラーなし）✅ |
| frontend `next build` | **Compiled successfully**（本番ビルド・型・静的生成）✅ |
| delivery スキーマ検証（B-01） | requirements/design ともに **PASS**。ネガティブ検証（必須欠落）で **NG を検出**＝検証が効く ✅ |
| MFA required 強制 | 第2要素なし→**403 mfa_required** / あり→200 ✅ |
| ロール別認可 | 患者=自分の consultation のみ / 医師=全件 ✅ |
| 退会の分離 | 認証アカウント論理削除＋診療データ保持（退会後も `consultations` が残る）✅ |
| トークン失効 | MFA 変更通知で `tokens_valid_after` 更新 ✅ |
| 差し替え可能設計(DP-007) | `AUTH_ADAPTER=test` で `Auth::TestAdapter` に切替・検証 ✅ |

## 4. 前回発見事項（F-1〜F-5 / B-10）の解消実証

| 前回の穴 | backlog | 再検証での実証 |
|---|---|---|
| **F-1** 実行環境の前提が未文書化 | B-06 (#129) | システム Ruby 2.6 では Rails 不可 → `environment-setup.md` の手順どおり rbenv で 3.3.6 / Rails 8.1 を用意して回避。**前提が明文化され再現できた** ✅ |
| **F-2** スキーマがスタブ | B-01 (#126) | requirements/design が本実装スキーマで検証 PASS。ネガティブ検証で「検証が効く」ことを確認。**前回『検証が効かない』が解消** ✅ |
| **F-3** firebase-auth-setup が運用詳細薄い | B-02 (#127) | 退会時 Admin 削除・証明書キャッシュ・トークン失効を backend に実装。失効テスト通過。`delete_user` のスタブ化が不要に ✅ |
| **F-4** 責務境界が design に無い | B-03 (#130) | `design.responsibility_split` を client/backend/iaas/shared で明示。実装が責務分割どおりに割れた（Next.js=client / Rails=backend） ✅ |
| **F-5** MFA 実装ガイドが無い | B-04 (#131) | `firebase-auth-mfa` で MFA=required を backend(強制)＋client(enroll/challenge) 実装。required 強制をテストで確認 ✅ |
| **F-9** DP-27 follow-up 未反映（ルート CLAUDE.md → skill 化・CONV-06 改訂） | B-05 (#128) | プラグインにルート `CLAUDE.md` は無く、運用 context（鉄則・フロー・判断ポイント）を `auth-plugin-guide` skill から参照して再パイロットを実施できた。※ B-05 は**構造／規約の改訂**で、実機テストではなく「skill ベースの運用 context でプラグインが回るか」の確認という性質（`claude plugin validate --strict` は T-021 完了時にクリーン済み） ✅ |
| （frontend ガイド欠落） | B-10 (#141) | `firebase-auth-frontend`(nextjs) で AuthClient/MfaClient を配置し tsc/build 通過。**前回未実装だったフロントが型レベルで通った** ✅ |

## 5. 今回の新たな発見事項

| # | 重要度 | 発見 | 対応案 |
|---|---|---|---|
| RN-1 | Med | **セッション戦略（BFF vs 直接 Bearer）が判断ポイントカタログ(DP-)に未登録**。`firebase-auth-frontend` のスキル内判断どまりで、案件横断の DP になっていない。要配慮個人情報案件では重要判断（BFF 採用＝ADR-002）。 | DP 新規起票候補（B-08 と同様に DP 化）。`docs/pending-decisions.md` に起票 |
| RN-2 | Med | **delivery 成果物のスキーマ検証が手動**（B-07 / `validate-plugin.sh` 未整備）。検証ロジック自体は B-01 で効くが、自動化されておらず都度スクリプトを書いた。 | B-07 (#132) の整備で `/implement` 前の検証をコマンド/CI 化 |
| RN-3 | Low | **MFA の client E2E は実 Firebase / Identity Platform が必要**で、ローカル検証は backend(TestAdapter)＋frontend(ビルド/型)に留まる。Firebase MFA の性質上の制約で「型の穴」ではない。 | 環境前提（B-06）に「MFA 検証は Identity Platform 有効プロジェクトが要る」を補足 |

> いずれも **High ではない**（Med 2 / Low 1）。前回のような「型の穴」が実装全体を止める性質のものは出ていない。

## 6. Phase 2: Docker Auth Emulator で実機 E2E 動作確認（2026-05-26）

Phase 1（要件→設計→backend(TestAdapter)+frontend(ビルド/型)）の後、「実際に動かして実装が問題ないか確認したい」「Docker で Firebase エミュレーター環境を構築したい」という要望に応えて、横断スキル **`firebase-auth-emulator`**（[PR #145](https://github.com/xtone/ai_development_tools/pull/145)）を新設し、サンプルアプリを emulator 対応に改修して `docker compose` で **実トークン経由の E2E** を確認した。

### 構成（docker-compose）

| サービス | イメージ / ポート | 状態 |
|---|---|---|
| `auth-emulator` | firebase-tools 14.4.0 + JRE17（port 9099 / UI 4000） | healthy |
| `backend` | Rails 8.1 / Ruby 3.3.6（port 3000） | up |
| `frontend` | Next.js (App Router)（port 3001） | up |

backend は `FIREBASE_AUTH_EMULATOR_HOST` 検出時のみ **署名検証スキップ + 手動 iss/aud/exp 検証**、Admin REST を `Bearer owner` で `http://EMU/identitytoolkit.googleapis.com` に切替。本番混入を防ぐ **production && emulator? → `abort`** ガードを app_auth.rb に同梱（PR #145 レビュー Major 指摘の対応）。

### E2E 結果（emulator REST + Rails API、12 ステップ）

| # | シナリオ | 結果 |
|---|---|---|
| 0 | emulator state クリア（再実行性） | OK |
| 1 | 患者・医師を emulator で `signUp` → `emailVerified=true` 更新 → `signInWithPassword` | OK |
| 2/3 | `POST /auth/session`（MFA 前、患者・医師とも） | 201 / 201 |
| 4 | **MFA 未充足の保護リソース** → **403 `mfa_required`** | ✅ `require_mfa!` が実機で発火 |
| 6–8 | SMS MFA enrollment: `start` → `verificationCodes` REST 取得 → `finalize` | OK（MFA 付き `idToken` 取得） |
| 9 | **MFA 充足で保護リソース** → 200 | ✅ `firebase.sign_in_second_factor` 検証成功 |
| 9b | ロール認可: **患者は自分のみ閲覧**（1 件） | OK |
| 10 | ロール認可: **医師は全件閲覧**（2 件） | OK |
| 11 | 退会 → 204、**診療データ保持**（`consultations` が 2 件残存） | ✅ ADR-002 の認証アカウント／診療データ分離が成立 |
| 12 | **退会後の同一 UID 再ログイン拒否** | 403（F-7 仮対応） |

### 実証されたポイント / 派生発見

- **MFA required の E2E がローカルで完結**（SMS MFA を使用）— 前回 **RN-3**「MFA の client E2E は実 Firebase が必要」の制約を **実質解消**。TOTP MFA は依然エミュレーター非対応（[firebase-tools #6224](https://github.com/firebase/firebase-tools/issues/6224)）のため、TOTP の E2E は実 Identity Platform へ委ねる（ADR-002 / スキル `firebase-auth-emulator` に明記）。
- **派生発見**: emulator の MFA enrollment は **`emailVerified=true` が前提**（`UNVERIFIED_EMAIL` エラー）。E2E スクリプトとスキルに反映（signUp 後に `accounts:update` で `emailVerified` を立てる）。
- **本番混入ガード**（production && emulator? → abort）が Vertex AI レビューの Major 指摘でテンプレート化（PR #145 Major #3）。サンプル `app_auth.rb` にも反映済み。

Phase 1（実機テスト＝TestAdapter / frontend=ビルドのみ）に **実トークンでの E2E**が積み上がり、Rollout の判定根拠が強化された。

## 7. Rollout 推進可否の再判定材料（判定は豊田）

- **Rollout の Go 条件だった High 4 件（B-01 / B-02 / B-05 / B-06）はすべて CLOSED**。さらに Med（B-03 / B-04 / B-10）も解消済み。
- 本再パイロットは、**前回と異なるドメイン・条件（医療 / MFA required / Next.js + Rails / ロール別認可 / 退会データ分離）**で要件→設計→実装を通し、修正が効いたことを実機（backend テスト）とビルド（frontend）で実証した。
- 新発見は Med 2・Low 1 のみで、いずれも Rollout と並行で対応可能。
- → **Rollout 着手を支持する材料が揃った**。

### 最終判定: **Go** — 2026-05-26 / 豊田

本書をもとに、T-022 内部パイロット報告書（[`pilot-report.md`](./pilot-report.md)）の Rollout 推進可否判定を **No-go → Go** に再判定。T-023〜の Rollout に進む。残バックログ B-07（検証スクリプト / Med）/ ~~B-08（退会再登録 DP / Low）~~ ✅（DP-28 で起票済）/ B-09（言語別実装テンプレ / Low）は **Rollout 並行**で順次対応する。

## 8. 関連

- 前回パイロット: [`pilot-report.md`](./pilot-report.md)
- 訂正バックログ: [`backlog.md`](./backlog.md)
- 再パイロット成果物: `~/RubymineProjects/t-021-repilot-telemedicine/`（`delivery/` にプラグイン成果物、`backend/` `frontend/` に実装）
- 使用スキル: `firebase-auth-setup` / `firebase-auth-frontend` / `firebase-auth-mfa` / `firebase-auth-design` / `auth-requirements-extraction`
- 関連タスク: T-021 / T-022 / T-004 / T-002 / T-005、判断ポイント DP-007/008/015/028
