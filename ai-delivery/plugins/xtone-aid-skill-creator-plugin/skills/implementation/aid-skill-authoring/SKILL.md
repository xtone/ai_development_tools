---
name: aid-skill-authoring
description: 対象 AIデリバリプラグインに新しい Skill を SKL-12 / SKL-20 準拠で対話的に起稿するスキル。フェーズ（requirements / design / implementation / test）+ skill_name + 責務を入力に、SKL-DB の骨格と xtone-auth-plugin のリファレンスを引いて SKILL.md と必要なら references/ / templates/ の雛形まで作る。「言語非依存契約 + 言語別レシピ分離」「既知の制約を徹底明文化」「要件で別指定があれば要件優先」を全 Skill に強制する。
---

# AID Skill Authoring Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

対象 AIデリバリプラグインに **新しい Skill** を起稿する。`xtone-plugin-template/skills/SKILL.md.template`（骨格）と `xtone-auth-plugin` の対応 Skill（型）を併用して、SKL-12（description 3要素）/ SKL-20（frontmatter 必須）/ B-19（横断機能は独立 Skill）/ B-15（DoD は他スキルとの結合まで）を満たす SKILL.md を生成する。

> 設計方針: 本スキルは「**Skill の容器**」を作る。中身（例: 認証なら DP-007/008/015、決済なら DP-PAYMENT-DRAFT-01）は対象プラグインの domain-architect / aid-domain-architect-design が埋める。本スキルは型の遵守責任を持つ。

## 入出力

- **入力:**
  - `target_plugin_path`（例: `ai-delivery/plugins/xtone-payment-plugin`）
  - `phase`（`requirements` / `design` / `implementation` / `test`）
  - `skill_name`（kebab-case、例: `payment-stripe-setup`）
  - `responsibility`（責務の 1〜2 文要約。`delivery/plugin-architecture.json` の `skills[*].responsibility` から取得可能）
  - `responsibility_split`（`["client", "backend", "iaas", "shared"]` の部分集合）
  - `needs_references`（boolean）/ `references_stacks`（`["rails", "nextjs", ...]`）
- **出力:**
  - `<target>/skills/<phase>/<skill_name>/SKILL.md`
  - `needs_references=true` なら `references/` ディレクトリと `<stack>.md` スタブ（中身の本実装は `/aid-references-new` ＝ `aid-references-authoring` Skill）
  - `templates/` 雛形（implementation かつ コピペ起点が要るなら）
  - `delivery/skill-authoring-log.md`（作成記録）

## 生成パターン（フェーズ別）

| フェーズ | 典型構造 | 必須セクション | 既定で参照する auth リファレンス |
|---|---|---|---|
| **requirements** | 抽出 Skill（チェックリスト中心） | 抽出チェックリスト / 入出力スキーマ / 運用方針 / 判断ポイント | `auth-requirements-extraction/SKILL.md` |
| **design** | 設計 Skill（contract + templates 分離） | 入出力（requirements.schema → design.schema）/ 手順 / 差し替え可能設計 / 判断ポイント / templates 参照 | `firebase-auth-design/SKILL.md` |
| **implementation** | 実装 Skill（言語非依存契約 + references 分離） | 呼び出しトリガ / 入出力 / 言語別レシピ表 / 実装契約（言語非依存） / 運用契約 / 手順 / 新言語展開手順 / DoD / 既知の制約 / 判断ポイント | `firebase-auth-setup/SKILL.md` / `firebase-auth-frontend/SKILL.md` / `firebase-auth-mfa/SKILL.md`（横断機能） |
| **test** | E2E 検証 Skill | 検証対象 UC / ツール（Playwright 等）/ 通過証跡（`delivery/e2e-verification-report.md`）/ DoD（他スキルからの完了判定） | `auth-e2e-verify/SKILL.md` |

## SKL-12 description の 3 要素テンプレ

frontmatter の `description` は必ず以下 3 要素を含める。万能記述は NG。

```yaml
description: "<何をするか: 動詞+目的語> + <いつ使うか: 起動トリガー（フェーズ・前提）> + <どんな条件で: ドメイン/規模/スタック/責務分担>"
```

良い例（auth プラグインから）:

- `Firebase Auth を任意のバックエンドに統合するスキル。実装フェーズで、design.schema.json の認証設計に従い、差し替え可能な認証アダプタ・JWT 検証・退会時の Admin SDK 削除・公開鍵キャッシュ・トークン失効を実装したいときに使う。言語/FW 非依存の契約と手順を定義し、具体コードは references/ の言語別レシピに分離（現状 Rails、Node 等は追加可能）。`

NG 例（自動拒否する）:

- 「決済まわりを処理する」（フェーズ・トリガー・条件すべて欠落）
- 「何でも処理できます」（万能記述）
- 1 文だけ・100 文字未満（情報量不足）

## 必須セクションの強制（実装 Skill の場合）

実装フェーズ Skill は以下を**必ず**含める（auth プラグイン firebase-auth-setup から型を写し取る）：

1. **呼び出しトリガ（B-13）** — `implementation-skill-planner` が判定する条件
2. **前提（B-11）** — `tech-version-check` 実行の指示
3. **スコープと責務分担** — `responsibility_split` を表で明示（client/backend/iaas/shared）
4. **入出力（スキーマ）** — 入力は design.schema、出力はコード + implementation-plan.schema
5. **言語別レシピ表** — `references/<stack>.md` と `templates/<stack>/` の対応表（state: ✅ / ⬜ 未作成）
6. **実装契約（言語非依存）** — adapter / port インターフェース、メソッドシグネチャ表（言語非依存記法）
7. **運用契約（言語非依存）** — 本番必須事項（冪等性・キャッシュ・失効など）
8. **手順（言語非依存）** — レシピを呼び出す前後の段取り
9. **新しい言語・FW への展開** — references / templates 追加の段取り
10. **DoD（B-15）** — 他スキル（test 系）の通過まで含める
11. **既知の制約** — 後続開発者が踏まないように
12. **判断ポイント** — 設計で未決のものを実装で勝手に決めない

> design / requirements / test フェーズは上の節を抜粋（不要なものは省く）。`responsibility_split` は **2 層以上をまたぐなら必須**（B-19）。

## 横断機能の判定（B-19）

`responsibility_split` が **2 つ以上の層**（client / backend / iaas / infrastructure）にまたがる場合：

- **既存 Skill を肥大化させない**。新規独立 Skill にする。
- 横断の **`kind`** を判定（FINDING-01 / ADR-AID-003 候補）：
  - **`feature-spanning`**: 機能そのものが複数層にまたがる（例: auth の `firebase-auth-mfa` = enrollment(client) + 検証・強制(backend) + SDK(iaas)）
  - **`environment-spanning`**: 実行環境が複数層にまたがる（例: auth の `firebase-auth-emulator` = Docker(infrastructure) + 署名検証スキップ(backend) + connectAuthEmulator(client)）
  - **`concern-spanning`**: 関心事（observability / privacy / audit 等）が複数層にまたがる
- 本スキルは入力 `responsibility_split` が 2 層以上のとき、ユーザに「独立 Skill 化推奨。既存 Skill 拡張で進めるなら理由を `decision_record` に残す（DP-AID-01）」と必ず警告する（warn_and_document）。
- `kind` に応じて SKILL.md 本文の節構成を微調整：
  - `feature-spanning` → `責務分担` 表は層 × 機能の 2 軸
  - `environment-spanning` → 「本番経路 vs ローカル経路」の分離節を追加（auth の emulator が前例）
  - `concern-spanning` → 「適用範囲」と「他 Skill との結合点」節を追加

## 「要件で別指定があれば要件優先」の強制（全層）

スキル既定パターン（例: 認証の `firebase-auth-frontend` の 3 パターン protected/public-aware/guest）を SKILL.md に書くときは、以下のフレーズを必ず添える：

> 上記は既定パターン。**案件で別指定があれば要件優先**。逸脱箇所は `responsibility_split` / `page_access_control` 等で明示し、`decision_record` に逸脱根拠を残す。warn_and_document に沿わせる。

本スキルは出力 SKILL.md にこのフレーズが含まれていない場合に警告する（template lint 相当）。

## 手順

1. **入力チェック**:
   - `target_plugin_path` の `xtone-<usecase>-plugin/` が存在し、`/aid-scaffold` 完了済みか確認。
   - `phase` が 4 値のいずれか。`skill_name` が kebab-case（小文字英数+ハイフン）。
   - 既存 `<target>/skills/<phase>/<skill_name>/SKILL.md` が**ない**ことを確認（上書きは `--force` 明示確認）。
2. **リファレンス読取**:
   - フェーズに応じた auth リファレンスを Read（上の対応表）
   - `xtone-plugin-template/skills/SKILL.md.template` も Read（骨格として）
3. **Notion DB 検索**（Notion MCP 必須）:
   - **SKL-DB** で当該フェーズ・近いユースケースの骨格候補を引く
   - **CONV-DB** の規約に逸脱がないか確認（命名・配置）
4. **frontmatter 生成**:
   - `name: <skill_name>`（kebab-case）
   - `description: <SKL-12 3 要素>`（ユーザに必ず内容を確認・3 要素揃わなければ AI が勝手に埋めず質問）
   - description が 100 文字未満 / 万能記述 / 3 要素欠落のいずれかなら警告して再質問
5. **本文生成**（フェーズ別必須セクションを埋める）:
   - 実装 Skill は 12 節すべて。design/requirements/test は適宜抜粋。
   - 「要件で別指定があれば要件優先」フレーズを必ず挿入。
   - `responsibility_split` を表で明示（2 層以上なら横断 Skill 警告）。
   - DP は `aid-skill-creator-architect` の出力（`plugin-architecture.json.dp_candidates`）から該当を引用。
   - 「本文中にダブル波括弧プレースホルダ例を書く場合は全角 `｛｛…｝｝` を使う」を出力時にチェック（validate-plugin.sh の grep 自己マッチ回避）。
6. **references / templates 雛形**:
   - `needs_references=true` なら `references/` ディレクトリ作成 + 各 `<stack>.md` を**スタブ**で置く（中身は `/aid-references-new` で本実装）
   - implementation でコピペ起点が要るなら `templates/<stack>/README.md` も置く（B-09）
7. **出力後の検証**:
   - `aid-validation-runner` を呼ぶ（特に SKL-20 frontmatter 必須フィールド・未置換プレースホルダ）
   - 警告ゼロを確認
8. **記録**:
   - `delivery/skill-authoring-log.md` に作成記録（usecase / phase / skill_name / description / 参照したリファレンス / 採用したテンプレ節）

## 既知の制約・落とし穴

- **`description` の万能記述は事故の元**: Claude が間違った Skill を選ぶ。SKL-12 3 要素は必ず守る。
- **`responsibility_split` を後から足すと整合性が崩れる**: 初稿で表を埋めない Skill は後で「これって client もやるの？」と混乱する。必ず初稿に含める。
- **`templates/` をフェーズで使いまわすと壊れる**: `firebase-auth-setup/templates/rails/` は setup 専用。frontend / mfa は別 templates を持つ。**フェーズ・スキル横断のテンプレ共有は禁止**（B-09 で確立）。
- **骨格テンプレ（SKILL.md.template）の `phase` プレースホルダ未置換**: 雛形は `xtone-plugin-template` 側に**手動置換前提**で残されている。本スキルは sed で置換するのではなく **完全に書き起こす**（テンプレ依存を断ち、出力品質を担保）。
- **横断 Skill の責務分担表を書かないと B-19 違反になる**: `firebase-auth-mfa` のように「client が何をやる / backend が何をやる / iaas が何をやる」を表で明示する。

## 判断ポイント（人間判断をスルーさせない）

- **DP-AID-01**（横断機能の境界）: `responsibility_split` が 2 層以上のときは独立 Skill 化を強く推奨。既存拡張で進めるなら `decision_record` に理由必須。
- **description の 3 要素のうち「条件」**（ドメイン/規模/スタック）が不確定なとき: AI が決めず人間に質問。`undecided` には残さない（description は Skill 選択の根拠なので空欄禁止）。
- **既存 Skill との重複**: 同フェーズに似た名前の Skill が既にある場合、AI が合体・差別化を勝手に決めない。**diff を提示してユーザに判断**してもらう。

未決は `delivery/skill-authoring-log.md` に明示し、`docs/pending-decisions.md` に追記する（T-002 warn_and_document）。

## メタゆえの留意点

- **本スキルは「容器の品質」のみを保証する**。中身のドメインロジックは domain-architect / 各設計 Skill の責務。境界を侵さない。
- **本プラグイン自身の Skill 追加にも使える**（ドッグフード）。例: `/aid-pilot` 等の新 Skill を本プラグインに追加するとき、`target_plugin_path=ai-delivery/plugins/xtone-aid-skill-creator-plugin` で本スキルを通す。
- **SKL-DB の検索粒度**: Skill 骨格 DB はフェーズ別・ドメイン別にエントリがある。usecase 単体で全文検索するより**フェーズで先絞り → ドメイン語で再絞り**が当たりやすい。
- **`SKILL.md` の長さ**: auth プラグインの実装 Skill は 70〜150 行が標準。短すぎ（< 30 行）は契約不足、長すぎ（> 200 行）は references に切り出す判断（DP-AID-04）。
