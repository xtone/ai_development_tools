# プラグイン開発者ガイド

このドキュメントは、AIデリバリシステムで **新しいプラグインを作る / 既存プラグインを拡張する**開発者向け。リファレンス実装である認証プラグインで確立した型を使い、自分のドメインのプラグインを実装するために必要な情報をここに集約する。

> **対をなすガイド**: プラグインを*使う*側（案件チーム）は [`plugin-user-guide.md`](./plugin-user-guide.md)。

## このガイドの読者

- 新しいドメイン（管理画面 / コンテンツ配信 / 決済 / 通知 / コミュニティ 等）のプラグインを担当する開発者
- 既存プラグインに新スキルを追加する開発者

## 0. 中核価値（必読）

プラグインは以下の鉄則に従って動くように設計する:

1. **判断の根拠を残す。** スキルや成果物の中で「なぜそうしたか」を ID（CONV / DP / ADR 等）参照やコメントで明示する。
2. **判断ポイントは「気づいたその場で」記録。** 後でまとめない。実装中に「ここは人間が決めるべき」と気づいたら即 `pending-decisions.md` に追加する。
3. **CI / Hook / Subagent は警告のみ・ブロックしない**（warn_and_document）。フェーズ移行を止めず、未決はドキュメントに残して人間が判断する時間を確保する。
4. **共通スキーマは編集しない**（Single Source of Truth）。`xtone-shared-plugin/schemas/v1/` への symlink を介してのみ参照する。

中核価値は「**人間の判断を要するポイントをスルーさせない**」こと。これに反する設計をしないこと。

## 1. プラグインの作り方（手順）

### Step 1: マスターテンプレからコピー

```bash
cd ai-delivery
cp -r xtone-plugin-template plugins/xtone-<your-domain>-plugin
```

将来 `xtone-plugin-template/scripts/generate-plugin.sh` が整備されたら、それを使ってボイラープレートを一気に生成できる予定。

### Step 2: プラグイン構造に従う

```
plugins/xtone-<domain>-plugin/
├── .claude-plugin/plugin.json     # Claude Code 標準フィールドのみ
├── README.md                      # 人間向け概要
├── agents/                        # Subagent（基盤 6 + ドメイン特化）
├── commands/                      # Slash Command（基盤 8 + ドメイン特化）
├── hooks/                         # hooks.json + Hook（warn_and_document）
├── skills/
│   ├── <domain>-plugin-guide/SKILL.md   # 運用ガイド（プラグインの読者向け context は skill 化する）
│   ├── requirements/<domain>-requirements-extraction/
│   ├── design/<domain>-design/ (+ templates/)
│   ├── implementation/<domain>-setup/ (+ references/)
│   └── implementation/<domain>-frontend/ など
├── schemas/                       # xtone-shared-plugin への symlink（編集不可）
├── docs/                          # decision-points / usage-guide / pending-decisions / adr
├── sample-inputs/                # 架空案件の入力例（成果物 sample-outputs/ は型化完了後に再生成）
└── .github/                       # PR テンプレ・CI
```

> プラグインの**ルート `CLAUDE.md` は置かない**。Claude Code はプラグインルートの `CLAUDE.md` を自動 context として読まないため、運用ガイドは `skills/<domain>-plugin-guide/SKILL.md` に集約する。

### Step 3: スキル設計の原則（言語非依存契約 + references）

リファレンス実装である認証プラグインで確立した型:

- **`SKILL.md` は言語/FW 非依存の「契約」と「手順」**を定義
- 具体コードは `references/<stack>.md`（言語別レシピ）に分離
- レシピを追加するときは契約を変えない（差し替え可能設計を維持）
- **「既知の制約」を徹底的に明文化**（後続の開発者が同じ穴を踏まないため）
- **「要件で別指定があれば要件優先」**を全層で明記

### Step 4: 判断ポイントの追跡

- 案件で出てくる判断は、既存の判断ポイントを再利用するか新規起票
- 新規判断ポイントはプラグインの `docs/pending-decisions.md` に起票 → スキル側に「**未決のまま実装に来た場合は確定せず残す**」と明記
- フェーズ移行時に `undecided` が残ると pre-phase-transition Hook が**警告**（ブロックはしない）

### Step 5: パイロット → 訂正バックログ → 再パイロット

認証プラグインで型化した検証サイクル（同じやり方を他プラグインでも踏む）:

1. **架空案件**で要件 → 設計 → 実装を 1 本通す
2. 発見事項を `pilot-report.md` に列挙（成功事例 + 失敗・摩擦）
3. 訂正タスクを `backlog.md` ＋ GitHub Issue 化（High / Med / Low）
4. High を解消した後で**再パイロット**（前回と異なる条件で）
5. 再判定でリリース可否を決める

#### 架空案件カタログ（`xtone-shared-plugin/sample-cases/`）から借りる

T-021 認証プラグインのパイロットは `bookclub-app` という独自の架空案件 1 本で通した。23 個の Rollout プラグイン（T-023〜T-045）でも同じ Verification が要るが、プラグインごとに別案件を作ると同じ案件が認証では使えても決済では使えないといった整合性崩れが起きる。

そのため、**業種別の架空案件カタログ**を [`xtone-shared-plugin/sample-cases/`](../xtone-shared-plugin/sample-cases/) に集約してある（EC / D2C / MaaS / メディア / 教育バウチャー / コーポレートサイト / 業務 SaaS / イベント LP の 7 業種）。各プラグインは、自分のユースケースが該当する案件を**カタログから symlink で取り込んでパイロットの入力にする**。

| ステップ | やること |
|---|---|
| 1 | [`sample-cases/README.md`](../xtone-shared-plugin/sample-cases/README.md) の「案件 × ユースケース マトリクス」で、自分のプラグインに該当する案件を選ぶ（複数選択可・1 件以上） |
| 2 | プラグインの `sample-inputs/` に symlink を張る（リンク名はカタログ側のディレクトリ名と一致させる） |
| 3 | プラグイン固有の追加ヒアリングが必要なら `sample-inputs/<case-name>.notes.md` を並置する（カタログ本体は編集しない） |

```bash
# 例: 決済プラグインが ec-d2c-app と event-campaign-lp を使う
cd plugins/xtone-payment-plugin/sample-inputs
ln -s ../../../xtone-shared-plugin/sample-cases/ec-d2c-app ec-d2c-app
ln -s ../../../xtone-shared-plugin/sample-cases/event-campaign-lp event-campaign-lp
```

各案件は `requirements-input.md`（自然言語のヒアリングメモ）と `requirements.json`（`requirements.schema.json` 準拠の構造化要件）を持つ。`/req-collect` 系スキルの入力には `requirements-input.md` を、後段の design / implementation スキルが直接入力にする場合は `requirements.json` を使う。

`validate-plugin.sh` は `sample-inputs/` 配下の symlink について **xtone-shared-plugin/sample-cases/ を指している symlink が壊れていないか**を warn_and_document でチェックする。壊れている / 通常ファイルになっていると警告（exit 1 にはしない）。

> **既存 `bookclub-app` の扱い**: 認証プラグインに先行運用していた [`plugins/xtone-auth-plugin/sample-inputs/bookclub-app.requirements-input.md`](../plugins/xtone-auth-plugin/sample-inputs/bookclub-app.requirements-input.md) は **そのまま残す（並存）**。リファレンス実装の経緯保存のため。新規 Rollout プラグインの Verification では原則として本カタログを使う。
>
> 該当する案件がカタログにない場合は、本カタログに**新案件を追加して PR**する（カタログ更新は本ガイドの責務）。プラグイン内で個別案件を抱えるよりカタログ追加が優先。

## 2. 認証プラグインから学べる設計パターン（必読）

リファレンス実装である [`xtone-auth-plugin`](../plugins/xtone-auth-plugin/) はパイロット → 訂正 → 再パイロットを経てリリース判定済み。設計判断の根拠は再パイロット報告と一連の PR に残っているので、自分のドメインでも踏襲する。

### 2.1 横断機能は独立スキルにする

backend / client / iaas のどれか 2 つ以上にまたがる機能は、既存スキルに無理に詰めず**独立スキル**にする。

- `firebase-auth-mfa` — enrollment(client) / 検証・強制(backend) / iaas にまたがる
- `firebase-auth-emulator` — Docker / 署名検証スキップ / `connectAuthEmulator` にまたがる

スキル内部で `responsibility_split` を表で示し、何が client / backend / iaas / shared かを明示する。

### 2.2 言語非依存契約 + references レシピ

すべてのスキルは「契約」と「実装手段」を分離する:

| 層 | 役割 |
|---|---|
| `SKILL.md` | 言語非依存の契約・手順・既知の制約・判断ポイント |
| `references/<stack>.md` | 言語/FW 別の具体コード（例: rails.md / nextjs.md / hotwire.md） |

別言語が増えても契約は不変。新言語のレシピを追加するだけ。

### 2.3 既知の制約は徹底的に明文化

後続の開発者が同じ穴を踏まないように、スキル側にすべて書く:

- 例: `firebase-auth-mfa/SKILL.md` の「**`auth_time` は MFA enrollment で更新されない**」 / 「**emulator は `emailVerified=true` が前提**」
- これらは再パイロットで実機の不具合として顕在化し、根本対応（2 段階失効）でスキルに反映された

### 2.4 「要件で別指定があれば要件優先」を全層で明記

スキル既定パターン（例: フロント 3 パターンの protected/public-aware/guest、デフォルトページ一覧）を作るときも、**案件で別指定があれば要件優先**を必ず書く:

- `design.responsibility_split` や `page_access_control` で逸脱を明示
- `decision_record` に逸脱根拠を残す
- warn_and_document に沿わせる

### 2.5 実機 E2E まで通す

test スタブのみだと**型の穴を見逃す**。Docker + emulator + Playwright で実機まで通すと、再パイロットでの発見（auth_time 仕様の不具合）が拾える:

- backend は TestAdapter で結合テスト（実 IaaS 不要）
- frontend は tsc / build を通す
- ローカル E2E は Docker emulator（複数サービスを compose で起動）
- ブラウザ動作確認は最小 UI で実プロンプト経由

### 2.6 不具合は「再現 + 原因特定 + スキル根本対応」までセットで

実機で不具合を踏んだら、スキルの型を直すまでが 1 タスク。認証プラグインの auth_time 不具合は **Playwright で再現 → 原因（Firebase 仕様）特定 → スキルの 2 段階失効化**まで進めた。これにより他案件での再発を防ぐ。

### 2.7 ドメイン特化 Subagent（domain-architect）を最初から用意する

T-021 認証プラグインでは、基盤の `designer`（SCH-2）を認証ドメインに特化させた `authentication-architect` を新設し、`/auth-design` で起動する型を確立した（複数スタックを比較し、IaaS / プロバイダ差し替え可能設計を担保）。**T-023〜T-045 の 23 Rollout プラグインでも同じ型が必要**になる（例: 決済 → `payment-architect` / 位置情報 → `geo-architect` / IaC → `iac-architect` / API 仕様 → `api-spec-architect`）。

そのため、雛形を `xtone-plugin-template` 側に置いてある:

| ファイル | 生成後 | 役割 |
|---|---|---|
| `xtone-plugin-template/agents/domain-architect.md.template` | `agents/<usecase>-architect.md` | ドメイン特化 Subagent（基盤 designer の特化版） |
| `xtone-plugin-template/commands/domain-design.md.template` | `commands/<usecase>-design.md` | 上記 Subagent を起動する Slash Command |

**置換プレースホルダ**（`generate-plugin.sh` が処理）:

| プレースホルダ | 置換内容 | 例 |
|---|---|---|
| `{{usecase}}` | ユースケース名 | `payment`, `geo`, `iac`, `api-spec` |
| `{{domain}}` | ドメインの自然言語ラベル（`--domain` で渡す） | `決済`, `位置情報`, `CI/CD・IaC`, `API 仕様` |

**フラグ**:

- 既定: 上記 2 ファイルを自動で実体化する（23 Rollout プラグインで毎回作成する想定のため）
- `--no-domain-architect`: 実体化しない（プラグインに{{usecase}}-architect が不要なケース）
- `--domain "<ラベル>"`: `{{domain}}` を置換。省略時は未置換のまま残り、`validate-plugin.sh` で警告（warn_and_document）

**生成後の埋め直し作業（必須）**: 雛形は DP セクションが骨格のため、各プラグインで以下を埋める。

1. **主要 DP**（`<usecase>-スタック選択`）の DP-XXX を割り当て、選択肢・判断軸・MVP 推奨を具体化する
2. **案件固有の DP**（適用判定する規約・MFA 等の方針）を追加する
3. `MOD-XXX` / `T-XXX` を該当 ID で置き換える
4. リファレンス実装: [`plugins/xtone-auth-plugin/agents/authentication-architect.md`](../plugins/xtone-auth-plugin/agents/authentication-architect.md)

> 認証プラグイン自身は B-19 以前に手で書いた `authentication-architect.md` / `auth-design.md` を保持している（usecase が `auth` でも agent 名は `authentication-architect`）。本テンプレを使うと `<usecase>-architect` 形式に揃うため、既存実装との文字列差は許容したうえで構造（役割・入出力・DP 比較・差し替え可能設計の明示）の等価性を担保する。

## 3. ドメイン拡張フィールドの追加方法（B-20 / #173）

`design.schema.json` 等の共通スキーマは**ドメイン非依存の共通部分のみ**を持つ（B-20 でドメイン汎用化）。決済・通知・MaaS・IaC など、各プラグイン固有のフィールドは次のいずれかで追加する。**ここに書かれていない経路で共通スキーマを直接編集してはならない**（CONV-14: Single Source of Truth）。

### 3.1 どちらの経路を使うか

| 経路 | 用途 | 例 |
|---|---|---|
| **(A) `domain_specific` スロット** | 軽量・少数のフィールド、構造化が浅い | 数個の boolean フラグ・ID・URL |
| **(B) `design.<domain>.schema.json` を追加** | 構造化が必要・配列・enum などで型強制したい | 認証の `page_access_control` / 決済の `payment_provider` ＋ `pci_dss_scope` |

迷ったら **(B)** を選ぶ。後から (A) → (B) への昇格は安全（後方互換あり）だが、逆は壊しやすい。

### 3.2 経路 (A): `domain_specific` を使う

base `design.schema.json` のトップレベルに `domain_specific` という自由形式オブジェクトがある。フィールドを増減するだけで済む小さな拡張はここに入れる:

```yaml
domain_specific:
  payment_test_mode: true
  webhook_endpoint: "https://example.com/stripe/webhook"
```

判断ポイント／逸脱理由は通常通り `decision_record` に残す。`domain_specific` 自体は型強制されないため、後で命名が他プラグインと衝突しないよう **プラグイン固有のプレフィックスを推奨**（例: `payment_*`, `notif_*`）。

### 3.3 経路 (B): ドメイン拡張スキーマを追加する

以下の 3 ステップで完結する。

#### Step 1: `design.<domain>.schema.json` を `xtone-shared-plugin/schemas/v1/` に追加

JSON Schema (draft-07) で**ドメイン固有のトップレベルフィールドのみ**を定義する。共通フィールド（`architecture`, `db_schema` 等）は base 側で既に定義されているので**重複させない**。

```jsonc
// xtone-shared-plugin/schemas/v1/design.payment.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://xtone.dev/ai-delivery/schemas/v1/design.payment.schema.json",
  "title": "Design (payment domain extension)",
  "type": "object",
  "required": ["payment_provider"],
  "properties": {
    "payment_provider": {
      "type": "object",
      "required": ["name", "test_mode"],
      "properties": {
        "name": { "type": "string", "enum": ["Stripe", "GMO", "Komoju"] },
        "test_mode": { "type": "boolean" }
      },
      "additionalProperties": true
    },
    "pci_dss_scope": {
      "type": "string",
      "enum": ["SAQ-A", "SAQ-A-EP", "SAQ-D", "none"]
    }
  },
  "additionalProperties": true
}
```

参考実装は [`design.auth.schema.json`](../xtone-shared-plugin/schemas/v1/design.auth.schema.json)。

#### Step 2: プラグインの `plugin.json` に拡張を宣言する

`.claude-plugin/plugin.json` に `delivery.design_extensions` を追加する（配列で複数指定可）:

```json
{
  "name": "xtone-payment-plugin",
  "version": "0.1.0",
  ...,
  "delivery": {
    "design_extensions": ["design.payment.schema.json"]
  }
}
```

#### Step 3: `validate-plugin.sh` で合成検証が通ることを確認する

`validate-plugin.sh` は `delivery.design_extensions` を読み取り、`design*.yaml`／`design*.json` を **base + 各拡張で順に検証する**（B-20）。すべて pass で OK:

```bash
ai-delivery/scripts/validate-plugin.sh ai-delivery/plugins/xtone-payment-plugin --strict
# → ✅ sample-outputs/design.yaml: OK
# → ✅ sample-outputs/design.yaml [+design.payment.schema.json]: OK
```

### 3.4 既存ドメイン拡張一覧

| ドメイン | スキーマ | 主なフィールド |
|---|---|---|
| 認証 | `design.auth.schema.json` | `authentication`, `page_access_control` |

新規ドメインを追加したら本表にも追記する。

### 3.5 やってはいけないこと

- ❌ base `design.schema.json` に **ドメイン固有のフィールド**を追加する（B-20 で剥がす前の状態に戻る）
- ❌ 拡張スキーマで base と**同名のフィールドを再定義**する（合成検証で意図しないバリデーション結果になる）
- ❌ プラグインの `schemas/` 配下に**シンボリックリンク以外のファイル**を置く（CONV-14 違反）
- ❌ 拡張スキーマを `additionalProperties: false` にする（base と合成すると base 由来のフィールドが落ちる）

## 4. 参考実装と便利リンク

- **xtone-auth-plugin（リファレンス実装）**
  - 全体ガイド: [`auth-plugin-guide`](../plugins/xtone-auth-plugin/skills/auth-plugin-guide/SKILL.md)
  - 使い方とプロンプト例: [`docs/usage-guide.md`](../plugins/xtone-auth-plugin/docs/usage-guide.md)（§7 が実プロンプト例）
  - パイロット報告: [`pilot-report.md`](../plugins/xtone-auth-plugin/docs/pilot-report.md) / [`re-pilot-report.md`](../plugins/xtone-auth-plugin/docs/re-pilot-report.md)
  - 訂正バックログ: [`backlog.md`](../plugins/xtone-auth-plugin/docs/backlog.md)
- **共通スキーマ**: `ai-delivery/xtone-shared-plugin/schemas/v1/`（編集不可・symlink で参照）
- **環境前提**: [`environment-setup.md`](./environment-setup.md)（バージョンは固定せず公式の最新安定版）
- **MCP 設定**: [`mcp-setup-guide.md`](./mcp-setup-guide.md)

## 5. レビュー・フィードバックの流れ

### あなたから外への流れ

- **PR レビュー**: AI 自動レビューが先に triage → review で指摘を出すので、Major までは対応してから人間レビュー依頼が効率的
- **新規規約 / 設計判断**: GitHub Issue で提案し、合意後にプラグイン・テンプレ・共通スキーマに反映

### プラグインユーザーからのフィードバックを受ける

[`plugin-user-guide.md`](./plugin-user-guide.md) が案件チームに案内する**フィードバックフォーマット**は次の通り:

- 案件で使って気づいた問題は、プラグインの `docs/backlog.md` 形式（**B-NNN**）で GitHub Issue 起票
- 「症状 / 想定挙動 vs 実挙動 / 影響範囲 / 回避策」を含める
- 開発者は **High（型の穴）/ Med / Low** でトリアージし、リリース並行で消化

認証プラグインの auth_time 不具合はこのフォーマットで「実機再現 → 原因特定 → スキル根本対応」まで到達した好例。プラグインユーザーからの報告も同じ流れで型を改善できる。

## 6. 複数プラグインを並行で開発するときの進め方

- **新しいプラグインのキックオフ**: 担当ドメインの背景を整理し、本ガイドの Step 1〜5 で実装着手
- **複数並行**: 1 人で全部はやらない。プラグインごとに**担当者**を明示する
- **共通基盤の改善**: 複数プラグインで似たパターンが出たら、**`xtone-shared-plugin` / `xtone-plugin-template` に昇格**させて他プラグインで使えるようにする（共通規約への昇格は別途合意プロセスを経る）

---

> **質問・提案**: GitHub Issue（`xtone/ai_development_tools` リポジトリ）。「やりたいことが既存スキルに無い」場合は遠慮なく**新スキル新設**を提案。横断機能なら独立スキル、特定の言語/FW 向けの実装は references レシピに、という分離を意識する。
