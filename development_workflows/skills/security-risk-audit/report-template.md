# セキュリティリスク報告: {{service.name}}

- 対象リポジトリ: {{repository}}（コミット `{{commit}}`、ブランチ `{{branch}}`）
- 実施日: {{date}}
- 参照仕様: サービス特性セキュリティ監査仕様 v{{spec_version}}（スキル同梱の `classification.yaml`）
- 実施者: {{agent name / model}}
- 調査範囲: コードベース / IaC / CI 定義 / ドキュメント（稼働中クラウドの実設定は {{含む / 含まない}}）

## 1. サービス特性プロファイル

| 特性 | 宣言（service-profile.yaml） | 検出結果 | 根拠（パス） |
|---|---|---|---|
| PII | true | 一致 | `db/schema.rb:42` users.email, `app/models/user.rb` |
| PII_SENSITIVE | false | 一致 | カード情報は Stripe トークンのみ（`app/services/payment.rb`） |
| REVENUE | true | 一致 | `app/controllers/checkout_controller.rb`, `terraform/alb.tf` |
| TENANT | unknown | **該当の疑い** | `db/schema.rb` に organization_id あり。要確認 |
| LEDGER | false | 一致 | 残高・台帳テーブルなし |
| PUBLISH | false | 一致 | — |
| FOUNDATION | false | 一致 | — |
| SAFETY | false | 一致 | — |
| GAME | false | 一致 | — |

宣言と検出結果の差分: {{あれば列挙。なければ「なし」}}

## 2. 合成した優先順位

該当する特性の順位を軸ごとに重ね合わせ、最も小さい順位（最優先）を採用する。

| 軸 | 合成順位 | 由来 |
|---|---|---|
| 機密性 | 1 | PII |
| 完全性 | 2 | PII, REVENUE |
| 可用性 | 1 | REVENUE |
| 安全性 | — | 該当なし |

## 3. 指摘一覧（重大度順）

| ID | 重大度 | チェック | 軸 | 到達性 | 場所 | 内容 | 推奨対応 |
|---|---|---|---|---|---|---|---|
| F-01 | Critical | X-01 | 機密性 | 外部 | `config/database.yml`（git 履歴 `a1b2c3d`） | 本番 DB パスワードがコミット履歴に残存（値は出力しない） | 認証情報のローテーション、履歴の除去、Secret Manager へ移行 |
| F-02 | High | REV-01 | 可用性 | 潜在 | `terraform/rds.tf:12` | RDS が単一 AZ 構成 | multi_az = true とフェイルオーバー試験 |
| F-03 | Medium | PII-07 | 機密性 | 内部 | `app/controllers/users_controller.rb:88` | ログに email と住所を出力 | 出力前にマスキング、ログのフィルタ設定 |

指摘ごとに、根拠（確認したファイルと内容）を 1〜3 行で添える。推定を含む場合は「推定」と明記する。

## 4. チェック結果の一覧

横断チェック（X-*）と、該当する特性のチェックを全件列挙する。省略しない。

| チェック | 結果 | 根拠・備考 |
|---|---|---|
| X-01 認証情報・シークレット | 要対応 | F-01 |
| X-02 管理者権限 | 確認不能 | IAM 設定はリポジトリ外。人間へ質問 Q-01 |
| X-03 バックアップ | OK | `terraform/rds.tf` backup_retention_period = 14、別アカウント保管は未確認 |
| … | … | … |
| PII-01 保存時の暗号化 | OK | `terraform/rds.tf` storage_encrypted = true |
| … | … | … |

結果の値: OK / 要対応 / 確認不能 / 対象外

## 5. 侵害時の方針

- service-profile.yaml の incident_policy: {{あり / なし}}
- 手順書・連絡先の所在: {{パス / なし}}
- 方針とコードの整合（例: 読み取り専用モードが実装されているか）: {{所見}}

## 6. 確認できなかった事項（人間への質問）

| ID | 質問 | 関連チェック |
|---|---|---|
| Q-01 | 本番 AWS アカウントの IAM で MFA は全ユーザー必須か | X-02 |
| Q-02 | バックアップは別アカウントまたは Object Lock で保護されているか | X-03, REV-04 |

## 7. 調査範囲と制約

- 調査したもの: {{ディレクトリ・ファイル種別}}
- 調査できなかったもの: {{稼働中の設定、外部 SaaS の設定 など}}
- この報告はコードと設定の静的な調査に基づく。ペネトレーションテストや運用実態の確認を代替しない。
