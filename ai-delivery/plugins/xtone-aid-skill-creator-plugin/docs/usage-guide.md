# xtone-aid-skill-creator-plugin 使い方ガイド

AIデリバリ用プラグインを「中身ごと」起こすメタプラグインの使い方。23 本の Rollout プラグイン（T-023〜T-045）を単独/少数の担当者で回し切るための助手として動く。

> **実行環境**: 言語・FW のバージョンは固定せず**公式の最新安定版**を使う（[`ai-delivery/docs/environment-setup.md`](../../../docs/environment-setup.md)）。本プラグインは Notion MCP 接続必須（DB から引いて中身を生成する設計）。

## 1. インストール / ロード

開発中はセッション限定でロードして試せる:

```bash
# ai-delivery/ で
claude --plugin-dir plugins/xtone-aid-skill-creator-plugin
```

検証のみ:

```bash
bash ai-delivery/scripts/validate-plugin.sh plugins/xtone-aid-skill-creator-plugin --strict
```

### Notion MCP の前提（必須）

本プラグインは Notion 16 DB（TPL / SKL / CONV / DP / SCH / MCS / MCP 等）を参照する設計。以下のいずれかを満たすこと：

1. **ローカルで Notion MCP が起動**しており、`.env` の `NOTION_TOKEN` で本ワークスペースの 16 DB に読み取りアクセスできる
2. （`/aid-dp-register` を使う場合）DP-DB への**書き込み**アクセスもある

MCP 接続失敗時は本プラグインのスキルは「`/aid-skill-creator-design` 入力情報の取得失敗」等を `pending-decisions.md` に警告として残す（warn_and_document）。

## 2. 基本フロー（新規プラグインの立ち上げ）

```
/req-collect                    # 新規ユースケースのヒアリング → plugin-scope.json
   ↓
/aid-skill-creator-design       # メタ設計（必要 Skill / Subagent / DP 候補 / references 見立て）
                                #   → plugin-architecture.{md,json}
   ↓
/aid-scaffold <usecase>         # generate-plugin.sh ラッパー（骨格生成）
   ↓
/aid-architect-author <usecase> # <usecase>-architect.md を中身ごと埋める
   ↓
/aid-skill-new <phase> <skill>  # 各フェーズの Skill を SKL-12/SKL-20 準拠で起稿
                                #   （複数回・必要数だけ）
   ↓
/aid-references-new <skill> <stack>   # 言語別 references を追加（implementation Skill のみ）
                                #   （複数回・案件で使う stack のみ）
   ↓
/aid-dp-register                # 検出した新規 DP を Notion DP DB に起票（3段階）
   ↓
/aid-sample-case-binding <usecase> <case>  # sample-cases から symlink（B-21）
   ↓
/aid-validation-runner          # 仕上げの品質ゲート（warn_and_document）
```

補助コマンドは基盤共通: `/decide`（判断記録）/ `/status`（進捗）/ `/next`（次アクション）/ `/pending-list`（未決一覧）/ `/skip-review`（AIレビュー）。

> 既存プラグインに **Skill だけ追加**するなら `/aid-skill-new` から始められる（scaffold/architect-author はスキップ可）。

## 3. 成果物

| フェーズ | コマンド | 出力 |
|---|---|---|
| 要件定義（メタ） | `/req-collect` → `aid-plugin-scope-extraction` | `delivery/plugin-scope.json`（usecase / モジュール / 適用ドメイン / フェーズ別 Skill 候補 / 横断機能候補 / 既知 DP 候補 / sample-cases 候補） |
| 設計（メタ） | `/aid-skill-creator-design` → `aid-skill-creator-architect` + `aid-plugin-architecture-design` | `delivery/plugin-architecture.md`（人間レビュー用）+ `delivery/plugin-architecture.json`（後続スキル機械可読） |
| 実装（メタ） | `/aid-scaffold` / `/aid-architect-author` / `/aid-skill-new` / `/aid-references-new` / `/aid-dp-register` / `/aid-sample-case-binding` / `/aid-validation-runner` | `ai-delivery/plugins/xtone-<usecase>-plugin/`（新規プラグインの骨格＋中身）+ Notion DP DB の新規エントリ + 各種 log（`scaffold-log.md` / `architect-authoring-log.md` / `skill-authoring-log.md` / `references-authoring-log.md` / `dp-registration-log.md` / `sample-case-binding-log.md` / `validation-report.md`） |

> **メタプラグインゆえ通常スキーマと別フォーマット**: `plugin-scope.json` / `plugin-architecture.{md,json}` は `requirements.schema.json` / `design.schema.json` の対象外（validate-plugin.sh のスキーマ検証パターンに合致させない別名）。

### スキル一覧

| 種別 | スキル | 責務 |
|---|---|---|
| 運用ガイド | [`aid-skill-creator-plugin-guide`](../skills/aid-skill-creator-plugin-guide/SKILL.md) | 本プラグインの作業ガイド（CONV-06 6項目） |
| 要件定義 | [`aid-plugin-scope-extraction`](../skills/requirements/aid-plugin-scope-extraction/SKILL.md) | 新ユースケースのヒアリング → plugin-scope.json |
| 設計 | [`aid-plugin-architecture-design`](../skills/design/aid-plugin-architecture-design/SKILL.md) | plugin-scope.json → plugin-architecture.{md,json}（4チャネル出力） |
| 設計 | [`aid-domain-architect-design`](../skills/design/aid-domain-architect-design/SKILL.md) | `<usecase>-architect.md` を中身ごと埋める（DP比較表・差し替え可能設計） |
| 実装 | [`aid-plugin-scaffold`](../skills/implementation/aid-plugin-scaffold/SKILL.md) | `generate-plugin.sh` ラッパー（引数組立・対話確認・post-checks） |
| 実装 | [`aid-skill-authoring`](../skills/implementation/aid-skill-authoring/SKILL.md) | 新 Skill を SKL-12/SKL-20 準拠で起稿（言語非依存契約 + references 分離強制） |
| 実装 | [`aid-references-authoring`](../skills/implementation/aid-references-authoring/SKILL.md) | references/<stack>.md + templates/<stack>/ 起稿（契約は変えない・既知の制約徹底明文化） |
| 実装 | [`aid-decision-point-registration`](../skills/implementation/aid-decision-point-registration/SKILL.md) | Notion DP DB への安全な起票（3段階・命名衝突チェック・書き込み権限の本スキル限定） |
| 実装 | [`aid-sample-case-binding`](../skills/implementation/aid-sample-case-binding/SKILL.md) | `xtone-shared-plugin/sample-cases/` カタログ案件を `sample-inputs/` に symlink で取り込み（B-21 / #174）。`--legacy-only` で B-21 以前の独自案件並存にも対応（FINDING-02 / DP-AID-03） |
| 実装 | [`aid-validation-runner`](../skills/implementation/aid-validation-runner/SKILL.md) | `validate-plugin.sh` ラッパー（8 カテゴリ分類・重大度判定・pending-decisions 同期） |

横断スキル（symlink）:

| スキル | 由来 |
|---|---|
| `skills/implementation/tech-version-check/` | xtone-shared-plugin（B-17） |
| `skills/implementation/implementation-skill-planner/` | xtone-shared-plugin（B-18） |

## 4. 判断ポイント（人間判断をスルーさせない）

| DP | 内容 | 既定の推奨 |
|---|---|---|
| **DP-AID-01** | 新規 Skill 追加時の境界判断（既存 Skill 拡張 vs 新規独立 Skill） | 2層以上にまたがる場合は独立 Skill |
| **DP-AID-02** | DP 再利用 vs 新規 DP 起票 | 80% 重複なら既存再利用、迷ったら人間 |
| **DP-AID-03** | sample-case の選定 | カタログから 2 件選定。該当ゼロなら新案件 PR |
| **DP-AID-04** | 言語別 references を増やすタイミング | 案件で必要になった時点で追加（先回りは型のドリフトを招く） |
| **DP-AID-05** | domain-architect の責務拡大判断 | 2 つ以上の比較対象スタックを持つドメインは特化を作る |

詳細は [`decision-points.md`](./decision-points.md)。AI は決めず推奨だけ提示。未決は `pending-decisions.md` に残る（warn_and_document, T-002）。

> **DP-AID-* は本プラグイン起稿時点では未起票（draft）**。本プラグインのドッグフードが安定したのち、`/aid-dp-register` で Notion DP DB に正式起票する想定。

## 5. 通し検証（決済プラグインを立ち上げるシナリオ）

仮想シナリオ: T-027 決済プラグイン（`xtone-payment-plugin`）を本プラグインで立ち上げる例。

> **本プラグインの sample-outputs/ は現在ありません。** ドッグフード（Step 11 予定）が完了次第、決済プラグインの中間成果物（plugin-scope.json / plugin-architecture.{md,json}）を再生成して同梱予定。それまでは新規ユースケースの雛形は本プラグインのスキル「入出力」節と auth プラグインの実装例を直接参照する。

## 6. メタゆえの留意点

1. **本プラグインを本プラグインで再生成しない**（循環参照）。修正前に**他プラグインの再生成が通る**ことを必ず確認（ADR-AID-001 予定）。
2. **Notion DP DB への書き込みは `/aid-dp-register` のみ**。他コマンド・スキルから起票しない（誤起票・重複・命名衝突防止）。
3. **CI 環境から `/aid-dp-register` を起動しない**（人間が起動するローカルからのみ運用）。
4. **二重波括弧プレースホルダ**を本ドキュメントや SKILL.md 本文で書く必要があるときは**全角** `｛｛…｝｝` を使う（`validate-plugin.sh` の grep 自己マッチ回避）。

## 7. プロンプト例（決済プラグインを立ち上げる）

仮想シナリオで実プロンプトをフェーズごとに整理する。プロンプトは **「ユースケース前提・判断ポイントの叩き・任せる範囲」を明示**することで、AI が `undecided` を残さず `decision_record` に書く / 適切なスキルと DP を引く動きをする。

### 7.1 要件定義（`/req-collect` ＋ `aid-plugin-scope-extraction`）

新ユースケースの前提と希望を 1 メッセージで揃え、scope 抽出スキルを呼ぶ。

```
決済モジュール（MOD-007）の新規プラグインを起こします。
- 対象ドメイン: EC・D2C と イベント LP の 2 種
- 想定スタック: backend = Rails、frontend = Next.js（hotwire は対象外）
- 候補決済プロバイダ: Stripe（第一）、GMO ペイメント、Komoju
- 既存資産: 認証プラグイン（xtone-auth-plugin）を adapter 設計の学習リファレンスに
- 既存改修対象: 含めない（新規開発のみ）
- sample-cases: ec-d2c-app と event-campaign-lp を pilot 入力候補に

aid-plugin-scope-extraction で delivery/plugin-scope.json を作ってください。
DP-AID-02（既存 DP 再利用判定）と DP-AID-03（sample-case 選定）は推奨だけ提示。
```

→ `delivery/plugin-scope.json`（usecase / モジュール候補 / 適用ドメイン / フェーズ別 Skill 候補 / 横断機能候補 / known_dp_candidates / sample_case_candidates / undecided）。

### 7.2 メタ設計（`/aid-skill-creator-design` ＋ `aid-skill-creator-architect`）

必要 Skill / Subagent / DP 候補 / references 見立てを 4 チャネルで揃える。

```
plugin-scope.json をもとに、aid-skill-creator-architect を起動して
新規 payment プラグインのメタ設計を作ってください。
- 既存 DP の再利用判定（DP-AID-02）: 認証の DP-007/008/015 とは別ドメインなので
  原則新規起票。ただし「規制適用判定」型は DP-015 と構造が近いか確認
- 主要 DP（DP-PAYMENT-DRAFT-01）: Stripe / GMO / Komoju の 3 スタック比較
  - 判断軸: 国際対応、PCI DSS スコープ、コスト、日本決済手段（コンビニ・キャリア決済）
  - MVP 推奨: Stripe（PaymentAdapter で差し替え可能設計を維持）
- 横断機能候補: payment-webhook-handler（backend + iaas にまたがる）
- references 初期スタック: rails と nextjs

出力は delivery/plugin-architecture.md（人間レビュー用）と
delivery/plugin-architecture.json（後続スキル機械可読）。
```

→ `delivery/plugin-architecture.md` + `plugin-architecture.json`（必要 Skill 5 本想定、payment-architect Subagent 必要、DP-PAYMENT-DRAFT-01〜03、references stacks = rails/nextjs）。

### 7.3 骨格生成（`/aid-scaffold`）

```
plugin-architecture.json から /aid-scaffold payment を実行してください。
--description / --author / --domains / --modules / --domain は plugin-architecture.json
から自動で組み立て、実行前にプレビューしてください。
--force は使わない（既存プラグインはない想定）。
```

→ `ai-delivery/plugins/xtone-payment-plugin/` が生成、`payment-architect.md` / `payment-design.md` 雛形が実体化、post-checks（symlink 整合・未置換チェック・validate）通過。

### 7.4 architect の中身埋め（`/aid-architect-author`）

```
/aid-architect-author payment を実行してください。
- plugin-architecture.json.dp_candidates から主要 DP・案件固有 DP を取り込む
- 主要 DP（DP-PAYMENT-DRAFT-01）の比較表: Stripe / GMO / Komoju を並べ、
  PaymentAdapter（charge / refund / webhook_verify）の差し替え見通しを記述
- 適用条件 DP（PCI DSS スコープ判定）は「適用条件: 全決済案件」と明示
- frontmatter description は SKL-12 3 要素＋ DP-PAYMENT-* を含む形に書き換え
- DP-XXX 雛形・二重波括弧プレースホルダ ｛｛…｝｝ の残存が 0 を validate で確認
```

→ `agents/payment-architect.md`（DP 比較表 / MVP 推奨 / 差し替え可能設計 / frontmatter SKL-12 化 / 雛形プレースホルダ残存ゼロ）。

### 7.5 Skill 起稿（`/aid-skill-new`・複数回）

```
/aid-skill-new design payment-design を実行してください。
- plugin-architecture.json.skills から responsibility / responsibility_split / needs_references を取得
- 学習リファレンス: firebase-auth-design/SKILL.md
- 「要件で別指定があれば要件優先」フレーズを必ず添える
```

```
/aid-skill-new implementation payment-stripe-setup を実行してください。
- responsibility_split = ["backend", "iaas"]（2 層）→ 横断 Skill 化は不要だが
  webhook 受け口の独立 Skill 化を提案（B-19）
- needs_references = true, references_stacks = ["rails", "nextjs"]
- 学習リファレンス: firebase-auth-setup/SKILL.md（12 節必須）
```

```
/aid-skill-new implementation payment-frontend を実行してください。
- responsibility_split = ["client"]
- 学習リファレンス: firebase-auth-frontend/SKILL.md
- 案件で別指定があれば要件優先（決済 UI のデフォルトパターンを書く際に必須）
```

### 7.6 references 追加（`/aid-references-new`・stack 別）

```
/aid-references-new payment-stripe-setup rails を実行してください。
- 学習リファレンス: firebase-auth-setup/references/rails.md
- 契約（PaymentAdapter）は変えない
- 既知の制約: Stripe API バージョン固定の落とし穴 / webhook 署名検証 / 冪等性キー / カード情報の非保持（PCI DSS-A 維持）
- tech-version-check で Stripe gem の最新安定版を delivery/version-matrix.md に記録
```

```
/aid-references-new payment-stripe-setup nextjs を実行してください。
- 学習リファレンス: firebase-auth-frontend/references/nextjs.md
- Stripe.js / Elements の最小実装、トークン化（カード情報非通過）
```

### 7.7 DP 起票（`/aid-dp-register`）

```
/aid-dp-register を実行してください。
Step A プレビューを表で表示してから、1 件ずつユーザ確認 → 起票してください。
- DP-PAYMENT-DRAFT-01 → DP-PAYMENT-001（決済プロバイダ選択）
- DP-PAYMENT-DRAFT-02 → DP-PAYMENT-002（PCI DSS スコープ判定）
- DP-PAYMENT-DRAFT-03 → DP-PAYMENT-003（webhook 失敗時のリトライ方針）
命名衝突チェックを必ず Notion 検索で実行。一括承認禁止。
```

→ Notion DP DB に 3 件起票、`docs/decision-points.md` 同期更新、`payment-architect.md` の DP-ID を仮 → 正規に置換、`pending-decisions.md` から該当行を削除。

### 7.8 sample-cases 紐付け（`/aid-sample-case-binding`）

```
/aid-sample-case-binding payment ec-d2c-app
/aid-sample-case-binding payment event-campaign-lp
plugin-architecture.json.sample_case_bindings と整合確認。
```

→ `sample-inputs/ec-d2c-app` と `sample-inputs/event-campaign-lp` が symlink で作成、validate-plugin.sh の #174 / B-21 チェックを通過。

### 7.9 仕上げの validate（`/aid-validation-runner`）

```
/aid-validation-runner ai-delivery/plugins/xtone-payment-plugin を実行してください。
警告がある場合は 8 カテゴリ分類と重大度判定（Block-worthy / Should-fix / Info-only）を提示し、
Block-worthy のみ修正候補を提案してください（機械的修正でもユーザ確認後に実行）。
```

→ `delivery/validation-report.md` に分類済みレポート、警告ゼロなら `✅ Validation passed`、警告ありなら修正候補リスト。

### 7.10 プロンプト設計のコツ

- **ユースケース前提と DP 叩きを最初に揃える**: 「DP-AID-02 の判定方針」「主要 DP の MVP 推奨候補」を明示すると AI が勝手に決めず推奨だけ提示する
- **メタ層と実層を混同しない**: 本プラグインのスキルは「**新規プラグインそのもの**」を作る。「決済処理を実装する」プロンプトは新規 payment プラグインの implementation Skill に書く（本プラグインには書かない）
- **学習リファレンスを必ず明示**: 「auth の `authentication-architect.md` を学習リファレンスに」「`firebase-auth-setup/SKILL.md` の 12 節必須」など、写し取る対象を毎回指定する
- **「契約は変えない」**: references の追加で挙動が変わったら、契約変更（ADR 化）と references 修正のどちらかをユーザに選択させる（AI が勝手に契約変更しない）
- **`/aid-dp-register` は 1 件ずつ**: 「全部 OK」と言われても 1 件ずつ確認（誤起票の取り消しコストが高い）
- **未決を残すのは恥ではない**: 「ユーザ判断待ち」は明示的に `pending-decisions.md` に残す。`undecided` ゼロを急がない（warn_and_document）

## 8. トラブルシューティング

| 症状 | 原因候補 | 対処 |
|---|---|---|
| `/aid-skill-creator-design` で「plugin-scope.json が見つかりません」 | `/req-collect` 未実行 | `/req-collect` で `aid-plugin-scope-extraction` を流す |
| `/aid-scaffold` で「未置換のプレースホルダ」警告 | `--domain` / `--description` 等の引数未指定 | `--domain "<ラベル>"` を追加して再実行（warn_and_document なのでブロックはしない） |
| `<usecase>-architect.md` が雛形のまま | `/aid-architect-author` 未実行 | `/aid-architect-author <usecase>` を実行 |
| Notion MCP タイムアウト | WSL2 環境・トークン期限切れ | `mcp-setup-guide.md` のエラーハンドリング 3 パターン参照（ローカルキャッシュフォールバック / トークン更新） |
| `/aid-dp-register` で命名衝突 | `DP-NNN` 形式と被る・既存 ID と被る | プレフィックス付き `DP-<USECASE>-NNN` 形式に変更 / 連番を +1（ユーザ確認のうえ） |
| `validate-plugin.sh` で二重波括弧プレースホルダ警告 | 本文中で `{` を 2 つ並べた表記が残っている | 全角 `｛｛…｝｝` または「二重波括弧」と日本語表記に書き換え |
| 「`schemas/` が symlink ではありません」 | scaffold 時にシンボリックリンクが実体化された | `rm -rf schemas && ln -s ../../xtone-shared-plugin/schemas/v1 schemas` で再作成 |
| 自プラグイン（本プラグイン）の修正で起動できない | 循環参照リスク | 修正前のバージョンに git revert し、ADR-AID-001 の運用に従い再修正（**修正前に他プラグインの再生成が通ることを必ず確認**） |

## 9. 関連

- 本プラグインの作業ガイド（CONV-06 6項目）: [`../skills/aid-skill-creator-plugin-guide/SKILL.md`](../skills/aid-skill-creator-plugin-guide/SKILL.md)
- 判断ポイント詳細: [`./decision-points.md`](./decision-points.md)
- 未決事項: [`./pending-decisions.md`](./pending-decisions.md)
- リファレンス実装: [`../../xtone-auth-plugin/`](../../xtone-auth-plugin/)
- マスターテンプレ: [`../../../xtone-plugin-template/`](../../../xtone-plugin-template/)
- スキーマ共有元: [`../../../xtone-shared-plugin/`](../../../xtone-shared-plugin/)
- プラグイン開発者ガイド: [`../../../docs/plugin-developer-guide.md`](../../../docs/plugin-developer-guide.md)
- Notion DB 一覧: [`../../../docs/notion-db-catalog.md`](../../../docs/notion-db-catalog.md)
- MCP 設定: [`../../../docs/mcp-setup-guide.md`](../../../docs/mcp-setup-guide.md)
