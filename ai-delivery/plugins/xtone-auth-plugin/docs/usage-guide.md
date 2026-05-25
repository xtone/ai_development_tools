# xtone-auth-plugin 使い方ガイド

認証モジュール（MOD-001）を「要件定義 → 設計 → 実装」の垂直スライスで型化するプラグインの使い方。MVP は Firebase Auth、IaaS 差し替え可能設計が前提（T-004 本決定）。

## 1. インストール / ロード

開発中はセッション限定でロードして試せる:

```bash
# ai-delivery/ で
claude --plugin-dir plugins/xtone-auth-plugin
```

検証のみ:

```bash
claude plugin validate --strict plugins/xtone-auth-plugin
```

## 2. 基本フロー

```
/req-collect   # 要件定義（認証要件の抽出は auth-requirements-extraction スキル）
   ↓
/auth-design   # 認証設計（authentication-architect が DP-007/008/015 を比較・推奨）
   ↓
/implement     # 実装計画と認証アダプタ実装（firebase-auth-setup スキル）
```

補助コマンド: `/decide`（判断記録）/ `/status`（進捗）/ `/next`（次アクション）/ `/pending-list`（未決一覧）/ `/skip-review`（AIレビュー）。

> 汎用設計でよい場合は `/design`、認証ドメイン特化は `/auth-design`。

## 3. 成果物（スキーマ）

| フェーズ | コマンド | 出力スキーマ |
|---|---|---|
| 要件定義 | `/req-collect` | `schemas/requirements.schema.json` |
| 設計 | `/auth-design` | `schemas/design.schema.json`（+ `docs/adr/ADR-NNN.md`） |
| 実装 | `/implement` | `schemas/implementation-plan.schema.json` + 実装コード |

`schemas/` は xtone-shared-plugin への symlink（編集不可, CONV-14）。

## 4. 判断ポイント（人間判断をスルーさせない）

| DP | 内容 |
|---|---|
| DP-007 | 認証スタック選択（Firebase Auth 推奨 + 代替比較・差し替え可能設計） |
| DP-008 | MFA 要件の振り分け |
| DP-015 | dAccount / docomo 規約の適用範囲 |

詳細は [`decision-points.md`](./decision-points.md)。AI は決めず推奨だけ提示。未決は各スキーマの `undecided` と [`pending-decisions.md`](./pending-decisions.md) に残る（warn_and_document, T-002）。フェーズ移行時に未決があると pre-phase-transition Hook が警告する（ブロックはしない）。

## 5. 通し検証（架空案件の作り込み例）

`sample-inputs/` の架空案件入力から、`sample-outputs/` に要件→設計→実装計画の成果物例が入っている。新規案件を始める際の雛形・期待値として参照する。詳細は [`../sample-outputs/README.md`](../sample-outputs/README.md)。

## 6. 差し替え可能設計（他 IaaS 追加）

Firebase 固有処理は `AuthAdapter` 実装に閉じ込める。別 IaaS（Cognito / Auth0 / Devise 等）追加時はアダプタ実装の差し替えで対応する（Rollout フェーズで実証）。
