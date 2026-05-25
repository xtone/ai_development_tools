# ADR-001: 認証スタックに Firebase Auth を採用する

- **ステータス**: accepted
- **日付**: 2026-05-25
- **決定者**: 豊田
- **関連判断ポイント**: DP-007 認証スタック選択

> 架空案件「みんなの読書会」の作り込み例。authentication-architect が `templates/ADR.template.md` から生成した想定。

## コンテキスト

BtoC コミュニティアプリ「みんなの読書会」（Web SPA + スマホアプリ、初年度数万人規模）の認証基盤を選定する。メール+パスワード、パスワードレス、Google/Apple OIDC、アカウント連携、退会まで必要。規制業界ではなく docomo 連携もなし。チームは Firebase 利用経験あり。ベンダーロックインは避けたい。

## 選択肢（2 スタックを比較 — DoD「2 種類以上の認証スタックを選べる」）

| 選択肢 | 長所 | 短所 |
|---|---|---|
| **Firebase Auth**（推奨） | メール/パスワードレス/OIDC(Google・Apple) を標準機能で網羅。チームに経験あり。スマホ SDK が充実 | ベンダー依存。細かい挙動カスタムに制約 |
| Devise + OmniAuth | Rails 標準的で自由度が高い。OSS で移行容易 | パスワードレス・Apple ログインは追加実装が必要。スマホ対応の手当てが増える |

（その他 Cognito / Auth0 / NextAuth.js / Laravel Sanctum も DP-007 の選択肢だが、本案件条件では上記 2 案に絞って比較した。）

## 決定

**Firebase Auth を採用する。** 必要なログイン方式を標準機能で満たせ、チーム習熟度が高く MVP を最短で検証できるため。ベンダーロックイン懸念は **AuthAdapter 層**（`FirebaseAuthAdapter`）で認証処理を抽象化し、差し替え可能設計を維持することで緩和する（T-004 本決定の「IaaS 差し替え可能」要件を満たす）。

## 影響

- 別 IaaS への移行は `AuthAdapter` 実装の差し替えで対応（例: `DeviseAuthAdapter`）。Rollout フェーズで実証する。
- DP-008（MFA）は別途決定（オプトイン / 運営管理者必須）。DP-015（dAccount）は本案件では非該当。
