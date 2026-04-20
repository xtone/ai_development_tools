# draw.io XML生成ベストプラクティス

draw.io XMLを生成する際のルールとベストプラクティス。
[jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) の skill-cli を基に、Terraformアーキテクチャ図向けに最適化。

### 外部リファレンス

- draw.io スタイルリファレンス: https://www.drawio.com/doc/faq/drawio-style-reference.html
- draw.io XML Schema: https://www.drawio.com/assets/mxfile.xsd
- drawio-mcp skill-cli（ベストプラクティスの出典）: https://github.com/jgraph/drawio-mcp/tree/main/skill-cli

## 目次

1. [XML基本構造](#1-xml基本構造)
2. [コンテナと親子関係](#2-コンテナと親子関係)
3. [アイコンスタイル](#3-アイコンスタイル)
4. [エッジルーティング](#4-エッジルーティング)
5. [スタイル定数](#5-スタイル定数)
6. [XML整形性ルール](#6-xml整形性ルール)
7. [ID生成規則](#7-id生成規則)
8. [ラベル規則](#8-ラベル規則)
9. [出力方法](#9-出力方法)
10. [ラベル配置パターン](#10-ラベル配置パターン)

---

## 1. XML基本構造

### .drawio ファイル形式

```xml
<mxfile host="app.diagrams.net" agent="Claude" version="22.1.0" type="device">
  <diagram name="Architecture" id="architecture-diagram">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1"
      tooltips="1" connect="1" arrows="1" fold="1" page="1"
      pageScale="1" pageWidth="1200" pageHeight="1600" math="0" shadow="0"
      adaptiveColors="auto">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- ここにセルを配置 -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### 基本ルール

- `id="0"` はルートレイヤー
- `id="1"` はデフォルト親レイヤー
- すべての図形要素は `parent="1"`（またはコンテナID）を指定
- `adaptiveColors="auto"` によりダークモード時に全色要素のコントラストが自動調整される（`simple`=白黒のみ調整、`none`=無効）

---

## 2. コンテナと親子関係

アーキテクチャ図ではコンテナの親子関係が最重要。重ねて配置するのではなく、`parent` 属性で正しく階層化する。

### コンテナタイプ

| タイプ | スタイル | 用途 |
|--------|---------|------|
| swimlane | `swimlane;startSize=30;` | タイトルバー付きコンテナ。コンテナ自体に接続がある場合に使用 |
| group | `group;` | 不可視コンテナ。接続を持たないグルーピング用 |
| カスタムコンテナ | 任意のシェイプ + `container=1;pointerEvents=0;` | AWS VPCグループ等のスタイル付きコンテナ |

### 必須ルール

- コンテナスタイルには必ず `container=1;collapsible=0;recursiveResize=0;` を付与
- 接続をキャプチャしたくないコンテナには `pointerEvents=0;` を付与
- 子要素は `parent="コンテナID"` を指定し、座標はコンテナからの相対座標を使用

### 例: VPC > AZ > Subnet > リソース

```xml
<!-- VPC -->
<mxCell id="vpc" value="VPC" style="...;container=1;pointerEvents=0;collapsible=0;"
  vertex="1" parent="1">
  <mxGeometry x="50" y="320" width="900" height="640" as="geometry"/>
</mxCell>

<!-- AZ（VPC相対座標） -->
<mxCell id="az1" value="AZ-1" style="...;container=1;collapsible=0;"
  vertex="1" parent="vpc">
  <mxGeometry x="20" y="40" width="400" height="580" as="geometry"/>
</mxCell>

<!-- Subnet（AZ相対座標） -->
<mxCell id="private_subnet_1" value="Private Subnet" style="...;container=1;pointerEvents=0;collapsible=0;"
  vertex="1" parent="az1">
  <mxGeometry x="20" y="160" width="360" height="400" as="geometry"/>
</mxCell>

<!-- リソース（Subnet相対座標） -->
<mxCell id="ecs_1" value="ECS" style="shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs;..."
  vertex="1" parent="private_subnet_1">
  <mxGeometry x="156" y="100" width="48" height="48" as="geometry"/>
</mxCell>
```

---

## 3. アイコンスタイル

### AWS

`mxgraph.aws4.*` 形式を使用。Draw.io Desktop版でネイティブサポート。

**重要**: AWSアイコンには2種類のスタイルがあり、サービスごとに正しいタイプを使い分ける必要がある。

#### スタイルタイプA: Direct Shape（サービス固有アイコン）

`shape=mxgraph.aws4.{service}` で直接シェイプを指定。`strokeColor=none` を使用。
ネットワーク系のインフラサービスで使用。

```
sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor={COLOR};strokeColor=none;html=1;shape=mxgraph.aws4.{SERVICE}
```

対象サービス:
- `internet` (User Traffic)
- `application_load_balancer` (ALB)
- `nat_gateway` (NAT Gateway)
- `internet_gateway` (IGW)
- `endpoints` (VPC Endpoints) ※ `endpoint` ではなく `endpoints`

#### スタイルタイプB: resourceIcon（四角バッジアイコン）

`shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{service}` で指定。`strokeColor=#ffffff` を使用。
ほとんどのマネージドサービスで使用。

```
sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor={COLOR};strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{SERVICE}
```

対象サービス: Route53, CloudFront, WAF, ACM, ECS/Fargate, Aurora, RDS, S3, ECR, Secrets Manager, CloudWatch, CloudTrail, SES, Lambda, SNS, EventBridge, CodePipeline, CodeDeploy, etc.

#### アイコン名の注意点

一部サービスは直感的でないアイコン名を使用する:

| サービス | 正しいアイコン名 | よくある間違い |
|---------|---------------|-------------|
| Fargate (ECS) | `fargate` | `ecs` |
| ACM | `certificate_manager_3` | `certificate_manager` |
| CloudWatch | `cloudwatch_2` | `cloudwatch` |
| VPC Endpoints | `endpoints` | `endpoint` |
| SQS | `sqs` | `simple_queue_service` |
| SNS | `sns` | `simple_notification_service` |

**注**: 誤ったアイコン名を使うとDrawio Desktop版でシェイプが解決されず、`fillColor` の単色四角形にフォールバックされる（ピンク矩形等）。[aws-resources.md](aws-resources.md) のマッピング表を参照すること。

#### Aurora特殊スタイル

Auroraはグラデーション付きの特殊スタイルを使用:

```
gradientColor=#945DF2;gradientDirection=north;fillColor=#5A30B5;strokeColor=#ffffff
```

#### ECS Console用の色分け

ECS Consoleサービスは茶色（`fillColor=#8B4513`）を使用し、API/Deviceサービスのオレンジ（`fillColor=#ED7100`）と区別する。

マッピング詳細は [aws-resources.md](aws-resources.md) を参照。

### GCP

**重要**: `mxgraph.gcp2.*` 形式はDraw.io Desktop版で表示されない。
SVG埋め込み形式を使用すること。

```xml
<mxCell id="gke_1" value="GKE"
  style="shape=image;aspect=fixed;imageAspect=0;image=data:image/svg+xml,{BASE64_SVG_DATA};labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top"
  vertex="1" parent="subnet_1">
  <mxGeometry x="100" y="100" width="48" height="48" as="geometry"/>
</mxCell>
```

SVGデータは [gcp-svg-icons.md](gcp-svg-icons.md) を参照。

---

## 4. エッジルーティング

### エッジの必須構造

エッジは必ず子要素 `<mxGeometry>` を持つ形式で記述する。自己閉じタグ（`<mxCell ... />`）はdraw.ioでレンダリングされない。

```xml
<!-- 正しい: 子要素を持つ -->
<mxCell id="e1" edge="1" parent="1" source="a" target="b" style="...">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- 間違い: 自己閉じタグ（描画されない） -->
<mxCell id="e1" edge="1" parent="1" source="a" target="b" style="..." />
```

### エッジラベル

エッジラベルにHTMLマークアップでフォントサイズを変更しない。デフォルトのフォントサイズは11pxで、そのまま使用する。

### 基本設定

全エッジに以下を適用：

```
edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;
```

### ノード間隔

- 最低間隔: 60px
- 推奨間隔: 水平200px、垂直120px
- 全ノードをグリッド（10の倍数）に配置

### アローヘッドクリアランス

エッジの最終直線セグメント（最後のベンドからターゲットまで）は最低20px確保する。
`orthogonalEdgeStyle` の自動ルーターは、ノードが近接していると短いセグメントを生成してアローヘッドが崩れる。

対策:
- ノード間隔を十分に確保する
- 必要に応じて明示的waypointsを追加する

### exitX/exitY/entryX/entryY

接続ポイントを制御する（値: 0-1）：

| 位置 | exitX/entryX | exitY/entryY |
|------|-------------|-------------|
| 上中央 | 0.5 | 0 |
| 下中央 | 0.5 | 1 |
| 左中央 | 0 | 0.5 |
| 右中央 | 1 | 0.5 |

接続が重ならないよう、異なるポートに分散させる。

**必須: 全エッジに exit/entry を明示する**

auto-routing（`exitX/exitY/entryX/entryY` の省略）は禁止。省略すると drawio が自動で近接ポートを選ぶが、source と target の間に他ノードがある場合、線が他ノード近傍を通過して「どのノードから出ている線か」が視覚的に曖昧になり、レビュアーに誤読される（例: `CloudFront Public → S3 Assets` の線が途中で `CloudFront Admin` のアイコン付近を通過し「Admin → S3」と誤読された実例あり）。

source → target の座標関係から方向を決めて割り当てる：

| 位置関係 | exit (source) | entry (target) |
|---------|---------------|----------------|
| source が上 | `exitY=1` | `entryY=0` |
| source が下 | `exitY=0` | `entryY=1` |
| source が左 | `exitX=1` | `entryX=0` |
| source が右 | `exitX=0` | `entryX=1` |

### waypointsの追加

```xml
<mxCell id="edge1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;..." edge="1" parent="1" source="a" target="b">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="300" y="150"/>
      <mxPoint x="300" y="250"/>
    </Array>
  </mxGeometry>
</mxCell>
```

### 中間ノード貫通の回避（線形チェーン原則）

同一軸（同じX または 同じY）に縦／横一列に並ぶ3つ以上のノード A, B, C が存在する場合、`A → C` のようなskip-connectエッジを描いてはならない。直線が中間ノード B を貫通し、エッジラベルが B のアイコンに被るため。

**必ず線形チェーン（A → B → C）で表現する。**

例: CI/CDパイプライン（縦一列）
- 悪い例: `CodePipeline → CodeBuild`（build）+ `CodePipeline → CodeDeploy`（deploy）← 2本目がCodeBuildを貫通
- 良い例: `CodePipeline → CodeBuild → CodeDeploy` の線形チェーン

やむを得ずskip-connectが必要な場合は、`<Array as="points">` で明示的なwaypointsを設定し、中間ノードの左右いずれかに迂回させる。

### コンテナ跨ぎのエッジ配置

- 同一コンテナ内の接続: `parent="コンテナID"`
- 異なるコンテナを跨ぐ接続: `parent="1"`（ルート）

---

## 5. スタイル定数

### AWSコンテナスタイル

```
VPC_STYLE = "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0"

AZ_STYLE = "fillColor=none;whiteSpace=wrap;html=1;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_availability_zone;verticalAlign=top;align=left;spacingLeft=30;dashed=1;container=1;collapsible=0;recursiveResize=0;strokeColor=#545B64;fontColor=#545B64"

PUBLIC_SUBNET_STYLE = "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet2;strokeColor=#7AA116;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#248814;dashed=0"

PRIVATE_SUBNET_STYLE = "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet2;strokeColor=#00A4A6;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;dashed=0"
```

### GCPコンテナスタイル

```
GCP_VPC_STYLE = "fillColor=#E6F2FF;strokeColor=#4285F4;dashed=0;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1;container=1;pointerEvents=0;collapsible=0"

GCP_ZONE_STYLE = "fillColor=#FFF8E6;strokeColor=#FBBC04;dashed=1;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1;container=1;collapsible=0"

GCP_SUBNET_STYLE = "fillColor=#E6E6FA;strokeColor=#5A5A9E;dashed=0;verticalAlign=top;align=left;spacingLeft=5;spacingTop=5;html=1;container=1;pointerEvents=0;collapsible=0"
```

### AWSアイコンスタイル（共通）

アイコンの `value` は空文字列にし、ラベルは別の `text` セルとして下に配置する（[セクション10](#10-ラベル配置パターン)参照）。

```
# タイプA: Direct Shape（ネットワーク系インフラサービス用）
AWS_ICON_DIRECT = "sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor={CATEGORY_COLOR};strokeColor=none;html=1;shape=mxgraph.aws4.{SERVICE}"

# タイプB: resourceIcon（マネージドサービス用）
AWS_ICON_RESOURCE = "sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor={CATEGORY_COLOR};strokeColor=#ffffff;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{SERVICE}"
```

`{SERVICE}` を具体的なサービス名に、`{CATEGORY_COLOR}` をカテゴリ別色に置換する。
タイプの使い分けは [セクション3](#3-アイコンスタイル) を参照。

#### カテゴリ別 fillColor

| カテゴリ | fillColor | 対象サービス例 |
|---------|-----------|-------------|
| ネットワーク | #8C4FFF | VPC, Route53, CloudFront, ELB, API Gateway |
| コンピュート | #ED7100 | EC2, ECS, EKS, Lambda, Fargate |
| セキュリティ | #DD344C | WAF, ACM, Secrets Manager, KMS, Cognito |
| ストレージ | #7AA116 | S3, EFS, EBS |
| データベース | #5A30B5 | RDS, Aurora, DynamoDB, ElastiCache |
| CI/CD | #C925D1 | CodePipeline, CodeBuild, CodeDeploy |
| 監視 | #759C3E | CloudWatch, X-Ray |
| メッセージング | #E7157B | SNS, SQS, EventBridge |

#### アイコンサイズ

標準サイズは **60x60px**（エッジサービス等の主要アイコン）または **50x50px**（サブネット内リソース）。48pxは使用しない。

### User Traffic（Internet）アイコン

```
USER_TRAFFIC_STYLE = "sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#232F3E;strokeColor=none;html=1;shape=mxgraph.aws4.internet"
```

ユーザーアクセスのエントリーポイントとして、VPC上部中央に配置する（上→下フローの起点）。

### サービスグループコンテナスタイル

```
# Multi-AZサービスグループ（オレンジ破線）
MULTI_AZ_GROUP = "rounded=1;strokeColor=#ED7100;dashed=1;fillColor=none;container=1;collapsible=0;recursiveResize=0;whiteSpace=wrap;html=1;verticalAlign=top;fontColor=#ED7100"

# DBクラスタグループ（マゼンタ破線）
DB_CLUSTER_GROUP = "rounded=1;strokeColor=#C925D1;strokeWidth=2;dashed=1;fillColor=none;container=1;collapsible=0;recursiveResize=0;whiteSpace=wrap;html=1;verticalAlign=top;fontColor=#C925D1"

# ECSクラスタグループ（オレンジ破線）
ECS_CLUSTER_GROUP = "rounded=1;strokeColor=#ED7100;dashed=1;fillColor=none;container=1;collapsible=0;recursiveResize=0;whiteSpace=wrap;html=1;verticalAlign=top;fontColor=#ED7100"
```

### CI/CDコンテナスタイル

```
CICD_CONTAINER = "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_on_premise;container=1;collapsible=0;recursiveResize=0;pointerEvents=0;strokeColor=#C925D1;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#C925D1;dashed=0;html=1;whiteSpace=wrap"
```

CI/CDパイプライン関連リソース（CodePipeline, CodeBuild, CodeDeploy等）を囲む。

### Amplifyコンテナスタイル

```
AMPLIFY_CONTAINER = "sketch=0;outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_on_premise;strokeColor=#DD344C;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#DD344C;dashed=1"
```

Amplifyコンテナの構成要素:
- **Amplifyサービスアイコン**: コンテナ左上に40x40で配置（`fillColor=#DD344C;resIcon=mxgraph.aws4.amplify`）
- **「AWS Amplify」タイトルラベル**: アイコン右横（fontSize=14, fontStyle=1）
- **内部リソース**: CloudFront CDN (60x60) + Lambda SSR (50x50) + S3 Static Content (50x50)
- **内部エッジ**: CF→Lambda, CF→S3（灰色 `strokeColor=#666666`）
- **外部エッジ**: Amplify CF → メインCloudFront（青 `strokeColor=#0066CC`、「User Traffic」ラベル）

**重要**: 内部リソースとエッジは `parent="1"`（ルート）に配置する。コンテナの `pointerEvents=0` によりエッジ接続が阻害されるため、子要素としてではなく座標で視覚的にコンテナ内に配置する。

### 注釈スタイル

```
ANNOTATION_STYLE = "text;html=1;strokeColor=#d79b00;fillColor=#ffe6cc;align=left;verticalAlign=top;whiteSpace=wrap;rounded=1;fontSize=11;fontColor=#333333;spacingLeft=5;spacingRight=5;spacingTop=5;spacingBottom=5"
```

背景色付きテキストセルでアーキテクチャの補足情報を表示する。

### エッジスタイル

```
DATA_FLOW = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0066CC;strokeWidth=2;endArrow=classic"

DEPENDENCY = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#666666;strokeWidth=1;dashed=1;endArrow=classic"

DEPLOY_FLOW = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#e74c3c;strokeWidth=2;endArrow=classic"

CONSOLE_ACCESS = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#8B4513;strokeWidth=1;endArrow=classic"

REPLICATION = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#C925D1;strokeWidth=1;dashed=1;endArrow=classic"

STORAGE_FLOW = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7AA116;strokeWidth=2;endArrow=classic"
```

エッジにはポート番号をラベルとして付与する（例: 「Port 3000」「Port 5432」）。

### タイトルスタイル

```
TITLE_STYLE = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=24;fontStyle=1"
```

---

## 6. XML整形性ルール

### 必須

- XMLコメント内で `--` を使わない（XML仕様違反でパースエラーになる）
- 属性値内の特殊文字をエスケープ: `&amp;`, `&lt;`, `&gt;`, `&quot;`
- すべての `mxCell` に一意の `id` を付与
- `vertex="1"` (ノード) または `edge="1"` (エッジ) を必ず指定
- `mxGeometry` を必ず含める

### 推奨

- インデント: スペース2つ
- セルの記述順: コンテナ → 子要素 → エッジ（親から子の順で記述）
- コメントでTier区切りを明示

---

## 7. ID生成規則

パターン: `{provider}_{resource_type}_{index}`

例:
- `aws_ec2_1`, `aws_rds_1`
- `gcp_gke_1`, `gcp_sql_1`
- `vpc`, `az1`, `az2`
- `public_subnet_1`, `private_subnet_1`
- `edge_alb1_ecs1` (接続線)
- `title` (タイトル)

同一タイプの複数リソースには `_1`, `_2` のインデックスを付与。

---

## 8. ラベル規則

1. Terraformの `name` 属性があればそれを使用
2. なければリソース名（`resource "aws_instance" "web"` の `web`）を使用
3. 最大20文字。長い場合は `value="行1&#xa;行2"` で改行
4. コンテナラベルにはTerraform名 + 説明を含める
   - 例: `VPC (10.0.0.0/16)`, `Private Subnet (10.0.1.0/24)`

---

## 9. 出力方法

Write ツールで `<mxfile>` 形式のXMLをファイルに書き出す。
ファイル名はダイアグラム内容に基づく（例: `aws-architecture.drawio`）。

```bash
# macOSで開く（draw.io Desktop が起動）
open aws-architecture.drawio
```

Desktop がない環境では [draw.io](https://app.diagrams.net/) に `.drawio` ファイルをドラッグ＆ドロップすれば閲覧できる。

---

## 10. ラベル配置パターン

### アイコンとラベルの分離

リファレンス品質の図では、アイコンの `value` を空文字列にし、ラベルは別の `text` セルとして下に配置する。これにより、アイコンとラベルの位置を独立して調整できる。

#### XML例

```xml
<!-- アイコン（value は空文字列） -->
<mxCell id="ecs_icon" value=""
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ecs"
  vertex="1" parent="private_subnet_1">
  <mxGeometry x="100" y="80" width="60" height="60" as="geometry"/>
</mxCell>

<!-- ラベル（別テキストセル、アイコンの下に配置） -->
<mxCell id="ecs_label" value="ECS Service"
  style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=12"
  vertex="1" parent="private_subnet_1">
  <mxGeometry x="85" y="145" width="90" height="20" as="geometry"/>
</mxCell>
```

#### 配置ルール

- ラベルの `x` = アイコンの `x` - (ラベル幅 - アイコン幅) / 2（中央揃え）
- ラベルの `y` = アイコンの `y` + アイコンの `height` + 5px
- ラベルの `width` = アイコンの `width` + 30px（テキストが収まるよう余裕を持たせる）
- ラベルの `height` = 20px

**⚠️ 重要**: ラベルは**必ずアイコンの下**に配置する。「近傍にスペースが足りない」「他要素と衝突する」等の理由でアイコンの上／横に配置してはならない。衝突する場合はアイコン自体の座標を移動して解決する。親コンテナが異なるセル同士（例: subnet内のリソースラベル と root配置のラベル）の衝突は、絶対座標を計算して検証すること。

#### VPC Endpointsの集約ラベル例

```xml
<!-- VPC Endpoint アイコン -->
<mxCell id="vpce_icon" value=""
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#8C4FFF;html=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.vpc_endpoints"
  vertex="1" parent="vpc">
  <mxGeometry x="400" y="500" width="50" height="50" as="geometry"/>
</mxCell>

<!-- 集約ラベル -->
<mxCell id="vpce_label" value="VPC Endpoints&#xa;(ECR, Secrets, Logs)"
  style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=11"
  vertex="1" parent="vpc">
  <mxGeometry x="370" y="555" width="110" height="35" as="geometry"/>
</mxCell>
```

#### User Trafficエントリーポイント例

VPC上部中央に配置し、上→下フローの起点とする。

```xml
<!-- User Traffic アイコン（VPC上部中央） -->
<mxCell id="user_traffic" value=""
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#232F3E;strokeColor=none;html=1;shape=mxgraph.aws4.internet"
  vertex="1" parent="1">
  <mxGeometry x="545" y="60" width="60" height="60" as="geometry"/>
</mxCell>

<!-- ラベル -->
<mxCell id="user_traffic_label" value="User Traffic"
  style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=12"
  vertex="1" parent="1">
  <mxGeometry x="530" y="125" width="90" height="20" as="geometry"/>
</mxCell>
```

---

## 参考リンク

- draw.io スタイルリファレンス: https://www.drawio.com/doc/faq/drawio-style-reference.html
- draw.io XML Schema: https://www.drawio.com/assets/mxfile.xsd
