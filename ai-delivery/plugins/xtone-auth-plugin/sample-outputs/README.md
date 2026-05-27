# 作り込み例（架空案件の通し検証）— sample-outputs

架空案件 [「みんなの読書会」](../sample-inputs/bookclub-app.requirements-input.md) を xtone-auth-plugin で **要件定義 → 設計 → 実装計画**まで通した成果物例。

> 本ディレクトリは **B-14（[#155](https://github.com/xtone/ai_development_tools/issues/155)）で再生成**された版。B-13 で旧サンプルを削除した後、B-11/B-12/B-13/B-15 一連の型化修正（新スキーマ・新スキル群）が完了したタイミング（2026-05-27）で 1 から作り直し。

## 通しフローと成果物

| フェーズ | コマンド / スキル | 成果物 | スキーマ |
|---|---|---|---|
| 要件定義 | `/req-collect` → `auth-requirements-extraction` | [`requirements.json`](./requirements.json)（**`page_access_control_candidates` を含む**、B-13） | `requirements.schema.json` |
| 設計 | `/auth-design` → `firebase-auth-design` / `authentication-architect` | [`design.yaml`](./design.yaml) + [`ADR-001-auth-stack.md`](./ADR-001-auth-stack.md) | `design.schema.json`（**`responsibility_split` / `page_access_control` / `local_dev_stack` を含む**、B-03/B-13） |
| 実装 | `/implement` → `implementation-skill-planner` → `tech-version-check` → `firebase-auth-setup` / `-frontend` / `-mfa` / `-emulator` → `auth-e2e-verify` | [`implementation-plan.json`](./implementation-plan.json)（**`skill_plan` を含む**、B-13） | `implementation-plan.schema.json` |

## この例が示していること（DoD 対応）

- **架空案件で要件定義〜実装まで一貫して進められる**: 上記 3 成果物が `page_access_control` / `responsibility_split` / `local_dev_stack` / `skill_plan` のフィールド名で **同一名のまま引き継ぎ**、フェーズ間の食い違いが出ない（B-13 で塞いだ穴）。
- **2 種類以上の認証スタックを比較**: [ADR-001](./ADR-001-auth-stack.md) で Firebase Auth と Devise+OmniAuth（+ Cognito）を比較し、根拠付きで採用を決定。
- **未決判断ポイントが warn_and_document される**:
  - `requirements.json` の `undecided` は `["DP-007", "DP-008"]`（要件段階では認証スタックと MFA 方針が未決）
  - 設計フェーズで人間（豊田）が DP-007/008/015 を決定し、`design.yaml.decision_record` に記録、`undecided` は `[]` に解消
  - `implementation-plan.json` の `undecided` も `[]`
- **`skill_plan` で全スキルが計画される**（B-13）: 最先頭 `tech-version-check`（B-11）→ `firebase-auth-setup` / `-frontend` / `-mfa` / `-emulator` → 最末尾 `auth-e2e-verify`（B-15）の流れ。設計フェーズで `responsibility_split.client` を含めば planner が **必ず `firebase-auth-frontend` を列挙**するので、サンプル案件 sample-auth で起きた「frontend スキル素通り」事故は再発しない。
- **ローカル開発は Emulator + Docker 既定**（B-12）: `design.yaml.local_dev_stack=emulator_docker` で planner が `firebase-auth-emulator` を必ず列挙。
- **architecture.stack と recipe の整合**: `architecture.stack` が React (Web SPA) なので `firebase-auth-frontend.recipe=nextjs`（Bearer 直送り）を流用、`firebase-auth-mfa.recipe=rails+nextjs` で揃う（PR #154 で確認した整合性問題に対応）。

## 注記

- `design.yaml` は DoD 記載の「design.yaml サンプル」。同内容を JSON 化すれば `design.schema.json` で検証できる（B-14 の検証スクリプトで実施、PR description / コミット参照）。
- 実際に動く Rails + Firebase のサンプルアプリ実装は **T-022 内部パイロット**および **再パイロット**の範囲（[`docs/pilot-report.md`](../docs/pilot-report.md) / [`docs/re-pilot-report.md`](../docs/re-pilot-report.md) 参照）。本ディレクトリはあくまで「設計フェーズまでの成果物テンプレ」。
- iOS / Android（Swift / Kotlin）レシピは未整備のため、`skill_plan.firebase-auth-frontend` の trigger に「判断ポイント」として記録（pending-decisions への起票は実装フェーズ着手時）。

## 関連 backlog

- B-14（本サンプル再生成、[#155](https://github.com/xtone/ai_development_tools/issues/155)）
- B-11（[#156](https://github.com/xtone/ai_development_tools/issues/156) tech-version-check）
- B-12（[#157](https://github.com/xtone/ai_development_tools/issues/157) Emulator+Docker 既定）
- B-13（[#153](https://github.com/xtone/ai_development_tools/issues/153) skill_plan 機構）
- B-15（[#158](https://github.com/xtone/ai_development_tools/issues/158) auth-e2e-verify）
