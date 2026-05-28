---
name: aid-plugin-scope-extraction
description: 新規 AIデリバリプラグイン（T-023〜T-045 Rollout 対象ユースケース）のヒアリングから plugin-scope.json を生成するスキル。プラグインの要件定義フェーズ（/req-collect 相当）で、usecase / モジュール / 適用ドメイン / フェーズ別 Skill 候補 / 横断機能候補 / 既存資産参照 / 既知 DP 候補 / sample-cases 候補を漏れなく洗い出したいときに使う。Notion 16 DB を引き、xtone-auth-plugin をリファレンスとする。
---

# AID Plugin Scope Extraction Skill

> SKL-12: `description` は Claude が Skill を選ぶための主要判断材料。3要素（何を / いつ / どんな条件で）を含む。

## 概要

新規 AIデリバリプラグインの担当者ヒアリング（自然言語の説明・既存資料の URL・周辺案件への言及）から、**プラグインそのもののスコープ**を抽出し `delivery/plugin-scope.json` に落とす。これは `aid-plugin-architecture-design` Skill（と `aid-skill-creator-architect` Subagent）の入力になる。

> **注意**: 出力は通常の `requirements.schema.json`（エンドユーザ向けソフトウェア要件）ではなく、**プラグインそのもののメタ要件**（どんな Skill / Subagent / DP が必要か）。スキーマ検証の対象外であるため `delivery/plugin-scope.json` という別名で出力する（validate-plugin.sh の `requirements*.json` パターンに合致させない）。

## 入出力

- **入力:**
  - ユースケース担当者の説明テキスト（自然言語）
  - 関連する既存案件・社内資産の URL / リポジトリ参照
  - （オプション）Notion 「プロセス棚卸しDB」「型化資産インベントリDB」「ドメインタクソノミーDB」「モジュールカタログスキーマDB」
- **出力:**
  - `delivery/plugin-scope.json`（後述スキーマ）
  - 質問が残れば `docs/pending-decisions.md` に追記（warn_and_document）

## `delivery/plugin-scope.json` のフィールド

```jsonc
{
  "usecase": "payment",                              // kebab-case, 小文字英数+ハイフン
  "plugin_name": "xtone-payment-plugin",             // generate-plugin.sh の出力に合わせる
  "module_candidates": ["MOD-007"],                  // MCS-DB から該当 ID を引く。新規なら "MOD-NEW-xxx"
  "applicable_domains": ["EC・D2C", "イベントLP"],   // T-008 ドメインタクソノミーから選択
  "phase_skill_candidates": {
    "requirements": ["payment-requirements-extraction"],
    "design":       ["payment-design"],
    "implementation": ["payment-stripe-setup", "payment-frontend"],
    "test":         ["payment-e2e-verify"]
  },
  "cross_cutting_candidates": [                      // 2 層以上にまたがる Skill 候補（B-19）
    {
      "name": "payment-webhook-handler",
      "spans": ["backend", "iaas"],
      "kind": "feature-spanning",                    // ADR-AID-003 想定（feature / environment / concern の 3 種）
      "rationale": "決済完了通知の受け口は backend と iaas にまたがる"
    }
  ],
  "stack_candidates": {                              // 言語別 references で初期に必要なスタック見立て
    "implementation": ["rails", "nextjs"]
  },
  "reference_assets": [                              // 学習用に必ず参照する既存資産
    "plugins/xtone-auth-plugin",
    "xtone-shared-plugin/schemas/v1/design.auth.schema.json"
  ],
  "known_dp_candidates": [                           // 既知の判断ポイント。再利用 vs 新規候補
    { "id": "DP-007",            "reuse": false, "reason": "認証用なので決済では再利用しない" },
    { "id": "DP-PAYMENT-DRAFT-01", "reuse": false, "reason": "新規候補: 決済プロバイダ選択（Stripe/GMO/Komoju）" }
  ],
  "sample_case_candidates": ["ec-d2c-app", "event-campaign-lp"],  // sample-cases/ から該当案件
  "sample_case_legacy": null,                                     // 既存プラグインの後追い起稿時のみ使用（FINDING-02 / B-21 以前の独自案件並存）
                                                                  // 例: { "name": "bookclub-app", "location": "sample-inputs/bookclub-app.requirements-input.md", "rationale": "B-21 以前の独自案件・経緯保存のため並存" }
  "client_work_constraints": {                       // クライアントワーク固有制約（Rollout共通方針4）
    "nda": null, "vendor_coordination": null, "release_window": null,
    "security_review": null, "budget_cap": null
  },
  "scenarios": {                                     // 共通方針1（新規 + 既存改修）
    "new": true,
    "existing_modification": false                   // 既存改修も対象にするか
  },
  "undecided": [
    { "field": "module_candidates", "reason": "MOD-007 が新規候補に該当するか MCS-DB 確認待ち" }
  ]
}
```

`undecided` に残った項目は `docs/pending-decisions.md` にも追記する（warn_and_document）。

## 抽出チェックリスト

ヒアリングテキストを読みながら以下を必ず確認し、`delivery/plugin-scope.json` に反映する。

### usecase と命名

- [ ] usecase 名は `[a-z][a-z0-9-]*`（小文字英数とハイフン）を満たすか
- [ ] `xtone-<usecase>-plugin` の最終名で既存プラグインと衝突しないか
- [ ] usecase は単独で意味が通るか（複合ドメインなら分割を提案）

### モジュール候補（MCS-DB 参照）

- [ ] Notion 「モジュールカタログスキーマDB」を検索し、該当 MOD-XXX があれば再利用
- [ ] 該当ゼロなら新規 `MOD-NEW-<usecase>` を仮置きし、`undecided` に MCS-DB 起票待ちと残す

### 適用ドメイン候補（T-008 ドメインタクソノミー）

- [ ] Notion 「ドメインタクソノミーDB」を検索し、該当ドメインタグを選定（1 件以上）
- [ ] 該当ゼロなら新規ドメイン追加 PR が必要か質問する

### フェーズ別 Skill 候補

- [ ] requirements / design / implementation / test の 4 フェーズについて、最低 1 Skill 候補を挙げる
- [ ] implementation は **複数候補**になることが多い（setup / frontend / 特化機能）。auth プラグインを参考に列挙
- [ ] test スキルはまずスタブでよい（auth プラグインも MVP 時点はスタブだった）

### 横断機能候補（B-19）

- [ ] client / backend / iaas / infrastructure のうち **2 層以上にまたがる機能**を切り出し候補にする（例: `auth-mfa`, `auth-emulator`）
- [ ] 候補があれば `cross_cutting_candidates` に列挙し、`spans` で層を明示
- [ ] **横断の `kind` を判定**（FINDING-01 / ADR-AID-003 候補）：
  - `feature-spanning`: 機能そのものが複数層にまたがる（例: `firebase-auth-mfa` = enrollment(client) / 検証・強制(backend) / SDK(iaas)）
  - `environment-spanning`: 実行環境が複数層にまたがる（例: `firebase-auth-emulator` = Docker(infrastructure) / 署名検証スキップ(backend) / connectAuthEmulator(client)）
  - `concern-spanning`: 関心事（observability / privacy / audit 等）が複数層にまたがる
- [ ] `rationale` に「なぜ横断なのか」を 1〜2 文で記録

### 既存資産参照（auth プラグインからの流用）

- [ ] `xtone-auth-plugin/` の Skill / agent / command / template から流用候補をリストアップ
- [ ] 流用候補は `reference_assets` に絶対パスで記録

### 既知の判断ポイント候補（DP-DB 検索 / DP-AID-02 適用）

- [ ] Notion DP-DB を `usecase` 関連語で検索し、再利用候補を `known_dp_candidates` に並べる
- [ ] 80% 以上重複する既存 DP があれば `reuse: true`、それ以外は新規候補（`DP-<USECASE>-DRAFT-NN`）として並置
- [ ] AI は新規 DP を勝手に起票しない（起票は `/aid-dp-register` で人間確認を経る）

### sample-cases 候補（B-21 / DP-AID-03）

- [ ] `xtone-shared-plugin/sample-cases/` のディレクトリから該当案件を 1〜3 件選定
- [ ] 該当ゼロなら新案件追加 PR を提案し、`undecided` に残す
- [ ] **既存プラグインの後追い起稿の場合のみ**（新規 Rollout では通常空）：
  - B-21 以前に独自 `sample-inputs/` を持つプラグイン（例: auth プラグインの `bookclub-app`）は `sample_case_legacy` に並記
  - `sample_case_legacy = { name, location, rationale }`（経緯保存のため・カタログ運用と並存）
  - 詳細は FINDING-02 を参照

### クライアントワーク固有制約（Rollout 共通方針 4）

- [ ] NDA / 外注パートナー連携 / 納期制約 / セキュリティ要件 / 予算制約のうち、ヒアリングで言及されたものを `client_work_constraints` に記録
- [ ] 言及がなくても要確認なら `undecided` に残す

### シナリオ（共通方針 1 / T-002 拡張）

- [ ] 新規開発のみか、既存改修も対象か
- [ ] 既存改修対象の場合は「既存コードの読み取り」フェーズが requirements 前段に必要になる旨を `undecided` で明示

## 手順

1. ヒアリングテキストと参照 URL を読み、上のチェックリストを順に当てる。
2. **Notion 16 DB を引く**（Notion MCP 必須）。MCS / ドメインタクソノミー / DP-DB / プロセス棚卸し / 型化資産インベントリを優先。
3. リファレンス実装 `xtone-auth-plugin/skills/auth-plugin-guide/SKILL.md` を必ず参照し、フェーズ別 Skill 候補の数とフレーズの粒度を合わせる。
4. 不足・曖昧な点は人間に質問する。判断が必要な点は AI が決めず `undecided` に残す。
5. `delivery/plugin-scope.json` を書き出す（既存ファイルがあれば diff を取って差分を明示）。
6. `undecided` 配列に項目があれば `docs/pending-decisions.md` にも該当行を追記する（warn_and_document）。

## 判断ポイント（人間判断をスルーさせない）

要件抽出段階で確定しないメタ設計方針は AI が決めない。特に以下：

- **DP-AID-01**: 横断機能を独立 Skill にするか / 既存 Skill 拡張にするか → 推奨だけ提示
- **DP-AID-02**: 既存 DP の再利用 vs 新規 DP 起票 → 80% 重複ルールで判定、迷ったら人間
- **DP-AID-03**: sample-cases 該当ゼロのときの新案件追加 → 提案のみ、PR は別タスク
- **DP-AID-05**: domain-architect が必要か → 比較対象スタック 2 つ以上で「必要」推奨

未決は `delivery/plugin-scope.json` の `undecided` と `docs/pending-decisions.md` に残し、次フェーズ（`/aid-skill-creator-design`）の `aid-skill-creator-architect` Subagent が引き継ぐ（T-002 warn_and_document）。

## メタゆえの留意点

- **このスキルは「プラグインそのものの要件抽出」を行う**。エンドユーザ向けソフトウェアの要件抽出（`auth-requirements-extraction` 等）と混同しない。出力ファイル名を `plugin-scope.json` にしているのはそのため。
- **`xtone-auth-plugin` 自体は本スキルを通っていない**（B-19 以前に手で書かれた）。リファレンスとしてのみ参照し、新規プラグインは必ず本スキル経由で立ち上げる。
- 既存資産インベントリ（Notion DB）に古い棚卸しが残っている場合がある。**実物のリポジトリを必ず参照**して整合させる（メモリと現在の状態が食い違うときは現状優先・CLAUDE.md 鉄則）。
