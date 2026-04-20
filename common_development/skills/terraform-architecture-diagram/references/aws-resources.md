# AWS Terraform Resources to Draw.io Mapping

AWS Terraform リソースタイプから draw.io のスタイル文字列への対応表。

## 目次

1. [アイコンスタイルタイプ](#アイコンスタイルタイプ)
2. [Compute](#compute)
3. [Networking](#networking)
4. [Storage](#storage)
5. [Database](#database)
6. [Messaging & Integration](#messaging--integration)
7. [Security & IAM](#security--iam)
8. [Monitoring & Logging](#monitoring--logging)
9. [CI/CD](#cicd)
10. [3rd Party Services](#3rd-party-services)
11. [Other Services](#other-services)
12. [Analytics](#analytics)
13. [ML & AI](#ml--ai)
14. [User Traffic](#user-traffic)
15. [Groups (for containing resources)](#groups-for-containing-resources)

---

## アイコンスタイルタイプ

AWSアイコンには2種類のスタイルがある。サービスごとに正しいタイプを使い分けること。

- **タイプA (Direct Shape)**: `shape=mxgraph.aws4.{service}` + `strokeColor=none` — ネットワーク系インフラ
- **タイプB (resourceIcon)**: `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{service}` + `strokeColor=#ffffff` — マネージドサービス

## Compute

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_instance | ec2 | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2 |
| aws_lambda_function | lambda | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda |
| aws_ecs_service | fargate | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.fargate |
| aws_ecs_service (console) | fargate | B | #8B4513 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8B4513;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.fargate |
| aws_ecs_cluster | ecs | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs |
| aws_ecs_task_definition | fargate | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.fargate |
| aws_eks_cluster | eks | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks |
| aws_autoscaling_group | auto_scaling2 | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.auto_scaling2 |
| aws_batch_compute_environment | batch | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.batch |

## Networking

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_internet_gateway | internet_gateway | A | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=none;html=1;shape=mxgraph.aws4.internet_gateway |
| aws_nat_gateway | nat_gateway | A | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=none;html=1;shape=mxgraph.aws4.nat_gateway |
| aws_lb / aws_alb | application_load_balancer | A | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=none;html=1;shape=mxgraph.aws4.application_load_balancer |
| aws_elb | classic_load_balancer | A | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=none;html=1;shape=mxgraph.aws4.classic_load_balancer |
| aws_vpc_endpoint | endpoints | A | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=none;html=1;shape=mxgraph.aws4.endpoints |
| aws_cloudfront_distribution | cloudfront | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudfront |
| aws_route53_zone | route_53 | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.route_53 |
| aws_api_gateway_rest_api | api_gateway | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.api_gateway |
| aws_apigatewayv2_api | api_gateway | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.api_gateway |

## Storage

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_s3_bucket | s3 | B | #7AA116 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#7AA116;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.s3 |
| aws_ebs_volume | elastic_block_store | B | #7AA116 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#7AA116;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elastic_block_store |
| aws_efs_file_system | efs | B | #7AA116 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#7AA116;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.efs |
| aws_glacier_vault | glacier | B | #7AA116 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#7AA116;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.glacier |

## Database

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_db_instance | rds | B | #5A30B5 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#5A30B5;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.rds |
| aws_rds_cluster (Aurora) | aurora | B | gradient | sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.aurora |
| aws_dynamodb_table | dynamodb | B | #5A30B5 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#5A30B5;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.dynamodb |
| aws_elasticache_cluster | elasticache | B | #5A30B5 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#5A30B5;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elasticache |
| aws_elasticache_replication_group | elasticache | B | #5A30B5 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#5A30B5;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.elasticache |
| aws_redshift_cluster | redshift | B | #5A30B5 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#5A30B5;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.redshift |
| aws_docdb_cluster | documentdb_with_mongodb_compatibility | B | #5A30B5 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#5A30B5;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.documentdb_with_mongodb_compatibility |
| aws_neptune_cluster | neptune | B | #5A30B5 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#5A30B5;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.neptune |

### エッジラベル: Aurora / RDS レプリケーション

Aurora クラスタの Writer → Reader 間や RDS レプリカへのレプリケーション線のラベルは、Terraform の属性で判定する：

| Terraform 属性の状態 | ラベル |
|---------------------|-------|
| `replica_source_identifier` が設定されている（別リージョン/別アカウントのレプリカ） | `replica_master_user_secret` |
| `manage_master_user_password = true` のみで単一クラスタ内の Writer/Reader 構成 | `Aurora replication` |
| その他 | `replication` |

**重要**: `replica_master_user_secret` は Terraform の属性名でもあり、別リージョン/別アカウントレプリケーション時の IAM DB 認証用シークレット管理機能を指す。単一クラスタ内の Writer/Reader 構成のレプリケーション線にこのラベルを付けるのは誤り。

## Messaging & Integration

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_sqs_queue | sqs | B | #E7157B | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#E7157B;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sqs |
| aws_sns_topic | sns | B | #E7157B | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#E7157B;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sns |
| aws_kinesis_stream | kinesis | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.kinesis |
| aws_kinesis_firehose_delivery_stream | kinesis_data_firehose | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.kinesis_data_firehose |
| aws_mq_broker | mq | B | #E7157B | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#E7157B;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.mq |
| aws_cloudwatch_event_rule | eventbridge | B | #E7157B | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#E7157B;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eventbridge |
| aws_cloudwatch_event_target | (edgeのみ描画) | — | — | Rule/Schedulerからの接続先を表現するためのリソース。独立アイコンは作らず、`aws_cloudwatch_event_rule` または `aws_scheduler_schedule` から `arn` で指定されたターゲット（ECSタスク、SNSトピック等）へのエッジを生成する |
| aws_scheduler_schedule | eventbridge | B | #E7157B | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#E7157B;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eventbridge |
| aws_sfn_state_machine | step_functions | B | #E7157B | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#E7157B;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.step_functions |

### EventBridge Scheduler と Rule の区別

EventBridge には2系統のリソースがあり、**それぞれ別アイコン + 別ラベル**で描画する。どちらか片方だけを描画して両方を兼ねさせることはしない。

| Terraform リソース | 役割 | 推奨ラベル |
|-------------------|------|-----------|
| `aws_scheduler_schedule` | 定期実行（cron/rate 式で ECS RunTask 等をスケジュール） | `EventBridge Scheduler` |
| `aws_cloudwatch_event_rule` + `aws_cloudwatch_event_target` | イベントパターン検知（ECS state change, S3 event 等からSNS/Lambda等へ） | `EventBridge Rule` |

**判定条件**:
- `aws_scheduler_schedule` リソースがある → Scheduler アイコンを側方 (side) に配置
- `aws_cloudwatch_event_rule` + `aws_cloudwatch_event_target` がある → Rule アイコンを managed に配置
- 両方ある場合はそれぞれ別アイコンで描画（共通化しない）

**エッジの描画**:
- Scheduler: Scheduler → Target（ECS, Lambda 等、`aws_cloudwatch_event_target.arn` の示す先）
- Rule: Source（Event source）→ Rule → Target（SNS, Lambda 等）。`event_pattern` に含まれる source からエッジを引く（例: `ecs.amazonaws.com` なら ECS サービスから Rule へ）

## Security & IAM

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_waf_web_acl | waf | B | #DD344C | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#DD344C;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.waf |
| aws_acm_certificate | certificate_manager_3 | B | #DD344C | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#DD344C;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.certificate_manager_3 |
| aws_secretsmanager_secret | secrets_manager | B | #DD344C | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#DD344C;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.secrets_manager |
| aws_kms_key | kms | B | #DD344C | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#DD344C;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.kms |
| aws_cognito_user_pool | cognito | B | #DD344C | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#DD344C;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cognito |
| aws_iam_role | iam | B | #DD344C | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#DD344C;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.iam |
| aws_ssm_parameter | systems_manager | B | #DD344C | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#DD344C;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.systems_manager |

## Monitoring & Logging

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_cloudwatch_log_group | cloudwatch_2 | B | #759C3E | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#759C3E;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudwatch_2 |
| aws_cloudwatch_metric_alarm | cloudwatch_2 | B | #759C3E | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#759C3E;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudwatch_2 |
| aws_cloudtrail | cloudtrail | B | #759C3E | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#759C3E;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.cloudtrail |
| aws_xray_sampling_rule | xray | B | #759C3E | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#759C3E;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.xray |

## CI/CD

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_codepipeline | codepipeline | B | #C925D1 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#C925D1;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.codepipeline |
| aws_codebuild_project | codebuild | B | #C925D1 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#C925D1;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.codebuild |
| aws_codedeploy_app | codedeploy | B | #C925D1 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#C925D1;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.codedeploy |

## 3rd Party Services

CI/CDパイプラインのソースプロバイダ等、AWS外のサービスアイコン。

**重要**: `mxgraph.signs.tech.*` 等のシェイプはDraw.io Desktop版で標準有効化されていないライブラリに属するため、fallback描画で単色の四角形になる。GCPアイコンと同様にSVGデータURI埋め込み形式を使用する。

| Service | Style |
|---------|-------|
| GitHub | `shape=image;aspect=fixed;imageAspect=0;image=data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA5OCA5NiI+PHBhdGggZmlsbD0iIzI0MjkyRiIgZmlsbC1ydWxlPSJldmVub2RkIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik00OC44NTQgMEMyMS44MzkgMCAwIDIyIDAgNDkuMjE3YzAgMjEuNzU2IDEzLjk5MyA0MC4xNzIgMzMuNDA1IDQ2LjY5IDIuNDI3LjQ5IDMuMzE2LTEuMDU5IDMuMzE2LTIuMzYyIDAtMS4xNDEtLjA4LTUuMDUyLS4wOC05LjEyNy0xMy41OSAyLjkzNC0xNi40Mi01Ljg2Ny0xNi40Mi01Ljg2Ny0yLjE4NC01LjcwNC01LjQyLTcuMTctNS40Mi03LjE3LTQuNDQ4LTMuMDE1LjMyNC0zLjAxNS4zMjQtMy4wMTUgNC45MzQuMzI2IDcuNTIzIDUuMDUyIDcuNTIzIDUuMDUyIDQuMzY3IDcuNDk2IDExLjQwNCA1LjM3OCAxNC4yMzUgNC4wNzQuNDA0LTMuMTc4IDEuNjk5LTUuMzc4IDMuMDc0LTYuNi0xMC44MzktMS4xNDEtMjIuMjQzLTUuMzc4LTIyLjI0My0yNC4yODMgMC01LjM3OCAxLjk0LTkuNzc4IDUuMDE0LTEzLjItLjQ4NS0xLjIyMi0yLjE4NC02LjI3NS40ODYtMTMuMDM4IDAgMCA0LjEyNS0xLjMwNCAxMy40MjYgNS4wNTJhNDYuOTcgNDYuOTcgMCAwIDEgMTIuMjE0LTEuNjNjNC4xMjUgMCA4LjMzLjU3MSAxMi4yMTMgMS42MyA5LjMwMi02LjM1NiAxMy40MjctNS4wNTIgMTMuNDI3LTUuMDUyIDIuNjcgNi43NjMuOTcgMTEuODE2LjQ4NSAxMy4wMzggMy4xNTUgMy40MjIgNS4wMTUgNy44MjIgNS4wMTUgMTMuMiAwIDE4LjkwNS0xMS40MDQgMjMuMDYtMjIuMzI0IDI0LjI4MyAxLjc4IDEuNTQ4IDMuMzE2IDQuNDgxIDMuMzE2IDkuMTI2IDAgNi42LS4wOCAxMS44OTctLjA4IDEzLjUyNiAwIDEuMzA0Ljg5IDIuODUzIDMuMzE2IDIuMzY0IDE5LjQxMi02LjUyIDMzLjQwNS0yNC45MzUgMzMuNDA1LTQ2LjY5MUM5Ny43MDcgMjIgNzUuNzg4IDAgNDguODU0IDB6Ii8+PC9zdmc+;labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top` |

サイズ: 48x48 推奨。ラベルは [drawio-xml-guide.md](drawio-xml-guide.md#10-ラベル配置パターン) のとおり別の `text` セルで配置する。

**⚠️ 重要（drawioスタイル構文の落とし穴）**: `image=data:image/svg+xml;base64,...` と書くと、`;base64,` 部分が drawio のスタイル区切り文字 `;` と衝突してスタイルが分断され、画像が描画されない。必ず `image=data:image/svg+xml,<base64データ>` と記述する（`;base64` を省略。drawio は拡張仕様として base64 をそのまま解釈する）。

**配置ルール**: CodePipelineのソースが GitHub の場合、CI/CD コンテナ内の先頭（CodePipelineの上）に配置し、GitHub → CodePipeline のデプロイエッジ（赤）で接続する。

## Other Services

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_ses_domain_identity | simple_email_service | B | #DD344C | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#DD344C;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.simple_email_service |
| aws_ecr_repository | ecr | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecr |
| aws_amplify_app | amplify | B | #ED7100 | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.amplify |

## Analytics

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_athena_database | athena | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.athena |
| aws_glue_catalog_database | glue | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.glue |
| aws_glue_job | glue | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.glue |
| aws_emr_cluster | emr | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.emr |
| aws_quicksight_data_source | quicksight | B | #8C4FFF | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.quicksight |

## ML & AI

| Terraform Resource | Icon Name | Type | fillColor | Style |
|-------------------|-----------|------|-----------|-------|
| aws_sagemaker_notebook_instance | sagemaker | B | #01A88D | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#01A88D;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sagemaker |
| aws_sagemaker_model | sagemaker | B | #01A88D | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#01A88D;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sagemaker |
| aws_comprehend_document_classifier | comprehend | B | #01A88D | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#01A88D;strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.comprehend |

## User Traffic

| Icon | Type | Style |
|------|------|-------|
| internet | A | sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#232F3E;strokeColor=none;html=1;shape=mxgraph.aws4.internet |

## Groups (for containing resources)

コンテナスタイルは [drawio-xml-guide.md](drawio-xml-guide.md) セクション5を参照。
