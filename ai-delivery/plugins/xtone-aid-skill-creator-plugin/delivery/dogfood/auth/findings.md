# ドッグフード所見：auth プラグインを本プラグインのフォーマットで起こす

> **目的**: 本プラグイン（`xtone-aid-skill-creator-plugin`）の出力フォーマット（`plugin-scope.json` / `plugin-architecture.{md,json}`）が、既存 `xtone-auth-plugin` の実態を表現できるかを後追いで実証する。**循環参照リスクの最小限のセーフティ**（aid-skill-creator-plugin-guide §メタゆえの留意点）。

- **検証日**: 2026-05-28
- **検証者**: aid-skill-creator-plugin Step 11（手動ドッグフード）
- **検証対象**: `plugins/xtone-auth-plugin/`
- **比較対象**: `plugins/xtone-auth-plugin/skills/auth-plugin-guide/SKILL.md`（CONV-06 6項目）/ `agents/authentication-architect.md` / `docs/decision-points.md` / `docs/usage-guide.md`

## サマリ

- ✅ **本プラグインの出力フォーマットは auth プラグインの実態をおおむね表現できる**（Skill 一覧・Subagent・DP 一覧・スタック・ドメイン拡張スキーマすべてカバー）
- ⚠️ **2 件のスキーマギャップ**を検出（横断機能の種類区別・独自 sample-input 表現）→ **2026-05-28 解消済み**（FINDING-01 / FINDING-02）
- ⚠️ **1 件の運用ギャップ**（DP 命名形式の混在：CONV-19 拡張の必要性が顕在化）→ **2026-05-28 ADR-AID-002 で accepted**（FINDING-03）
- ✅ **B-19（横断 Skill 化）・T-004（差し替え可能設計）・CONV-06（6項目）は本プラグインのフォーマットで漏れなく追える**

### 解消状況（2026-05-28 更新）

| ID | 内容 | 状態 | 対応 |
|---|---|---|---|
| **FINDING-01** | 横断 Skill の kind 表現フィールド不足 | ✅ **解消** | `aid-plugin-scope-extraction` / `aid-plugin-architecture-design` / `aid-skill-authoring` の SKILL.md に `cross_cutting_candidates[].kind` / `skills[].kind` を追加。`decision-points.md` の DP-AID-01 判定軸に `kind` を追加 |
| **FINDING-02** | 独自 sample-input 表現フィールド不足 | ✅ **解消** | `aid-plugin-scope-extraction` / `aid-plugin-architecture-design` SKILL.md に `sample_case_legacy` フィールド追加。`/aid-sample-case-binding` Command に `--legacy-only` モード追加。`decision-points.md` DP-AID-03 に併記 |
| **FINDING-03** | DP 命名形式の混在（CONV-19 拡張必要） | ✅ **解消（ADR-AID-002 accepted）** | `docs/adr/ADR-AID-002.md` 起票。既存番号形式（DP-007 等）凍結 + 新規プラグインは `DP-<USECASE>-NN` + メタは `DP-AID-NN` + 横断は `DP-<CONCERN>-NN` の運用ルール合意 |

## 検出されたギャップ

### FINDING-01: 横断 Skill の「種類」を表現するフィールドが不足

**現象:**
- auth プラグインには横断 Skill が 2 つある：
  - `firebase-auth-mfa`（**機能**が複数層にまたがる: enrollment=client / 検証・強制=backend / SDK=iaas）
  - `firebase-auth-emulator`（**実行環境**が複数層にまたがる: Docker=infrastructure / 署名検証スキップ=backend / connectAuthEmulator=client）
- 本プラグイン仕様の `cross_cutting_candidates[]` / `skills[].responsibility_split` は層を表現できるが、**「なぜ横断なのか」の種類（feature-spanning vs environment-spanning）を区別できない**

**影響:**
- 後段の `/aid-architect-author` / `/aid-skill-new` で、独立 Skill 化判断（DP-AID-01）の根拠が薄くなる
- 将来 Rollout で「決済プラグインの webhook 受け口は environment-spanning か feature-spanning か」のような判断が必要なときに型が無い

**修正候補（本プラグイン側）:**

| 修正対象 | 修正内容 |
|---|---|
| `aid-plugin-scope-extraction/SKILL.md` | `cross_cutting_candidates[]` に `kind` フィールドを追加（enum: `feature-spanning` / `environment-spanning` / `concern-spanning`）|
| `aid-plugin-architecture-design/SKILL.md` | `skills[]` の構造化抜粋に `cross_cutting` (boolean) + `kind` (enum) を追加 |
| `aid-skill-authoring/SKILL.md` | 横断 Skill の判定（B-19）に `kind` を引いて、種類に応じた SKILL.md テンプレを使い分け |
| `decision-points.md` の DP-AID-01 | 「責務分担が 2 層以上」の判定軸に「横断の種類」を追加 |

**優先度:** 中。MVP ではどちらも「横断 Skill 化推奨」で十分動くが、Rollout 中盤で型化精度を上げるために対応。

**ADR 候補:** ADR-AID-003「横断 Skill の種類分類（feature / environment / concern）」

---

### FINDING-02: 独自 sample-input（カタログ外）を表現するフィールドが不足

**現象:**
- auth プラグインは **B-21（共通 sample-cases カタログ運用）が確立される前**に独自の `sample-inputs/bookclub-app.requirements-input.md` を作成した経緯がある
- 経緯保存のため**現状もカタログ運用と並存**（plugin-developer-guide §1 Step 5 で明記）
- 本プラグイン仕様の `sample_case_candidates` / `sample_case_bindings` は **カタログ参照のみ**を想定しており、独自案件並存を表現できない

**影響:**
- 既存プラグインを本プラグインで「後追い起稿」しようとすると、独自案件の存在が抜け落ちる
- Rollout 中に「特殊案件で独自 sample-input を追加したい」要望が出たときに型が無い

**修正候補（本プラグイン側）:**

| 修正対象 | 修正内容 |
|---|---|
| `aid-plugin-scope-extraction/SKILL.md` | `sample_case_legacy` フィールドを追加（独自案件名 / 場所 / 経緯 / カタログ運用との関係）|
| `aid-plugin-architecture-design/SKILL.md` | 同上を `plugin-architecture.json` にも反映 |
| `aid-sample-case-binding.md`（Command）| `legacy_only` モードを追加（カタログ symlink は作らず legacy ノートのみ生成）|
| `decision-points.md` の DP-AID-03 | 「該当ゼロなら新案件追加 PR」に「またはレガシー並存（既存プラグインの場合のみ）」を併記 |

**優先度:** 低。新規プラグインでは基本的にカタログ運用で十分（auth は例外）。ただし**既存プラグインの後追い起稿**（Rollout の途中で本プラグインに切り替えるケース）では必須。

**ADR 候補:** なし（運用ルールとして decision-points.md に追記で足る）

---

### FINDING-03: DP 命名形式の混在が顕在化（CONV-19 拡張の必要性）

**現象:**
- auth プラグインの DP は 2 形式が混在：
  - 番号形式（CONV-19 既存）: `DP-007` / `DP-008` / `DP-015` / `DP-28`
  - プレフィックス付き形式（既存だが規約化されていない）: `DP-INVITATION-POLICY-001` / `DP-AUDIT-VIEW-001` / `DP-NOTIFY-001`
- 本プラグインは `DP-AID-NN`（メタ）と `DP-<USECASE>-NN`（Rollout）を提案しており、CONV-19 拡張の議論を**ADR-AID-002 予定**としていた

**影響:**
- このまま Rollout を進めると、DP の命名が**プラグインごとに揺れる**（決済が `DP-PAYMENT-NN` か `DP-PAY-NN` か `DP-28`〜の連番継続か）
- DP-AID-02（80% 重複ルール）の命名衝突チェックで、形式の違いによる誤判定が起きる

**修正候補（本プラグイン側）:**

| 修正対象 | 修正内容 |
|---|---|
| `aid-decision-point-registration/SKILL.md` の Step B | 「正規 ID の命名」を **CONV-19 拡張の合意前**は仮ルール（`DP-<USECASE>-NN` 形式）として明示 |
| `decision-points.md` の DP-AID-02 / 末尾 CONV-19 拡張節 | 既存 7 形式の混在を一覧化し、Rollout で増えうる形式を列挙 |
| 本プラグインの `docs/adr/ADR-AID-002.md` を**新規起票**（後段タスク）| CONV-19 拡張の正式 ADR |

**優先度:** 高（Rollout 開始前に決めないと、後から命名統一が困難）。

**ADR 候補:** **ADR-AID-002**「DP 命名規約の拡張（CONV-19 拡張）」— 形式の合意・既存 DP のマイグレーション方針

---

## 妥当性が確認できた点（フォーマットがカバーできている）

| 観点 | 結果 | 補足 |
|---|---|---|
| CONV-06 6項目（Plugin Description / Applicable Domains / Dependent Modules / Phase Skills / Decision Points / Related Plugins）| ✅ | `plugin-scope.json` で全項目を表現可 |
| Skill 一覧（フェーズ × 責務 × responsibility_split）| ✅ | 7 Skill すべて表現可（mfa / emulator の横断性も `responsibility_split` で表現可、ただし FINDING-01 の補足必要）|
| Subagent 拡張（authentication-architect）| ✅ | `subagents[]` + `trigger_command` で表現可・DP-AID-05 の判断軸に合致 |
| Command 拡張（/auth-design）| ✅ | `commands[]` で表現可 |
| DP 候補（7 件・既存再利用 vs 新規）| ✅（FINDING-03 補足必要）| `dp_candidates[]` で表現可・命名形式の混在は FINDING-03 |
| ドメイン拡張スキーマ（design.auth.schema.json）| ✅ | `design_extension_schema` で表現可 |
| 外部 MCP（github / notion）| ✅ | `external_mcps[]` で表現可 |
| 言語別 references stacks（rails / nextjs / hotwire / docker-compose）| ✅ | `stack_candidates` / `skills[].references_stacks` で表現可 |
| クライアントワーク制約（共通方針 4）| ✅ | `client_work_constraints` で表現可（auth では security_review のみ該当）|
| シナリオ（共通方針 1）| ✅ | `scenarios.{new, existing_modification}` で表現可 |
| 横断 Skill の存在（B-19）| ⚠️ | `cross_cutting_candidates[]` で表現可、ただし種類区別は FINDING-01 |
| 独自 sample-input（B-21 以前）| ❌ | FINDING-02・追加フィールド必要 |

## 次のアクション

### 本プラグイン側の修正（Step 11 後の必要対応）

**すべて 2026-05-28 に対応済み**（findings.md 上のサマリ表を参照）：

1. ✅ **FINDING-01**: `cross_cutting_candidates[].kind` と `skills[].kind` を `aid-plugin-scope-extraction` / `aid-plugin-architecture-design` / `aid-skill-authoring` の SKILL.md に追記済み
2. ✅ **FINDING-02**: `sample_case_legacy` フィールドを同 SKILL.md と `aid-sample-case-binding.md` Command に追記済み
3. ✅ **FINDING-03**: `docs/adr/ADR-AID-002.md` 起票・accepted（DP 命名規約の拡張）
4. ✅ **付随**: `docs/adr/ADR-AID-001.md` 起票・accepted（メタプラグイン修正時のドッグフード必須化）

### auth プラグイン側のアクション

なし。auth プラグインは現状のままで本プラグインのフォーマットでおおむね表現できる。`sample-inputs/bookclub-app` の並存は経緯保存のため維持。

## ドッグフードの結論

- **本プラグインのフォーマットは Rollout プラグイン（T-023〜T-045）に適用可能**。22/50 タスクで確立された型を本プラグインが概ね受け取れている。
- 2 件のスキーマギャップ（FINDING-01 / FINDING-02）は MVP では許容範囲。**FINDING-03 のみ Rollout 開始前に対応必須**。
- 循環参照リスクは未顕在化（本プラグインで本プラグインを再生成していないため）。本ドッグフードでは別プラグイン（auth）を対象にしたので問題なし。

## メタ的な学び

- **既存プラグインの後追い起稿は、新規プラグインの起稿よりも難しい**（既に決まっている命名・構造に合わせなければならない）。本プラグインの主たる対象は新規（T-023〜T-045）であり、後追いは検証目的に留めるのが妥当。
- **「型を作る型」自体の検証はドッグフードで実証するしかない**（ユニットテストでは網羅できない）。今後も Rollout の節目（5 プラグイン目・10 プラグイン目）で同様のドッグフードを行い、型の劣化を検出する。
