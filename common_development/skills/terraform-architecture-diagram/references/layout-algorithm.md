# 決定論的レイアウトアルゴリズム仕様

同一のTerraformコードからは常に同一のレイアウトを生成するための仕様。
座標計算はすべてルールベースで行い、LLMの裁量による配置を排除する。

## 目次

1. [Tier階層定義](#1-tier階層定義)
2. [スペーシング定数](#2-スペーシング定数)
3. [コンテナサイズの動的計算](#3-コンテナサイズの動的計算)
4. [座標計算アルゴリズム](#4-座標計算アルゴリズム)
5. [GCP用レイアウト](#5-gcp用レイアウト)
6. [接続線ルーティング](#6-接続線ルーティング)
7. [座標参照テーブル](#7-座標参照テーブル)
8. [カスタマイズルール](#8-カスタマイズルール)
9. [サービスグルーピング](#9-サービスグルーピング)
10. [色分けルール](#10-色分けルール)
11. [注釈・補足テキスト・凡例](#11-注釈補足テキスト)

---

## 1. Tier階層定義

### AWS

| Tier | Y座標起点 | リソースタイプ | 説明 |
|------|----------|--------------|------|
| 0 | 10 | タイトル | ダイアグラムタイトル |
| 1 | 60 | エッジサービス | Route53, CloudFront, WAF, ACM, API Gateway |
| 2 | 320 | VPCコンテナ | VPC全体を囲むコンテナ |
| 3 | VPC相対: 40 | AZコンテナ | Availability Zone |
| 4 | AZ相対: 40 | パブリックサブネット | NAT Gateway, Bastion Host, IGW |
| 5 | AZ相対: 160 | プライベートサブネット | ALB, ECS, RDS, Aurora, Lambda |
| 6 | VPC下部+40 | マネージドサービス | ECR, Secrets Manager, CloudWatch, S3, KMS |
| Side | x = VPC右端+100 | サイドサービス | CI/CD, 外部連携 |

### GCP

| Tier | Y座標起点 | リソースタイプ | 説明 |
|------|----------|--------------|------|
| 0 | 10 | タイトル | ダイアグラムタイトル |
| 1 | 60 | エッジサービス | Cloud DNS, Cloud CDN, Cloud Armor, Cloud Load Balancing |
| 2 | 320 | VPCコンテナ | VPC Network |
| 3 | VPC相対: 40 | リージョン/ゾーンコンテナ | Region / Zone |
| 4 | Zone相対: 40 | パブリックサブネット | Cloud NAT, Cloud Router |
| 5 | Zone相対: 160 | プライベートサブネット | Cloud Run, GKE, Cloud SQL |
| 6 | VPC下部+40 | マネージドサービス | Cloud Storage, Artifact Registry, Secret Manager |
| Side | x = VPC右端+100 | サイドサービス | Cloud Build, Cloud Source Repositories |

---

## 2. スペーシング定数

```
SPACING = {
    MARGIN_X: 20,              # コンテナ内水平マージン
    MARGIN_Y: 40,              # コンテナ内垂直マージン

    AZ_GAP_2AZ: 460,           # 2-AZ構成時のAZ間水平間隔
    AZ_GAP_3AZ: 310,           # 3-AZ構成時のAZ間水平間隔
    SUBNET_GAP: 20,            # サブネット間の垂直ギャップ

    RESOURCE_GAP_X: 80,        # リソース間の水平間隔
    RESOURCE_GAP_Y: 80,        # リソース間の垂直間隔（アイコン48px + ラベル余白含む）

    TIER_GAP: 40,              # Tier間の垂直ギャップ
    EDGE_SERVICE_GAP: 150,     # エッジサービス間の水平間隔

    GRID_UNIT: 10,             # グリッド単位（全座標はこの倍数に丸める）
}
```

---

## 3. コンテナサイズの動的計算

### 基本サイズ定数

```
BASE_SIZE = {
    ICON: 60,              # 主要アイコン（エッジサービス等）
    ICON_SMALL: 50,        # サブネット内リソース
    LABEL_HEIGHT: 20,      # ラベルは別テキストセルとして配置
    TITLE_HEIGHT: 40,
}
```

### 動的計算ルール

同一Terraformからの再現性を保証するため、サイズはリソース数から決定論的に計算する。

#### パブリックサブネット

```pseudocode
function calcPublicSubnetSize(resourceCount):
    cols = max(1, min(resourceCount, 3))
    rows = ceil(resourceCount / cols)

    width = MARGIN_X * 2 + cols * ICON + (cols - 1) * RESOURCE_GAP_X
    width = max(width, 180)  # 最小幅
    width = roundToGrid(width)

    height = MARGIN_Y + rows * (ICON + RESOURCE_GAP_Y)
    height = max(height, 100)  # 最小高さ
    height = roundToGrid(height)

    return (width, height)
```

#### プライベートサブネット

```pseudocode
function calcPrivateSubnetSize(resourceCount):
    cols = max(1, min(resourceCount, 3))
    rows = ceil(resourceCount / cols)

    width = MARGIN_X * 2 + cols * ICON + (cols - 1) * RESOURCE_GAP_X
    width = max(width, 360)  # 最小幅
    width = roundToGrid(width)

    height = MARGIN_Y + rows * (ICON + RESOURCE_GAP_Y)
    height = max(height, 200)  # 最小高さ
    height = roundToGrid(height)

    return (width, height)
```

#### AZコンテナ

```pseudocode
function calcAZSize(publicSubnet, privateSubnet):
    width = max(publicSubnet.width, privateSubnet.width) + MARGIN_X * 2
    width = max(width, 400)
    width = roundToGrid(width)

    height = MARGIN_Y + publicSubnet.height + SUBNET_GAP + privateSubnet.height + MARGIN_X
    height = max(height, 400)
    height = roundToGrid(height)

    return (width, height)
```

#### VPCコンテナ

```pseudocode
function calcVPCSize(azCount, azSize):
    if azCount == 1:
        width = azSize.width + MARGIN_X * 2
    elif azCount == 2:
        width = azSize.width * 2 + MARGIN_X * 3
    elif azCount == 3:
        width = azSize.width * 3 + MARGIN_X * 4

    width = max(width, 500)
    width = roundToGrid(width)

    height = azSize.height + MARGIN_Y * 2
    height = max(height, 400)
    height = roundToGrid(height)

    return (width, height)
```

#### roundToGrid 関数

```pseudocode
function roundToGrid(value):
    return ceil(value / GRID_UNIT) * GRID_UNIT
```

---

## 4. 座標計算アルゴリズム

### 4.1 リソース分類

Terraformリソースを以下のカテゴリに分類する。分類はリソースタイプ名から機械的に判定する。

```pseudocode
RESOURCE_CLASSIFICATION = {
    # Tier 0.5: User Traffic（エントリーポイント）
    "user_traffic": [
        # shape=mxgraph.aws4.internet でユーザーアクセスの起点を明示
        # VPC上部中央に配置（エッジサービスの上、上→下フローの起点）
    ],

    # Tier 1: エッジサービス（VPC上部中央寄せ）
    "edge": [
        "aws_route53_*", "aws_cloudfront_*", "aws_waf_*", "aws_acm_*",
        "aws_api_gateway_*", "aws_apigatewayv2_*",
        "google_dns_*", "google_compute_ssl_*", "google_compute_security_policy",
        "google_compute_global_forwarding_rule", "google_compute_target_*_proxy",
        "google_compute_url_map"
    ],

    # Tier 4: パブリックサブネットリソース
    "public": [
        "aws_nat_gateway", "aws_internet_gateway",
        "google_compute_router", "google_compute_router_nat"
    ],

    # Tier 4.5: ALB（AZ横断・VPC直下配置）
    # ALBはPublic/Private境界に配置し、いずれのサブネットにも属さない
    # VPC直下（parent=vpc）で、AZ間の中央に水平配置する
    "alb": [
        "aws_lb", "aws_alb"
    ],

    # Tier 5: プライベートサブネットリソース
    "private": [
        "aws_instance", "aws_ecs_*", "aws_eks_*", "aws_lambda_*",
        "aws_db_*", "aws_rds_*",
        "aws_elasticache_*", "aws_dynamodb_*",
        "google_compute_instance*", "google_cloud_run_*",
        "google_container_*", "google_sql_*", "google_redis_*",
        "google_compute_forwarding_rule", "google_compute_backend_service"
    ],

    # VPC Endpoints（AZ間に集約配置）
    # 複数のVPC Endpointは1アイコンに集約し、テキストラベルで内訳を表示
    # 例: 1アイコン + テキスト「(ECR, Secrets, Logs)」
    # VPC直下、AZ群の下部に配置
    "vpc_endpoint": [
        "aws_vpc_endpoint"
    ],

    # Amplify（独立コンテナとして配置）
    # VPC外・左上に独立コンテナとして配置（エッジサービスやVPCの左側）
    # 内部にCloudFront CDN + Lambda SSR + S3 Static Contentを含む
    "amplify": [
        "aws_amplify_*"
    ],

    # Tier 6: マネージドサービス（VPC外下部）
    "managed": [
        "aws_s3_*", "aws_ecr_*", "aws_secretsmanager_*", "aws_ssm_*",
        "aws_cloudwatch_*", "aws_kms_*", "aws_sns_*", "aws_sqs_*",
        "aws_kinesis_*", "aws_cognito_*",
        "google_storage_*", "google_artifact_registry_*", "google_secret_manager_*",
        "google_pubsub_*", "google_kms_*", "google_monitoring_*", "google_logging_*"
    ],

    # Side: サイドサービス（右側）
    "side": [
        "aws_codepipeline", "aws_codebuild_*", "aws_codecommit_*",
        "aws_sfn_*", "aws_eventbridge_*",
        "google_cloudbuild_*", "google_sourcerepo_*", "google_clouddeploy_*"
    ],

    # 図示省略（デフォルト）
    "skip": [
        "aws_iam_*", "aws_iam_role_policy_attachment",
        "aws_security_group", "aws_security_group_rule",
        "aws_route_table*", "aws_route",
        "aws_lb_listener*", "aws_lb_target_group*",
        "google_project_iam_*", "google_service_account",
        "google_compute_firewall"
    ]
}
```

分類に該当しないリソースは `managed`（VPC外下部）にフォールバックする。

### 4.2 プライベートサブネット内の配置優先順位

同一サブネット内のリソースはこの順序で上から配置する：

```
PRIORITY_ORDER = {
    "loadbalancer": 1,   # NLB, Cloud Load Balancing（ALBはVPC直下に独立配置）
    "compute": 2,        # EC2, ECS, EKS, Lambda, Cloud Run, GKE
    "database": 3,       # RDS, Aurora, DynamoDB, Cloud SQL, Spanner
    "cache": 4,          # ElastiCache, Memorystore
    "storage": 5,        # EFS, Filestore
    "other": 6
}
```

### 4.3 全体座標計算フロー

```pseudocode
function calculateLayout(resources):
    # 1. リソースを分類
    classified = classifyResources(resources)

    # 2. AZ数を判定（サブネットリソースから推定）
    azCount = detectAZCount(resources)

    # 3. コンテナサイズを動的計算
    pubSubnetSize = calcPublicSubnetSize(len(classified.public) / azCount)
    privSubnetSize = calcPrivateSubnetSize(len(classified.private) / azCount)
    azSize = calcAZSize(pubSubnetSize, privSubnetSize)
    vpcSize = calcVPCSize(azCount, azSize)

    # 4. 各Tierの座標を計算
    layout = {}

    # Amplifyがある場合、左上に配置（VPCの左側）
    amplifyWidth = 300 if hasAmplify else 0
    amplifyOffset = amplifyWidth + 50 if hasAmplify else 0

    # Tier 0: タイトル（VPC上部中央に配置）
    layout.title = {x: amplifyOffset + vpcSize.width / 2 - 200, y: 20, w: 400, h: 40}

    # Tier 0.5: User Traffic（VPC上部中央、エッジサービスの上）
    layout.user_traffic = {
        x: amplifyOffset + vpcSize.width / 2 - 30,  # VPC中央に配置
        y: 60
    }

    # Tier 1: エッジサービス（VPC上部に中央寄せ配置）
    edgeCount = len(classified.edge)
    edgeTotalWidth = edgeCount * ICON + (edgeCount - 1) * EDGE_SERVICE_GAP
    edgeStartX = amplifyOffset + (vpcSize.width - edgeTotalWidth) / 2
    for i, svc in enumerate(sorted(classified.edge)):
        layout[svc] = {
            x: edgeStartX + i * (ICON + EDGE_SERVICE_GAP),
            y: 200
        }

    # Amplify: 左上に独立コンテナとして配置
    if hasAmplify:
        layout.amplify = {x: 50, y: 50, w: 300, h: 280}

    # Tier 2: VPC（エッジサービスの下）
    layout.vpc = {x: amplifyOffset + 50, y: 340, w: vpcSize.width, h: vpcSize.height}

    # Tier 3: AZ（VPC相対座標）
    for i in range(azCount):
        azGap = AZ_GAP_2AZ if azCount == 2 else AZ_GAP_3AZ
        layout[f"az_{i}"] = {
            x: MARGIN_X + i * azGap,   # VPC相対
            y: MARGIN_Y                  # VPC相対
        }

    # Tier 4-5: サブネット（AZ相対座標）
    # ... サブネット内リソースはグリッド配置（4.4参照）

    # Tier 6: マネージドサービス
    managedY = layout.vpc.y + layout.vpc.h + TIER_GAP
    for i, svc in enumerate(sorted(classified.managed)):
        layout[svc] = {
            x: 100 + i * EDGE_SERVICE_GAP,
            y: managedY
        }

    # Side: サイドサービス
    sideX = layout.vpc.x + layout.vpc.w + 100
    for i, svc in enumerate(sorted(classified.side)):
        layout[svc] = {
            x: sideX,
            y: 400 + i * 100
        }

    return layout
```

### 4.4 サブネット内リソースのグリッド配置

```pseudocode
function placeResourcesInSubnet(subnet, resources):
    # リソースを優先順位でソート
    sorted_resources = sortByPriority(resources)

    # グリッド計算
    cols = calcColumns(subnet.width)  # 通常2-3列

    for i, resource in enumerate(sorted_resources):
        col = i % cols
        row = i // cols

        # サブネット相対座標
        resource.x = MARGIN_X + col * (ICON + RESOURCE_GAP_X)
        resource.y = MARGIN_Y + row * (ICON + RESOURCE_GAP_Y)

        # 1列の場合は中央配置
        if cols == 1:
            resource.x = (subnet.width - ICON) / 2

        # グリッドに丸める
        resource.x = roundToGrid(resource.x)
        resource.y = roundToGrid(resource.y)

function calcColumns(subnetWidth):
    available = subnetWidth - MARGIN_X * 2
    cols = floor(available / (ICON + RESOURCE_GAP_X))
    return max(1, min(cols, 3))  # 1-3列
```

### 4.5 リソースのソートキー

決定論性を保証するため、同一カテゴリ・同一優先順位内のリソースはTerraformリソースタイプ名 → リソース名のアルファベット順でソートする。

```pseudocode
function sortKey(resource):
    return (PRIORITY_ORDER[resource.category], resource.type, resource.name)
```

---

## 5. GCP用レイアウト

GCPの場合、コンテナ階層が異なる：

```
AWS:  Cloud > Region > VPC > AZ > Subnet > Resource
GCP:  Cloud > Project > VPC Network > Region/Zone > Subnet > Resource
```

### GCPコンテナ階層の座標計算

基本的にAWSと同じアルゴリズムを使用するが、以下を置換：
- AZ → Zone（または Region）
- Public Subnet → パブリックサブネット相当（Cloud NAT, Cloud Router）
- Private Subnet → プライベートサブネット相当（Cloud Run, GKE, Cloud SQL）

GCPではAZの概念がZoneに対応し、複数Zoneが存在する場合はAWSの複数AZ構成と同じレイアウトルールを適用する。

---

## 6. 接続線ルーティング

### 6.1 基本ルール

- 全エッジに `edgeStyle=orthogonalEdgeStyle` を使用（直角コネクタ）
- ノード間隔は最低60px、推奨200px水平 / 120px垂直
- アローヘッドの最終直線セグメントは最低20px確保
- エッジに `rounded=1` を付与して見やすいベンドに
- `jettySize=auto` でポート間隔を自動調整

### 6.2 接続線の種類

| 接続タイプ | スタイル | 色 | strokeWidth | 用途 |
|-----------|--------|-----|------------|------|
| データフロー | 実線 + 矢印 | #0066CC (青) | 2 | リクエスト/レスポンス、データの流れ |
| 依存関係 | 破線 + 矢印 | #666666 (灰) | 1 | リソース間の依存関係 |
| デプロイ | 実線 + 矢印 | #e74c3c (赤) | 2 | CI/CDパイプライン、デプロイフロー |
| コンソール/管理 | 実線 + 矢印 | #8B4513 (茶) | 1 | 管理者アクセス、運用操作 |
| レプリケーション | 破線 + 矢印 + ラベル | #666666 (灰) | 1 | DB/ストレージのレプリケーション |

エッジにはポート番号をラベルとして付与する（例: 「Port 3000」「Port 5432」）。

### 6.3 接続点（アンカー）の決定

```pseudocode
function selectAnchor(source, target):
    dx = target.centerX - source.centerX
    dy = target.centerY - source.centerY

    if abs(dy) > abs(dx):
        if dy > 0: return (exitY=1, entryY=0)   # 下→上
        else:      return (exitY=0, entryY=1)     # 上→下
    else:
        if dx > 0: return (exitX=1, entryX=0)     # 右→左
        else:      return (exitX=0, entryX=1)      # 左→右
```

### 6.4 コンテナ跨ぎの接続

異なるコンテナ（例: VPC外→VPC内）を跨ぐエッジは `parent="1"`（ルート）に配置する。
同一コンテナ内のエッジはそのコンテナの `parent` に配置する。

### 6.5 waypoints の使用

エッジが重なる場合は明示的にwaypointsを追加：

```xml
<mxCell id="edge1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;" edge="1" parent="1" source="a" target="b">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="300" y="150"/>
      <mxPoint x="300" y="250"/>
    </Array>
  </mxGeometry>
</mxCell>
```

---

## 7. 座標参照テーブル

### 7.1 2-AZ構成（デフォルト）

#### 全体レイアウトフロー

```
上→下の中央軸フロー:
  [Amplify: 左上]    [Title: 中央上]
                     [User Traffic: 中央]
           [Edge Services: 中央寄せ横並び]
                     [VPC: 中央]
            [Managed Services: 中央寄せ]
                              [CI/CD: 右側]
```

#### 絶対座標（parent: root）

Amplifyがある場合、VPC以降の要素はAmplifyコンテナ幅分（約350px）右にオフセットする。

| 要素 | X | Y | Width | Height |
|-----|---|---|-------|--------|
| Amplify（ある場合） | 50 | 50 | 300 | 280 |
| タイトル | VPC中央-200 | 20 | 400 | 40 |
| User Traffic | VPC中央-30 | 60 | 60 | 60 |
| エッジサービス群 | VPC中央寄せ | 200 | 60 | 60 |
| VPC | offset+50 | 340 | 動的 | 動的 |
| マネージドサービス群 | VPC中央寄せ | VPC.y+VPC.h+40 | 60 | 60 |
| サイドサービス群 | VPC.x+VPC.w+100 | 400+i*100 | 60 | 60 |

#### VPC相対座標

| 要素 | X | Y | Width | Height |
|-----|---|---|-------|--------|
| AZ-1 | 20 | 40 | 400 | 580 |
| AZ-2 | 480 | 40 | 400 | 580 |

#### AZ相対座標

| 要素 | X | Y | Width | Height |
|-----|---|---|-------|--------|
| Public Subnet | 20 | 40 | 360 | 100 |
| Private Subnet | 20 | 160 | 360 | 400 |

#### Public Subnet相対座標

| 要素 | X | Y |
|-----|---|---|
| リソース（中央配置） | (subnet.w - 48) / 2 | 26 |

#### Private Subnet相対座標

| 優先順位 | 要素 | X（2列時） | Y |
|---------|-----|-----------|---|
| 1 | LB | 156 (中央) | 20 |
| 2 | Compute左 | 80 | 100 |
| 2 | Compute右 | 232 | 100 |
| 3 | DB | 156 (中央) | 200 |
| 4 | Cache | 156 (中央) | 300 |

### 7.2 3-AZ構成

VPC幅とAZ間隔を調整：

```
AZ_WIDTH = 280
AZ_GAP = 310
VPC_WIDTH = 3 * 280 + 4 * 20 = 920
```

### 7.3 単一AZ/Zone構成

```
AZ_WIDTH = 400
VPC_WIDTH = 400 + 2 * 20 = 440
```

---

## 8. カスタマイズルール

### 8.1 リソース数増加時の対応

リソース数が多い場合はコンテナサイズを動的に拡張する。ただし以下の制約を守る：

- Private Subnet の最大列数: 3
- Private Subnet の最大行数: 制限なし（高さを拡張）
- AZ/VPC のサイズはサブネットサイズから自動計算

### 8.2 マルチクラウド構成

AWSとGCPの両方を含む場合：

```
AWS Cloud コンテナ（左側）
  └── VPC → AZ → Subnet → Resources

GCP Cloud コンテナ（右側）
  └── VPC Network → Zone → Subnet → Resources

クラウド間接続線（AWS ↔ GCP）はルートレベルに配置
```

水平配置で、AWSコンテナの右端 + 100px にGCPコンテナを配置する。

---

## 9. サービスグルーピング

関連するリソースを破線コンテナで囲み、論理的なグループを視覚化する。

### 9.1 グルーピング判定ルール

| グループ種別 | 判定条件 | コンテナスタイル |
|-------------|---------|---------------|
| Multi-AZサービス | 同一リソースタイプが複数AZに存在 | `rounded=1;strokeColor=#ED7100;dashed=1;fillColor=none;` |
| Single AZサービス | 同一AZ内で密接に関連するリソース群 | `rounded=1;strokeColor=#147EBA;dashed=1;fillColor=none;` |
| DBクラスタ | Aurora Cluster、RDS Multi-AZ | `rounded=1;strokeColor=#5A30B5;dashed=1;fillColor=none;` |
| ECSクラスタ | ECS Service + Task Definition | `rounded=1;strokeColor=#ED7100;dashed=1;fillColor=none;` |

### 9.2 グルーピングの配置ルール

- グループコンテナは `container=1;collapsible=0;` を付与
- グループ内のリソースは通常のグリッド配置ルールに従う
- グループラベルはコンテナの上部に配置（例: 「Aurora Cluster」「ECS Multi-AZ」）
- グループコンテナのパディング: 上20px、左右下10px

### 9.3 ALBのAZ横断配置

ALB（Application Load Balancer）はVPC直下（`parent=vpc`）に配置する。いずれのAZにもサブネットにも属さない。

```
配置位置:
  x = VPC内の水平中央
  y = パブリックサブネットとプライベートサブネットの境界
      （AZコンテナの上端 + パブリックサブネットの高さ付近）
```

### 9.4 VPC Endpointsの集約配置

複数のVPC Endpoint（ECR, Secrets Manager, CloudWatch Logs等）は1つのアイコンに集約する。

```
配置:
  - 1つのVPC Endpointアイコン（parent=vpc）
  - テキストラベル「(ECR, Secrets, Logs)」をアイコン下部に配置
  - 位置: AZ群の下部、VPCコンテナ下端付近
```

### 9.5 Amplifyの独立コンテナ

AWS Amplifyは独立したコンテナとして左上に配置する。

```
Amplifyコンテナ:
  - スタイル: shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_on_premise;strokeColor=#DD344C;dashed=1
  - 配置: VPC外・左上（x=50, y=50）。エッジサービスやVPCの左側に配置
  - サイズ: 約300x280（内部リソース数に応じて調整）

  構成要素（すべて parent="1" で配置し、コンテナの pointerEvents=0 によるエッジ阻害を回避）:
  1. Amplifyサービスアイコン: コンテナ左上（x=60, y=80, 40x40）
     - スタイル: fillColor=#DD344C;strokeColor=#ffffff;resIcon=mxgraph.aws4.amplify
  2. 「AWS Amplify」タイトルラベル: アイコン右横（fontSize=14, fontStyle=1）
  3. CloudFront CDN: 60x60
  4. Lambda SSR (Dynamic Content): 50x50
  5. S3 Static Content: 50x50

  内部エッジ（灰色、strokeColor=#666666）:
  - CloudFront → Lambda SSR（exitX=1,exitY=0 → entryX=0,entryY=0.5）
  - CloudFront → S3 Static（exitX=1,exitY=1 → entryX=0,entryY=0.5）

  外部エッジ（青、strokeColor=#0066CC、strokeWidth=2）:
  - Amplify CloudFront → メインCloudFront（ユーザートラフィックの流れ）
  - waypoint経由で接続し、「User Traffic」ラベルを付与
```

---

## 10. 色分けルール

### 10.1 AWSカテゴリ別アイコン色（fillColor）

アイコンの `fillColor` でAWSサービスカテゴリを色分けする。

| カテゴリ | fillColor | 対象サービス |
|---------|-----------|------------|
| ネットワーク | #8C4FFF (紫) | VPC, Route53, CloudFront, ELB, API Gateway |
| コンピュート | #ED7100 (オレンジ) | EC2, ECS, EKS, Lambda, Fargate |
| セキュリティ | #DD344C (赤) | WAF, ACM, Secrets Manager, KMS, Cognito |
| ストレージ | #7AA116 (緑) | S3, EFS, EBS |
| データベース | #5A30B5 (紫) | RDS, Aurora, DynamoDB, ElastiCache |
| CI/CD | #C925D1 (マゼンタ) | CodePipeline, CodeBuild, CodeDeploy |
| 監視 | #759C3E (深緑) | CloudWatch, X-Ray |
| メッセージング | #E7157B (ピンク) | SNS, SQS, EventBridge |

### 10.2 接続線の色

| 接続種別 | strokeColor | 用途 |
|---------|-------------|------|
| データフロー | #0066CC (青) | リクエスト/レスポンス |
| 依存関係 | #666666 (灰) | リソース間の参照 |
| デプロイ | #e74c3c (赤) | CI/CDパイプライン |
| コンソール/管理 | #8B4513 (茶) | 管理者アクセス |

---

## 11. 注釈・補足テキスト

### 11.1 注釈の配置ルール

アーキテクチャ図に補足情報を注釈として追加する。

```
注釈スタイル:
  fillColor=#ffe6cc;strokeColor=#d79b00;rounded=1;
  fontSize=11;fontColor=#333333;
  align=left;verticalAlign=top;
  whiteSpace=wrap;html=1;
```

### 11.2 注釈の配置位置

| 注釈種別 | 配置位置 |
|---------|---------|
| 全体説明 | ダイアグラム右上 |
| VPC設定 | VPCコンテナの右下外側 |
| セキュリティ注記 | 該当リソースの近傍 |
| スケーリング情報 | 該当リソースの右側 |

### 11.3 注釈の内容例

注釈は**ネットワーク構造・トポロジー・セキュリティ境界**に関する情報のみ記載する。

**記載してよい内容**:
- CIDR情報: 「VPC: 10.0.0.0/16」
- セキュリティ境界: 「SSL/TLS終端」「WAF有効」
- ポート情報: 「Port 443 (HTTPS)」
- リージョン/AZ: 「ap-northeast-1 Multi-AZ (1a/1d)」

### 11.4 注釈として記載してはいけない内容

以下の情報はアーキテクチャ図の責務外。記載しないこと。

#### サーバースペック・運用パラメータ

Terraform変数で管理される値であり、図で表現すると陳腐化しやすく、アーキテクチャ構造の理解も阻害する。

- **サイジング**: CPU/Memory（例: `CPU 512 / Mem 1024`）、ACU（例: `Min 0.5 ACU / Max 1 ACU`）、instance_type（例: `db.t4g.medium`）
- **タスク・レプリカ数**: `desired_count=2`, `2 tasks` など
- **Auto Scaling閾値**: `min=2, max=10` など
- **バックアップ保持期間**: `Backup 30日` など
- **プラットフォーム版数**: `Fargate platform 1.4.0` など
- **機能フラグ**: `Data API 有効`、`削除保護 ON` など

これらが必要な場合はTerraformコードや別途のスペック表を参照する設計とする。

#### 推測ベースの凡例・メタ情報

Terraformリソースから機械的に導出できない情報は、LLMの推測が入り込むため記載しない。決定論的レイアウトの原則（LLMの裁量を排除）と整合させる。

- **環境名凡例**: `Environment: prod`, `Env: dev` など（`environment` variableがTerraform内に明示されていない限り、ディレクトリ名やファイル名からの推測にすぎない）
- **デプロイフェーズ**: `Deploy Phase: 1-4 (network→ECS→CDN→CI/CD)` など（コードコメント由来の主観的な分類）
- **リリース戦略**: `Blue/Green deploy`、`Canary rollout` など（明示的なリソース定義がある場合を除く）
- **運用ポリシー**: `24x7 monitoring`, `oncall: team-xxx` など

例外的に環境名を図に含めたい場合は、**タイトル文字列**（例: `OurPick Prod Architecture`）として1箇所で表現するに留め、別立ての凡例注釈としては出さない。

### 11.5 エッジ色凡例（必須）

読者がエッジ色の意味を解釈できるよう、ダイアグラム左下に**エッジ色凡例**を必ず配置する。スキルが [drawio-xml-guide.md §5](drawio-xml-guide.md#5-スタイル定数) で定義したエッジスタイルに対応する。

**必須要件**:
- **タイトルは日本語「凡例」を使用**（`Legend` のような英単語は外部読者に伝わりづらいため禁止）
- ダイアグラムに実際に使われている色のみを列挙（使われていない線種は載せない）
- 注釈スタイル（`fillColor=#ffe6cc`）で背景を付ける

**凡例項目マスタ**（`drawio-xml-guide.md §5` のエッジスタイル定義と1対1対応）:

| 表示ラベル | 色 | 線種 | 対応スタイル定数 |
|---|---|---|---|
| 青実線: データフロー | `#0066CC` | 実線 | `DATA_FLOW` |
| 緑実線: ストレージアクセス | `#7AA116` | 実線 | `STORAGE_FLOW` |
| 赤実線: CI/CDデプロイ | `#e74c3c` | 実線 | `DEPLOY_FLOW` |
| 茶実線: コンソール/管理アクセス | `#8B4513` | 実線 | `CONSOLE_ACCESS` |
| 灰破線: 依存・ポーリング | `#666666` | 破線 | `DEPENDENCY` |
| 紫破線: DBレプリケーション | `#C925D1` | 破線 | `REPLICATION` |

**XML例**:
```xml
<mxCell id="legend" value="&lt;b&gt;凡例&lt;/b&gt;&lt;br/&gt;━━ 青実線: データフロー&lt;br/&gt;━━ 緑実線: ストレージアクセス&lt;br/&gt;━━ 赤実線: CI/CDデプロイ&lt;br/&gt;-- 灰破線: 依存・ポーリング&lt;br/&gt;-- 紫破線: DBレプリケーション"
  style="text;html=1;strokeColor=#d79b00;fillColor=#ffe6cc;align=left;verticalAlign=top;whiteSpace=wrap;rounded=1;fontSize=10;fontColor=#333333;spacingLeft=8;spacingRight=8;spacingTop=6;spacingBottom=6"
  vertex="1" parent="1">
  <mxGeometry x="80" y="[VPC下端+40]" width="280" height="100" as="geometry"/>
</mxCell>
```

配置: ダイアグラム左下（VPC外、最下部）。
