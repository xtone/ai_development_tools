# 認証設計セクション（design ドキュメント雛形）

## 採用スタック（DP-007）

- **採用**: <例: Firebase Auth>（MVP 推奨）
- **比較した代替**: <例: Devise+OmniAuth>
- **差し替え可能設計**: AuthAdapter 越しに認証処理を呼ぶ。Firebase 固有処理は FirebaseAuthAdapter に閉じ込める。

## ログイン方式

- [ ] メール+パスワード
- [ ] パスワードレス（一時トークン）
- [ ] OIDC（Google / Apple）
- [ ] 認証方式の追加

## MFA 方針（DP-008）

- 方針: <全員必須 / 管理者のみ / オプトイン / 不要>
- 根拠: <セキュリティ要件・規制>

## dAccount / docomo 規約（DP-015）

- 適用: <該当 / 非該当（スコープ外）>
- 該当時の規約遵守チェックタイミング: <…>

## セッション設計

- IDトークン TTL / リフレッシュ方針 / 失効条件

## 未決（undecided）

- DP-XXX: <概要>（`docs/pending-decisions.md` に起票済み）
