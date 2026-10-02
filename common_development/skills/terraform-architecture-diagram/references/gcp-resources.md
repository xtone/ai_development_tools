# Google Cloud Terraform Resources to Draw.io Mapping

GCP Terraform リソースタイプから draw.io 表現への対応表。

## ファイルの役割

- **主用途**: `google_*` Terraform リソース → GCP サービス名 + 描画方針の lookup
- **アイコン描画**: **SVG 埋め込み形式が標準**（Draw.io Desktop 版で唯一表示可能）。Base64 データは [gcp-svg-icons.md](gcp-svg-icons.md) を参照
- **下部の `mxgraph.gcp2.*` マッピング表**: draw.io Web 版 (`app.diagrams.net`) 向けの fallback 参考情報。Desktop 版では描画されないため、Desktop で開く前提なら無視してよい

## 目次

1. [SVG 埋め込みスタイルの書き方](#svg-埋め込みスタイルの書き方)
2. [Compute（Web 版 fallback 参考）](#compute)
3. [Networking（Web 版 fallback 参考）](#networking)
4. [Storage（Web 版 fallback 参考）](#storage)
5. [Database（Web 版 fallback 参考）](#database)
6. [Messaging & Integration（Web 版 fallback 参考）](#messaging--integration)
7. [Security & IAM（Web 版 fallback 参考）](#security--iam)
8. [Monitoring & Logging（Web 版 fallback 参考）](#monitoring--logging)
9. [Analytics & BigQuery（Web 版 fallback 参考）](#analytics--bigquery)
10. [ML & AI（Web 版 fallback 参考）](#ml--ai)
11. [DevOps & CI/CD（Web 版 fallback 参考）](#devops--cicd)
12. [Groups (for containing resources)](#groups-for-containing-resources)

---

## SVG 埋め込みスタイルの書き方

GCP アイコンは以下のスタイル文字列パターンで埋め込む：

```
shape=image;aspect=fixed;imageAspect=0;image=data:image/svg+xml,<base64データ>;labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top
```

- **Base64 データの取得**: 各リソース対応の Base64 文字列は [gcp-svg-icons.md](gcp-svg-icons.md) を参照
- **推奨サイズ**: 48x48
- **ラベル**: アイコンの `value` は空にし、`text` セルとして下に配置（[drawio-xml-guide.md](drawio-xml-guide.md) のラベル配置パターン参照）

### ⚠️ 重要な落とし穴: `;base64,` を書かない

`image=data:image/svg+xml;base64,...` と書くと、`;base64,` 部分が drawio のスタイル区切り文字 `;` と衝突してスタイルが分断され、画像が描画されない。

**必ず `image=data:image/svg+xml,<base64データ>` と記述する**（`;base64` を省略。drawio は拡張仕様として base64 をそのまま解釈する）。

同じ落とし穴は AWS 側の 3rd Party SVG アイコン（GitHub 等）にも存在する。詳細は [aws-resources.md](aws-resources.md) の `## 3rd Party Services` 節を参照。

## Compute

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_compute_instance | mxgraph.gcp2.compute_engine | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.compute_engine; |
| google_compute_instance_group | mxgraph.gcp2.compute_engine | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.compute_engine; |
| google_compute_instance_template | mxgraph.gcp2.compute_engine | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.compute_engine; |
| google_cloudfunctions_function | mxgraph.gcp2.cloud_functions | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_functions; |
| google_cloudfunctions2_function | mxgraph.gcp2.cloud_functions | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_functions; |
| google_cloud_run_service | mxgraph.gcp2.cloud_run | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_run; |
| google_cloud_run_v2_service | mxgraph.gcp2.cloud_run | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_run; |
| google_container_cluster | mxgraph.gcp2.google_kubernetes_engine | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.google_kubernetes_engine; |
| google_container_node_pool | mxgraph.gcp2.google_kubernetes_engine | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.google_kubernetes_engine; |
| google_app_engine_application | mxgraph.gcp2.app_engine | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.app_engine; |
| google_compute_autoscaler | mxgraph.gcp2.compute_engine | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.compute_engine; |

## Networking

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_compute_network | mxgraph.gcp2.virtual_private_cloud | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.virtual_private_cloud; |
| google_compute_subnetwork | mxgraph.gcp2.virtual_private_cloud | fillColor=#E6F2FF;strokeColor=#4285F4;dashed=1;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1; |
| google_compute_firewall | mxgraph.gcp2.cloud_firewall_rules | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_firewall_rules; |
| google_compute_router | mxgraph.gcp2.cloud_router | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_router; |
| google_compute_router_nat | mxgraph.gcp2.cloud_nat | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_nat; |
| google_compute_global_address | mxgraph.gcp2.external_ip_addresses | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.external_ip_addresses; |
| google_compute_address | mxgraph.gcp2.external_ip_addresses | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.external_ip_addresses; |
| google_compute_forwarding_rule | mxgraph.gcp2.cloud_load_balancing | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_load_balancing; |
| google_compute_global_forwarding_rule | mxgraph.gcp2.cloud_load_balancing | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_load_balancing; |
| google_compute_target_http_proxy | mxgraph.gcp2.cloud_load_balancing | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_load_balancing; |
| google_compute_target_https_proxy | mxgraph.gcp2.cloud_load_balancing | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_load_balancing; |
| google_compute_url_map | mxgraph.gcp2.cloud_load_balancing | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_load_balancing; |
| google_compute_backend_service | mxgraph.gcp2.cloud_load_balancing | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_load_balancing; |
| google_compute_health_check | mxgraph.gcp2.cloud_load_balancing | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_load_balancing; |
| google_dns_managed_zone | mxgraph.gcp2.cloud_dns | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_dns; |
| google_dns_record_set | mxgraph.gcp2.cloud_dns | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_dns; |
| google_compute_vpn_gateway | mxgraph.gcp2.cloud_vpn | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_vpn; |
| google_compute_vpn_tunnel | mxgraph.gcp2.cloud_vpn | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_vpn; |
| google_compute_interconnect_attachment | mxgraph.gcp2.cloud_interconnect | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_interconnect; |
| google_service_networking_connection | mxgraph.gcp2.virtual_private_cloud | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.virtual_private_cloud; |
| google_compute_network_endpoint_group | mxgraph.gcp2.cloud_endpoints | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_endpoints; |
| google_api_gateway_api | mxgraph.gcp2.api_analytics | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.api_analytics; |
| google_apigee_organization | mxgraph.gcp2.apigee_api_platform | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.apigee_api_platform; |
| google_compute_ssl_certificate | mxgraph.gcp2.cloud_security_scanner | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_security_scanner; |

## Storage

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_storage_bucket | mxgraph.gcp2.cloud_storage | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_storage; |
| google_compute_disk | mxgraph.gcp2.persistent_disk | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.persistent_disk; |
| google_filestore_instance | mxgraph.gcp2.cloud_filestore | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_filestore; |

## Database

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_sql_database_instance | mxgraph.gcp2.cloud_sql | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_sql; |
| google_sql_database | mxgraph.gcp2.cloud_sql | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_sql; |
| google_spanner_instance | mxgraph.gcp2.cloud_spanner | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_spanner; |
| google_spanner_database | mxgraph.gcp2.cloud_spanner | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_spanner; |
| google_bigtable_instance | mxgraph.gcp2.cloud_bigtable | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_bigtable; |
| google_bigtable_table | mxgraph.gcp2.cloud_bigtable | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_bigtable; |
| google_firestore_database | mxgraph.gcp2.cloud_firestore | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_firestore; |
| google_redis_instance | mxgraph.gcp2.cloud_memorystore | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_memorystore; |
| google_memcache_instance | mxgraph.gcp2.cloud_memorystore | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_memorystore; |
| google_datastore_index | mxgraph.gcp2.cloud_datastore | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_datastore; |

## Messaging & Integration

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_pubsub_topic | mxgraph.gcp2.cloud_pubsub | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_pubsub; |
| google_pubsub_subscription | mxgraph.gcp2.cloud_pubsub | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_pubsub; |
| google_cloud_tasks_queue | mxgraph.gcp2.cloud_tasks | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_tasks; |
| google_cloud_scheduler_job | mxgraph.gcp2.cloud_scheduler | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_scheduler; |
| google_workflows_workflow | mxgraph.gcp2.cloud_endpoints | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_endpoints; |
| google_eventarc_trigger | mxgraph.gcp2.cloud_pubsub | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_pubsub; |

## Security & IAM

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_service_account | mxgraph.gcp2.cloud_iam | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_iam; |
| google_project_iam_member | mxgraph.gcp2.cloud_iam | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_iam; |
| google_project_iam_binding | mxgraph.gcp2.cloud_iam | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_iam; |
| google_kms_key_ring | mxgraph.gcp2.cloud_key_management_service | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_key_management_service; |
| google_kms_crypto_key | mxgraph.gcp2.cloud_key_management_service | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_key_management_service; |
| google_secret_manager_secret | mxgraph.gcp2.secret_manager | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.secret_manager; |
| google_compute_security_policy | mxgraph.gcp2.cloud_armor | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_armor; |
| google_iap_web_iam_member | mxgraph.gcp2.cloud_iam | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_iam; |
| google_identity_platform_config | mxgraph.gcp2.cloud_iam | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_iam; |

## Monitoring & Logging

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_logging_project_sink | mxgraph.gcp2.cloud_logging | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_logging; |
| google_monitoring_alert_policy | mxgraph.gcp2.cloud_monitoring | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_monitoring; |
| google_monitoring_notification_channel | mxgraph.gcp2.cloud_monitoring | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_monitoring; |
| google_monitoring_uptime_check_config | mxgraph.gcp2.cloud_monitoring | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_monitoring; |
| google_monitoring_dashboard | mxgraph.gcp2.cloud_monitoring | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_monitoring; |
| google_cloud_trace_config | mxgraph.gcp2.trace | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.trace; |

## Analytics & BigQuery

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_bigquery_dataset | mxgraph.gcp2.bigquery | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.bigquery; |
| google_bigquery_table | mxgraph.gcp2.bigquery | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.bigquery; |
| google_dataflow_job | mxgraph.gcp2.cloud_dataflow | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_dataflow; |
| google_dataproc_cluster | mxgraph.gcp2.cloud_dataproc | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_dataproc; |
| google_composer_environment | mxgraph.gcp2.cloud_composer | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_composer; |
| google_data_catalog_entry | mxgraph.gcp2.data_catalog | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.data_catalog; |
| google_looker_instance | mxgraph.gcp2.looker | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.looker; |

## ML & AI

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_vertex_ai_dataset | mxgraph.gcp2.ai_platform | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.ai_platform; |
| google_vertex_ai_endpoint | mxgraph.gcp2.ai_platform | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.ai_platform; |
| google_vertex_ai_featurestore | mxgraph.gcp2.ai_platform | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.ai_platform; |
| google_ml_engine_model | mxgraph.gcp2.ai_platform | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.ai_platform; |
| google_notebooks_instance | mxgraph.gcp2.ai_platform_notebooks | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.ai_platform_notebooks; |
| google_dialogflow_agent | mxgraph.gcp2.dialogflow | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.dialogflow; |

## DevOps & CI/CD

| Terraform Resource | Draw.io Shape | Style |
|-------------------|---------------|-------|
| google_cloudbuild_trigger | mxgraph.gcp2.cloud_build | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_build; |
| google_artifact_registry_repository | mxgraph.gcp2.artifact_registry | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.artifact_registry; |
| google_container_registry | mxgraph.gcp2.container_registry | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.container_registry; |
| google_sourcerepo_repository | mxgraph.gcp2.cloud_source_repositories | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_source_repositories; |
| google_clouddeploy_target | mxgraph.gcp2.cloud_build | outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.gcp2.cloud_build; |

## Groups (for containing resources)

| Type | Use For | Style |
|------|---------|-------|
| Google Cloud | Top-level container | fillColor=#F2F6FA;strokeColor=#4285F4;dashed=0;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1; |
| Project | Project boundary | fillColor=#E8F4E8;strokeColor=#34A853;dashed=0;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1; |
| Region | Regional boundary | fillColor=#E6F2FF;strokeColor=#4285F4;dashed=1;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1; |
| Zone | Zone boundary | fillColor=#FFF8E6;strokeColor=#FBBC04;dashed=1;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1; |
| VPC | VPC container | fillColor=#E6F2FF;strokeColor=#4285F4;dashed=0;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1; |
| Subnet | Subnet | fillColor=#E6E6FA;strokeColor=#5A5A9E;dashed=0;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1; |
