# ADR-AID-002: DP 命名規約の拡張（CONV-19 拡張・Rollout 開始前の合意）

- **ステータス**: accepted
- **決定日**: 2026-05-28
- **決定者**: 豊田
- **関連判断ポイント**: DP-AID-02（DP 再利用 vs 新規 DP 起票）
- **関連規約**: CONV-19（ID プレフィックス体系）
- **関連スキル**: aid-decision-point-registration
- **根拠成果物**: `delivery/dogfood/auth/findings.md` FINDING-03

## コンテキスト

T-021 認証プラグイン（MVP）と auth プラグインの後追いドッグフード（Step 11）で、判断ポイントカタログDB（DP-）の**命名形式が混在**していることが顕在化した：

| 既存形式 | 例 | 由来 |
|---|---|---|
| **番号形式（CONV-19 既存）** | DP-007 / DP-008 / DP-015 / DP-028 | T-007 判断ポイントカタログ初期起票（auth プラグインを含む 24 件超） |
| **プレフィックス付き形式（既存だが規約未整備）** | DP-INVITATION-POLICY-001 / DP-AUDIT-VIEW-001 / DP-NOTIFY-001 | B-22 / Issue #181 の運用系 DP（auth プラグインで先行採用）|

このまま Rollout（T-023〜T-045 / 23 プラグイン）を開始すると、プラグインごとに命名が揺れる：

- 決済プラグイン: `DP-PAYMENT-NN` / `DP-PAY-NN` / `DP-029〜` のどれか？
- 通知プラグイン: `DP-NOTIFY-NN`（既存 DP-NOTIFY-001 と被る）/ `DP-NTF-NN` ？
- メタプラグイン（本プラグイン）: `DP-AID-NN`（提案中）

DP-AID-02（80% 重複ルール）の命名衝突チェックも、形式の違いによる誤判定が起きる懸念がある（例: `DP-007` と `DP-AUTH-007` を別物として扱うか？）。

**Rollout 開始前に命名規約を合意しないと、後からの統一が困難**（DP DB のリレーション・既存プラグインの全文置換・ドキュメント整合が必要になる）。

## 検討した選択肢

### (A) 番号形式を継続（DP-001〜DP-NNN）

| 長所 | 短所 |
|---|---|
| シンプル。CONV-19 を変えない | プラグインを横断したときに**所属が見えない**（DP-128 が認証か決済かは DP DB を開かないと分からない）|
| 既存 DP との連番継続が自然 | 既存プレフィックス付き DP（DP-INVITATION-POLICY-001 等）の扱いが宙に浮く |

### (B) プレフィックス付き形式に完全統一（既存もマイグレ）

| 長所 | 短所 |
|---|---|
| 所属が明確（`DP-AUTH-007` で認証由来と一目瞭然）| **既存 DP の全文置換が必要**（Notion DB / コード / ドキュメント / git 履歴に DP-007 等のリテラルが多数）|
| Rollout で形式が揺れない | 既存案件（オンライン診療パイロット等）の ADR を破壊的に書き換える運用負荷 |

### (C) 共存（既存番号は維持・新規はプレフィックス付き）

| 長所 | 短所 |
|---|---|
| **既存 DP に手を入れない**（マイグレ不要）| 命名形式が形式上は混在し続ける（ただし「既存固定 / 新規プレフィックス」のルールで運用は明確）|
| Rollout の新規 DP は `DP-<USECASE>-NN` で所属明確 | 命名衝突チェックは形式横断で実装する必要 |
| プレフィックス付き既存（DP-INVITATION-POLICY-001 等）も**そのまま採用**（横断 DP の前例として扱う）| — |

### (D) 完全自由（プラグインが決める）

| 長所 | 短所 |
|---|---|
| 自由度が高い | 揃わない（最悪パターン）。DP-AID-02 が機能しない |

## 決定

**(C) 採用：既存番号は維持・新規はプレフィックス付き形式で運用する。**

### 命名規約（CONV-19 拡張）

| カテゴリ | 形式 | 例 | 用途 |
|---|---|---|---|
| **既存番号形式（凍結）** | `DP-NNN`（NNN は 3 桁 0 埋め）| DP-007 / DP-008 / DP-015 / DP-028 | T-007 起票分。**新規追加しない**（マイグレもしない）|
| **既存プレフィックス付き（凍結）** | `DP-<DOMAIN>-<TOPIC>-NNN` | DP-INVITATION-POLICY-001 / DP-AUDIT-VIEW-001 / DP-NOTIFY-001 | B-22 起票分。**新規追加しない**（既存形式として残す）|
| **新規プラグイン固有 DP** | `DP-<USECASE>-NN`（USECASE は kebab-case を upper-snake_case 化、NN は 2 桁 0 埋め）| DP-PAYMENT-01 / DP-PAYMENT-02 / DP-NOTIFY-01（既存 DP-NOTIFY-001 と被るので**注意必要**：FINDING-03 派生）/ DP-IAC-01 | Rollout プラグイン（T-023〜T-045）の新規 DP |
| **メタ層 DP（本プラグイン）** | `DP-AID-NN`（NN は 2 桁 0 埋め）| DP-AID-01〜DP-AID-05 | xtone-aid-skill-creator-plugin が扱うメタ判断 |
| **横断 DP（複数プラグインで再利用される DP）** | `DP-<CONCERN>-NN`（CONCERN は upper-snake_case）| DP-OBSERVABILITY-01 / DP-PRIVACY-01 | 特定プラグインに閉じない横断的論点（運用方針・規制対応等）|

### 既存 DP との衝突回避（重要）

- 新規プラグイン固有 DP の USECASE 部分が**既存プレフィックス付き DP のドメイン名と被る**場合は、新規側にサフィックスを追加して回避：
  - 例：通知プラグインの DP-NOTIFY-01 は **既存 DP-NOTIFY-001 と紛らわしい** → 通知プラグインは `DP-NOTIFICATION-NN`（usecase = notification）に変更するか、`DP-NOTIFY-PLUGIN-NN` と区別する
- 命名衝突チェックは `aid-decision-point-registration` Skill の Step B で**形式横断で実行**する（番号形式 + プレフィックス付き形式の両方を Notion DB 全文検索）

### マイグレーション方針

- **既存 DP（番号形式 / プレフィックス付き）はマイグレしない**（凍結）
- 既存 DP の追加情報（選択肢・MVP 推奨の更新等）は**現行 ID を維持したまま**行う
- Rollout プラグインで既存 DP を再利用する場合は `docs/decision-points.md` に「**`DP-007` を本プラグインでも採用**」と追記（新規起票しない・DP-AID-02 の運用そのまま）

### 番号採番ルール

- `DP-<USECASE>-NN` の NN は**プラグイン単位で 01 から採番**（プラグイン横断の通し番号にしない）
- `DP-AID-NN` も同様（本プラグイン単位で 01 から）
- 同プラグイン内で**廃止された DP の番号は再利用しない**（Notion DB の参照履歴を壊さない）

## 帰結

### 正の帰結

- **既存 DP に手を入れない**ことで、ADR・実装コード・git 履歴・サンプル成果物への影響ゼロ
- **新規 DP は所属が明確**（DP-PAYMENT-01 で決済由来と即時判別）
- DP-AID-02（80% 重複ルール）の命名衝突チェック仕様が明確化
- Rollout で発生する 50〜100 件の新規 DP が**プラグイン単位で整理**される

### 負の帰結 / リスク

- **命名形式が形式上は混在し続ける**（既存番号・既存プレフィックス・新規プレフィックスの 3 系統）。緩和：本 ADR で運用ルールを明文化、Notion DP DB に「形式」プロパティ（Select）を追加する案を別タスク化
- **DP-NOTIFY-* 衝突問題**: 既存 DP-NOTIFY-001（auth プラグイン由来の横断的通知 DP）と新規通知プラグインの DP の名前空間が被る。緩和：通知プラグインは usecase = `notification` で命名するか、DP の所属を明示する prefix `<USECASE>-PLUGIN-` を使う（Rollout 開始前にプラグイン担当者で再協議）
- **複合 USECASE（例: 認証 + SSO）の扱い**: usecase が複合的なときの命名が曖昧。緩和：プラグイン側で usecase を 1 つに正規化する（plugin-scope.json の usecase は単数）
- **横断 DP（DP-OBSERVABILITY-01 等）と新規プラグイン固有 DP の境界が曖昧**: 緩和：横断 DP は ADR で正式起票してから DP-DB に追加（プラグインから直接起票しない）

## 関連スキル / 規約の更新

本 ADR を受けて、以下を**別タスク**で更新する：

- `aid-decision-point-registration/SKILL.md` の「命名衝突チェック」節：3 形式の横断検索ルールを明記
- `aid-decision-point-registration` Command（`/aid-dp-register`）：正規 ID 命名のユーザ確認時に本 ADR を引用
- `docs/decision-points.md` の DP-AID-02：本 ADR 採用後のルール（既存形式凍結 / 新規プレフィックス）を反映
- 本プラグインの `docs/decision-points.md` 末尾「CONV-19 拡張」節：「ADR-AID-002 で accepted」と更新
- **CONV-19 規約 DB（Notion）**：本 ADR を関連リンクとして追加（規約側を更新するか、ADR を CONV-19 の補遺として位置付けるかは別議論）

## 関連

- 根拠ドッグフード結果: `delivery/dogfood/auth/findings.md` FINDING-03
- 関連 ADR: ADR-AID-001（メタプラグイン修正時のドッグフード必須化）
- 既存規約 CONV-19: ID プレフィックス体系（RULE / DP / MOD / ADR / FLD / CONV / DPS / MCS / SCH / MCP / SKL / TPL）
- 既存 DP プレフィックス付き例: DP-INVITATION-POLICY-001（B-22 / Issue #181）

## 履歴

| 日付 | 出来事 |
|---|---|
| 2026-05-28 | Step 11 ドッグフード FINDING-03 を受けて起票・accepted |
