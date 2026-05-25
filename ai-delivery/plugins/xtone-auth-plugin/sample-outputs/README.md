# 作り込み例（架空案件の通し検証）— sample-outputs

架空案件 [「みんなの読書会」](../sample-inputs/bookclub-app.requirements-input.md) を xtone-auth-plugin で **要件定義 → 設計 → 実装計画**まで通した成果物例。T-021 DoD [Verification] の実証物。

## 通しフローと成果物

| フェーズ | コマンド / スキル | 成果物 | スキーマ |
|---|---|---|---|
| 要件定義 | `/req-collect` → auth-requirements-extraction | [`requirements.json`](./requirements.json) | requirements.schema.json |
| 設計 | `/auth-design` → firebase-auth-design / authentication-architect | [`design.yaml`](./design.yaml) + [`ADR-001-auth-stack.md`](./ADR-001-auth-stack.md) | design.schema.json |
| 実装 | `/implement` → firebase-auth-setup | [`implementation-plan.json`](./implementation-plan.json) | implementation-plan.schema.json |

## この例が示していること（DoD 対応）

- **架空案件で要件定義〜実装まで進められる**: 上記 3 成果物が一貫してつながる。
- **2 種類以上の認証スタックを選べる**: ADR-001 で Firebase Auth と Devise+OmniAuth を比較し、根拠付きで採用を決定。
- **未決判断ポイントがあれば警告される（warn_and_document）**:
  - `requirements.json` の `undecided` は `["DP-007", "DP-008"]`（要件段階では認証スタックと MFA 方針が未決）。
  - この状態でフェーズ移行すると `pre-phase-transition` Hook が「未決 2 件」を警告する（ブロックはしない）。
  - 設計フェーズで人間（豊田）が DP-007/008/015 を決定し、`design.yaml` の `decision_record` に記録、`undecided` は `[]` に解消。
  - `implementation-plan.json` の `undecided` も `[]`。

## 注記

- `design.yaml` は DoD 記載の「design.yaml サンプル」。同内容を JSON 化すれば design.schema.json で検証できる。
- 実際に動く Rails + Firebase のサンプルアプリ実装は **T-022（内部パイロット）**の範囲（T-021 はプラグイン本体 + 本作り込み例まで）。
