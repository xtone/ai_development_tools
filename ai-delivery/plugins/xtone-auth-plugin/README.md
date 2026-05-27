# xtone-auth-plugin

Xtone AIデリバリシステムの **認証モジュール（MOD-001）** プラグイン。認証を「要件定義 → 設計 → 実装」の垂直スライスとして型化する MVP（T-021）。中核価値は **「人間の判断を要するポイントをスルーさせない」**。

- **MVP スコープ**: Firebase Auth 1パターン（T-004 本決定）。他 IaaS（Cognito / Auth0 / Devise 等）は **差し替え可能な設計**を前提にスコープ外。
- **生成元**: マスターテンプレ `xtone-plugin-template`（T-019）+ 認証特化（T-021）。

## クイックスタート

```bash
# ai-delivery/ で（セッション限定ロード）
claude --plugin-dir plugins/xtone-auth-plugin

# 検証
claude plugin validate --strict plugins/xtone-auth-plugin
```

フロー: `/req-collect → /auth-design → /implement`。詳細は [`docs/usage-guide.md`](./docs/usage-guide.md)。

## 構成

| パス | 内容 |
|---|---|
| `.claude-plugin/plugin.json` | プラグイン定義（標準フィールドのみ） |
| `skills/auth-plugin-guide/` | 作業ガイド・鉄則・判断ポイント（運用 context。ルート CLAUDE.md は置かない＝DP-27 本決定） |
| `agents/` | 7 Subagent（基盤6 + authentication-architect） |
| `commands/` | 9 Slash Command（基盤8 + auth-design） |
| `skills/` | auth-plugin-guide（ガイド）+ requirements / design / implementation（実動）+ test（スタブ） |
| `hooks/` | hooks.json + 4 Hook（warn_and_document） |
| `schemas/` | xtone-shared-plugin への symlink（編集不可, CONV-14） |
| `docs/` | decision-points / usage-guide / pending-decisions / adr |
| `sample-inputs/` | 架空案件の入力例（成果物 `sample-outputs/` は B-13 一連の型化修正完了後に再生成予定。`docs/backlog.md` B-14 参照） |
| `.github/` | PR テンプレート・CI |

## 判断ポイント

- **DP-007** 認証スタック選択（Firebase Auth 推奨 + 代替比較）
- **DP-008** MFA 要件の振り分け
- **DP-015** dAccount / docomo 規約の適用範囲
- **DP-28** 退会済みアカウントの再登録ポリシー（MVP 既定推奨 = 403 拒否）

詳細は [`docs/decision-points.md`](./docs/decision-points.md)。

## 関連

- 親プロジェクト: [`../../README.md`](../../README.md) / [`../../CLAUDE.md`](../../CLAUDE.md)
- スキーマ共有元: `../../xtone-shared-plugin/`
- マスターテンプレ: `../../xtone-plugin-template/`
