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
| F-02 | Critical | X-06 | 機密性 | 外部 | `api/Dockerfile:1`, `terraform/ec2_api.tf:20` | 画像変換ライブラリの RCE（CVE-YYYY-NNNNN）。公開 EC2 上で root 実行、全シークレットを読めるインスタンスロール（詳細は 3.1） | ライブラリの更新。ロールを必要なシークレットに絞り、IMDSv2 を必須にする |
| F-03 | High | REV-01 | 可用性 | 潜在 | `terraform/rds.tf:12` | RDS が単一 AZ 構成 | multi_az = true とフェイルオーバー試験 |
| F-04 | Medium | X-06 | 完全性 | 内部 | `worker/Dockerfile:1`, `terraform/ecs_worker.tf:8` | F-02 と同じ CVE。private サブネットの Fargate タスクで、入力は社内 CMS の画像のみ（詳細は 3.1） | ライブラリの更新（F-02 と同時に実施） |
| F-05 | Medium | PII-07 | 機密性 | 内部 | `app/controllers/users_controller.rb:88` | ログに email と住所を出力 | 出力前にマスキング、ログのフィルタ設定 |

指摘ごとに、根拠（確認したファイルと内容）を 1〜3 行で添える。推定を含む場合は「推定」と明記する。

### 3.1 ミドルウェア・ライブラリの脆弱性の詳細

X-06・PUB-06 の指摘ごとに、`classification.yaml` の `component_vulnerability` の因子と、想定される被害を書く。CVE 番号と CVSS の値だけで済ませない。読み取れない因子は「確認不能（Q-xx）」と書き、推定で埋めない。

**F-02 画像変換ライブラリの RCE（api）**

| 因子 | 内容 | 根拠 |
|---|---|---|
| 種類と前提（V-KIND） | RCE。細工した画像を処理させるだけで成立し、認証は不要。アップロード画像のサムネイル生成で該当機能を使用 | `api/app/services/thumbnail.rb:14` |
| 実行基盤（V-RUNTIME） | EC2（Auto Scaling グループ、AMI に直接インストール） | `terraform/ec2_api.tf:20`, `ansible/roles/api/tasks/main.yml:31` |
| ネットワーク（V-NETWORK） | public サブネット、パブリック IP あり、443 を 0.0.0.0/0 に許可。インターネットゲートウェイ経由で外向き通信も可能 | `terraform/ec2_api.tf:35`, `terraform/sg.tf:12` |
| 実行権限（V-PRIVILEGE） | プロセスは root。インスタンスロールに `secretsmanager:GetSecretValue`（Resource `*`）と、会員アップロード用バケットへの `s3:*`。IMDSv1 が有効 | `terraform/iam_api.tf:8`, `terraform/ec2_api.tf:41` |
| 届く資産（V-ASSETS） | 全シークレット（本番 DB の接続情報を含む）、会員のアップロードファイル、同じセキュリティグループから届く本番 DB | `terraform/iam_api.tf:8`, `terraform/sg.tf:30` |

- 想定される被害: 未認証の利用者が細工した画像をアップロードすると、API サーバー上で root として任意のコードが動く。インスタンスロールで全シークレットを取得でき、本番 DB の個人情報をまるごと持ち出せる。ホストに永続化されると、パッチ適用後も侵害が続く。
- 重大度の導出: 到達性は外部、軸は届く資産のうち合成順位が最も小さい機密性（順位 1）で、matrix の結果は Critical。全シークレットを読めるため、escalation でも Critical。

**F-04 同じライブラリの RCE（worker）**

| 因子 | 内容 | 根拠 |
|---|---|---|
| 種類と前提（V-KIND） | F-02 と同じ。ただし処理するのは社内 CMS で編集者が登録した画像のみ | `worker/app/jobs/resize_job.rb:9`, `cms/app/controllers/banners_controller.rb:22` |
| 実行基盤（V-RUNTIME） | ECS Fargate | `terraform/ecs_worker.tf:8`（requires_compatibilities = ["FARGATE"]） |
| ネットワーク（V-NETWORK） | private サブネット、パブリック IP なし、ingress なし。SQS からジョブを受け取る | `terraform/ecs_worker.tf:30` |
| 実行権限（V-PRIVILEGE） | 非 root ユーザー。タスクロールはバナー画像用バケットへの読み書きのみ | `worker/Dockerfile:18`, `terraform/iam_worker.tf:5` |
| 届く資産（V-ASSETS） | 公開サイトのバナー画像。個人情報 DB・シークレットには届かない | `terraform/iam_worker.tf:5`, `terraform/sg.tf:48` |

- 想定される被害: CMS の編集者アカウントが乗っ取られた場合、細工した画像でワーカー上のコードを実行され、公開バナー画像を差し替えられる。影響はタスクロールの権限内に閉じ、個人情報やシークレットには届かない。
- 重大度の導出: 到達性は内部（編集者のみが入力できる）、軸は完全性（順位 2）で Medium。バナー画像が消えてもサービスの稼働は止まらないため、可用性は対象にしない。プロセスの外へ広がる経路（特権・ホスト脱出・広い権限）は確認できず、escalation は適用しない。

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
| Q-03 | `batch` サービスはどこで動いているか（EC2 / Fargate など）と、付与している IAM ロール。IaC が見つからない。回答次第で F-0x の重大度が上がる | X-06 |

## 7. 調査範囲と制約

- 調査したもの: {{ディレクトリ・ファイル種別}}
- 調査できなかったもの: {{稼働中の設定、外部 SaaS の設定 など}}
- この報告はコードと設定の静的な調査に基づく。ペネトレーションテストや運用実態の確認を代替しない。
