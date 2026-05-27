# ADR-001: 認証スタックに Firebase Auth を採用

- **ステータス**: accepted
- **決定日**: 2026-05-27
- **決定者**: 豊田
- **関連判断ポイント**: DP-007（認証スタック選択）/ DP-008（MFA 方針, `admin_only`）
- **案件**: みんなの読書会（架空、xtone-auth-plugin 通し検証）

## コンテキスト

BtoC コミュニティアプリ（Web SPA + iOS + Android）の認証基盤を選定する。要件は以下:

- メール+パスワード / パスワードレス（メールリンク）/ OIDC（Google・Apple）の 3 方式に対応
- 認証方式の追加（連携）/ パスワード・メール変更 / 退会
- API（Rails）の JWT 認可、Web/アプリでのセッション保持
- 初年度数万人規模、規制業界ではない、docomo 連携なし
- 開発チームは Firebase 経験あり
- ベンダーロックインは避けたい（将来的に別 IaaS へ移行できる余地を残す）
- 運営管理者だけは多要素認証（`admin_only`）で守りたい

## 検討した選択肢

### (A) Firebase Auth（採用）

- メール+パスワード / メールリンク / OIDC（Google・Apple）を **標準機能**でカバー
- 公式 JS / iOS / Android SDK が揃い、トークン発行と検証が安定
- **Identity Platform** にアップグレードで TOTP / SMS MFA を提供（`admin_only` 実装が現実的）
- ローカル検証は **Firebase Auth Emulator** を Docker で起動して完結（B-12）
- 退会時の Admin SDK ユーザー削除、トークン失効、公開鍵キャッシュなどの **運用詳細**は `firebase-auth-setup` スキルが網羅（B-02）

### (B) Devise + OmniAuth + 独自実装

- Rails エコシステムで完結する伝統的な選択肢
- パスワードレス（メールリンク）は独自実装が必要（gem 単体では弱い）
- Apple ログインは OmniAuth Apple の実装と公開鍵検証の自前運用が増える
- スマホアプリのセッション管理は別途設計が必要（gem の SessionsController は Web 向け）
- MFA は Devise 拡張 gem の組合せが必要で、運営管理者強制の実装は自前

### (C) Cognito / Auth0 等の別 IaaS

- 機能面は Firebase Auth と同等以上だが、チームの経験 / コスト / コミュニティ規模で Firebase Auth に劣る
- ベンダーロックイン懸念は (A) と同等で、差し替え可能設計（AuthAdapter）でカバー可能

## 決定

**(A) Firebase Auth を採用する。**

ただし、Firebase 固有処理は `FirebaseAuthAdapter`（`Auth::AuthAdapter` インターフェース実装）に閉じ込め、**別 IaaS へ差し替え可能な構造**を維持する。テストは同インターフェースを満たす `TestAdapter` で実 Firebase 不要に回す（DP-007 の差し替え可能設計の核）。

MFA は `admin_only`（管理者必須・一般オプトイン）を採用（DP-008）。実装は `firebase-auth-mfa` スキルが網羅（TOTP / SMS、enrollment / challenge / 管理者強制 / soft 失効）。

ローカル開発は **Firebase Auth Emulator + Docker** を既定とし、`firebase-auth-emulator` スキルが提供する compose / レシピで完結する（B-12）。`design.yaml.local_dev_stack=emulator_docker`。

## 帰結

### 正の帰結
- 3 方式（メール+PW / パスワードレス / OIDC）が SDK 標準でカバーされ、実装コストが低い
- Identity Platform へのアップグレードで MFA 要件（DP-008 = `admin_only`）が満たせる
- Auth Emulator + Docker でローカル / CI の E2E（`auth-e2e-verify`）が回せる
- `AuthAdapter` 抽象化で将来の IaaS 移行が現実的

### 負の帰結 / リスク
- Firebase / Identity Platform への依存（緩和: AuthAdapter で差し替え可能、本 ADR で明示）
- **TOTP MFA は Auth Emulator 非対応**（[firebase-tools #6224](https://github.com/firebase/firebase-tools/issues/6224)）。ローカルは SMS で代替、TOTP の E2E は staging / 実 Identity Platform（ADR にも本制約を明示、`auth-e2e-verify` の判断ポイントに記録）
- Identity Platform は GCP プロジェクトのアップグレードと課金設定が必要（運用負荷の上振れ）

## 関連スキル / 規約

- `firebase-auth-setup`（backend、JWT 検証 / Admin SDK 削除 / 公開鍵キャッシュ / 2 段階の失効）
- `firebase-auth-frontend`（client、AuthClient 契約 / セッション戦略 / page_access_control の A/B/C ガード）
- `firebase-auth-mfa`（横断、admin_only 実装 / TOTP・SMS / soft 失効）
- `firebase-auth-emulator`（ローカル E2E、docker-compose / 署名検証スキップ / Admin REST 切替）
- `tech-version-check`（実装着手前に Ruby / Rails / Firebase JS SDK 等の最新安定版を `delivery/version-matrix.md` に記録、B-11）
- `auth-e2e-verify`（実装後の DoD、representative_use_cases を Playwright で全件 PASS、B-15）
- 規約: CONV-14（SSoT / スキーマは xtone-shared-plugin）

## 履歴

| 日付 | 出来事 |
|---|---|
| 2026-05-27 | 本 ADR を起票し、accepted。B-14（sample-outputs 再生成）時に最新スキル群と整合させて記述 |
