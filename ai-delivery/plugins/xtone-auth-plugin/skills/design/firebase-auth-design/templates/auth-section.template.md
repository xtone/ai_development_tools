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

## 責務仕分け（design.schema: responsibility_split / F-4）

requirements に並ぶ各機能を **backend / client / iaas / shared** に仕分ける。クライアント SDK や IaaS 側で完結する機能（パスワード変更・リセット・メール変更など）を明示し、バックエンド実装対象と取り違えないようにする。

owner は **単一の enum 値**（`backend` / `client` / `iaas` / `shared`）。複合的な場合は主担当を1つ選び、内訳は「補足」列に書く（design.schema.json の `responsibility_split[].owner` と一致させる）。

| 機能 | 担当（owner） | 補足 |
|---|---|---|
| サインイン（メール+パスワード / パスワードレス / OIDC） | client | クライアント SDK 主体（認証自体は IaaS=Firebase Auth が提供） |
| ID トークン検証 / JWT 認可 | backend | API ミドルウェア |
| セッション確立（アプリ側ユーザー作成） | backend | POST /auth/session |
| パスワード変更・リセット | iaas | Firebase が提供、クライアント SDK で完結（**バックエンド対象外**） |
| メールアドレス変更 | iaas | 同上 |
| 認証方式の追加（アカウント連携） | client | クライアント SDK 主体（**バックエンド対象外**） |
| 退会（IaaS ユーザー削除 ＋ アプリ側論理削除） | shared | Admin SDK（backend）＋ アプリ DB 論理削除 |
| MFA | shared | 設定は IaaS、フローは client（DP-008 の方針に従う） |

> owner の値: **backend**=サーバ実装 / **client**=アプリ・フロント SDK / **iaas**=Firebase 等が提供 / **shared**=両方。

## 未決（undecided）

- DP-XXX: <概要>（`docs/pending-decisions.md` に起票済み）
