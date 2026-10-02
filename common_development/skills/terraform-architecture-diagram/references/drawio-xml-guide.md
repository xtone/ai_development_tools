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

### エッジラベル付与の判定基準（必須・whitelist 方式）

エッジラベルは **絶対省略**。例外は以下の **厳密な whitelist のみ**。リストに無いラベルは「具体的な action だから」「重要だから」「データの流れを示すから」等の理由で **個別判断による追加を絶対に行わない**。

#### ✅ 許可される唯一のラベル種別（whitelist）

ラベルは **構造情報のみ許可**。実装情報（ポート番号、認証機構、設定階層等）は接続の有無を変えないため、線では表現せず別ドキュメント（IAM 設計書、セキュリティ仕様等）で扱う。

| 種別 | 形式 | 具体例 | 適用条件 |
|------|------|--------|---------|
| **URL path pattern** | `/path/*` 形式 | `/api/client/*`, `/admin/*` | route の区別が必要な場合（同じ宛先でも path で分岐するロジックは構造情報） |
| **Deploy method** | 固定文字列 | `Blue/Green`, `Rolling`, `Canary` | 同色線（赤実線）で複数のデプロイ戦略が混在する場合のみ（デプロイトポロジは構造情報） |
| **AWS API call name**（Terraform リソースに紐づく specific call） | API 名そのまま | `RunTask`（aws_scheduler_schedule の target_action）, `Invoke`（lambda 直接呼び出し）| 一般的なデータフローではなく、Terraform で明示的に定義された specific API call の場合のみ（コントロールプレーン操作は構造情報） |

#### ⛔ 絶対に追加してはならないラベル（exhaustive list）

以下は「データの流れを示す」「具体的な動詞」「target アイコンの補足」「実装詳細」のいずれであっても、ラベルとして追加してはならない。**例外なし**：

- **TCP/UDP ポート番号**: `:3000`, `:5432`, `:443`, `:80` 等（実装詳細。線の存在と方向で接続は明示済み）
- **認証/セキュリティ機構**: `signed cookie`, `mTLS`, `OAuth`, `IAM auth`, `API key` 等（実装詳細。アクセス制御は IAM 設計書/セキュリティ仕様で扱う）
- **Origin priority**: `default origin`, `primary origin` 等（CloudFront の `default_cache_behavior` origin は太線 `strokeWidth=3` で hierarchy を表現する。ラベル不要）
- **線色・線種から自明な動詞**: `HTTPS`, `HTTP`, `image pull`, `push`, `push image`, `pull`, `poll`, `get`, `put`, `put/get`, `read`, `write`, `request`, `response`, `connect`, `access`
- **凡例で意味が確定している関係性**: `Aurora replication`, `replication`, `data flow`, `dependency`, `notification`, `event`, `failure event`, `state change`
- **target アイコンから自明な機能**: `origin`（→ ALB）, `logs`（→ S3 Logs）, `alert`（→ SNS）, `DLQ alarm`, `master_user_secret`（→ Secrets Manager）, `DB credentials`, `artifacts`, `cache`
- **CI/CD パイプラインの動詞**: `webhook`, `trigger build`, `trigger deploy`, `trigger`, `build`, `deploy`, `source`
- **集約された複数リソースの内訳**: `(api, auth-proxy, video-gen)` のような括弧書きリスト

判断に迷った場合は **省略する**（凡例＋線色＋線太さ＋target アイコンで読み手は理解できる）。

#### whitelist 適用例（softbank-ourpick prod の場合）

許可される 3 個のラベル：
- `/api/client/*` × 1（CloudFront Public → ALB のルーティング分岐）
- `RunTask` × 1（EventBridge Scheduler → ECS Batch のコントロールプレーン操作）
- `Blue/Green` × 1（CodeDeploy → ECS API のデプロイトポロジ）

合計 3 個。これ以外のエッジはすべて value="" で生成すること。

**CloudFront → default origin** は太線（`strokeWidth=3`）で hierarchy を表現（[layout-algorithm.md §9.6](layout-algorithm.md) 参照、ラベルは付与しない）。

#### ⛔ 同一 whitelist ラベル文字列の図全体での出現回数は 1 回のみ

同じ操作を表す edge が複数本存在する場合（例: EventBridge Scheduler から ECS Worker と ECS Video Worker への 2 本の RunTask edge）、**ラベル文字列を付与するのは 1 本のみ。残りの edge は `value=""` で生成する**。

理由: 同じ単語のラベルが図上に 2 箇所以上表示されると、読み手は「これは別の操作か？」と混乱する。同操作なら 1 回の表示で十分。

**判定 pseudo code:**
```
edges_by_label = group_edges_by(value)  # whitelist label 文字列でグループ化
for label, edges in edges_by_label:
    if len(edges) > 1:
        # source ID アルファベット順で先頭 1 本のみ value 維持
        edges_sorted = sort_by(edges, source_id)
        for edge in edges_sorted[1:]:
            edge.value = ""  # ラベル文字列を消す（edge 自体は残す）
```

**違反例 / 修正例:**

| 違反 | 修正 |
|------|------|
| `<mxCell ... source="eventbridge" target="ecs_worker" value="RunTask">` + `<mxCell ... source="eventbridge" target="ecs_video" value="RunTask">` | 1 本目: `value="RunTask"` 維持 / 2 本目: `value=""` |
| `<mxCell ... source="codedeploy" target="ecs_api_a" value="Blue/Green">` + `<mxCell ... source="codedeploy" target="ecs_api_d" value="Blue/Green">`（B-1 集約後に残った場合） | 1 本目: `value="Blue/Green"` / 2 本目: `value=""` |

**注意**: B-1 (エッジ集約) は **同一 source resource type → 同一 target ID** の per-AZ 重複を集約する規則。本ルールは **同一 whitelist label** が複数 edge にまたがる場合のラベル重複排除規則。両者は別の制約なので、両方適用する。

ラベル省略を前提とするため、**凡例（[layout-algorithm.md §11.5](layout-algorithm.md)）の網羅性が必須**。図中で使う全線色・線種が凡例に列挙されていない場合、読み手が線の意味を判別不能になる。

### エッジラベルの可読性確保（必須）

エッジラベルが他のアイコン・ノードラベル・別エッジのラベルと重なると、テキストが交錯して判読不能になる。以下を必ず実施する：

**1. 全エッジラベルに白背景を必須付与**

`value` を持つ全エッジに `fontBackgroundColor=#ffffff` を style に必ず追加する。これによりラベル文字が白背景の上に描画され、他要素と重なっても判読可能になる。

```xml
<!-- 必須: fontBackgroundColor=#ffffff -->
<mxCell id="e1" value="image pull" edge="1" parent="1" source="ecs_api_a" target="ecr"
        style="edgeStyle=orthogonalEdgeStyle;rounded=1;...;fontBackgroundColor=#ffffff;exitX=0.5;exitY=1;entryX=0.5;entryY=0">
```

**2. エッジラベル位置は source/target/中継ノードとの関係で決定する**

エッジラベルはデフォルトで edge 中央配置だが、これが他要素（中継ノード、別エッジのラベル、VPC 内アイコン等）と重なると判読不能になる。以下のルールで `<mxPoint as="offset"/>` を必ず指定する。

##### (2a) 中継ノード横切りの場合は target 寄り 70% 地点へ offset

エッジが source → target の経路途中で **他のアイコンを横切る場合**（典型: CodeDeploy → ECS API のエッジが ECS Worker を横切る）、ラベルが中継ノードの真上に来てしまい、視覚的に「中継ノードに紐づいたラベル」と誤認される。

判定基準: edge の経路上に source / target 以外の他 vertex の bounding box（幅・高さ）と交差する区間がある場合、または source と target の間に距離 ≥ 200px 離れた他 vertex がある場合。

対応: ラベルを **target 寄り 30% 地点（中央から target 側へ 30%）** に offset する。

```xml
<!-- CodeDeploy → ECS API (ECS Worker を横切る経路) の例 -->
<mxCell id="e_cd_api" value="Blue/Green" edge="1" source="codedeploy" target="ecs_api_d" ...>
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="200" y="0" as="offset"/>  <!-- 中央から target 側へ 200px シフト → ECS API 直近に表示 -->
  </mxGeometry>
</mxCell>
```

##### (2b) 長距離エッジのラベルは source 寄りに配置

`abs(source_y - target_y) > 600` の長距離エッジでは、デフォルトの中央配置だとラベルが他要素（VPC 内のノード等）と重なりやすい。`<mxPoint as="offset"/>` で source 寄り 30% 地点に配置する：

```xml
<mxCell id="e1" value="/api/client/*" edge="1" ...>
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="760" y="1310"/>
      <mxPoint x="130" y="1310"/>
    </Array>
    <mxPoint x="-280" y="0" as="offset"/>  <!-- 中央から source 側へ 280px シフト -->
  </mxGeometry>
</mxCell>
```

`offset` の x 値: 負値で source 側、正値で target 側へシフト（単位: px）。waypoint の中央点から計算してシフト量を決める。

##### 適用優先順位

1. (2a) 中継ノード横切りがある → target 寄り 30% 地点へ offset（中継ノードとの誤関連を防ぐ）
2. (2b) (2a) に該当せず長距離エッジの場合 → source 寄り 30% 地点へ offset
3. それ以外（短距離・直線エッジ） → offset なし（中央配置）

**3. 多行ラベル & 同一行内括弧書き補足情報の絶対禁止（例外なし）**

ノードラベル・エッジラベルともに、以下 2 種類のラベルを **絶対に作成してはならない**。例外なし。1 ラベル = 1 行・最短表現。

- **(3a) 改行を含むラベル**: `&#xa;`、`<br>`、`\n` 等
- **(3b) 同一行内の括弧書き補足情報**: デプロイ方式、バージョン、属性リスト、状態説明等を `(...)` で付記

「集約された複数リソースの内訳をラベルで明示する」「バージョン情報を併記する」「URL pattern を補足する」「実行時刻を併記する」「デプロイ方式を併記する」等の動機があっても、**両方禁止**。詳細を残したい場合は、ユーザー要望に応じて注釈セル（[layout-algorithm.md §11](layout-algorithm.md) 参照）で提示する（**デフォルトでは注釈セルを追加しない**）。

#### 括弧書きの「識別子」と「補足情報」の区別

(3b) は **同一リソースタイプの複数インスタンスを区別するための識別子のみ例外** として許可する。識別子か補足情報かは以下の基準で機械的に判定:

| 区分 | 形式 | 例 | 許可/禁止 |
|------|------|-----|----------|
| **識別子（許可）** | カッコ内が **1 単語**で、同一 resource type の複数インスタンスを区別する目的 | `CloudFront (Public)` / `CloudFront (Admin)`, `CodeBuild (api)` / `CodeBuild (Migration)`, `Aurora (Writer)` / `Aurora (Reader)` | ✅ 許可 |
| **補足情報（禁止）** | カッコ内がデプロイ方式・バージョン・属性リスト・状態説明等 | `ALB (Blue/Green)`, `CodePipeline (V2)`, `S3 (assets, signed)`, `ECR (api, auth-proxy)`, `RDS (Multi-AZ)` | ❌ 禁止 |

**判定 pseudo code:**
```
if value matches r'\((Public|Admin|API|Migration|Writer|Reader|primary|secondary)\)':
    OK  # 単語限定の識別子
elif value matches r'\([^)]+\)':
    VIOLATION  # それ以外の括弧書きは補足情報
```

#### 違反例 / 修正例

| 悪い例（絶対禁止） | 良い例 |
|-------|--------|
| `Aurora Writer&#xa;PostgreSQL Serverless v2` | `Aurora Writer` |
| `/api/client/*&#xa;(also: /admin/*)` | `/api/client/*` |
| `RunTask (4am JST)` | `RunTask` |
| `ECR&#xa;(api, auth-proxy, video-gen)` | `ECR` |
| `GitHub&#xa;xtone/repo (branch: main)` | `GitHub` |
| `CloudFront (Public)&#xa;Frontend + S3 OAC` | `CloudFront (Public)` |
| `CodePipeline (V2)&#xa;Source(CodeStar) → Build → Migration → Deploy` | `CodePipeline` |
| `ALB (Blue/Green)` ← Blue/Green は edge ラベルで表現済み | `ALB` |
| `S3 (assets, signed)` ← 補足情報 | `S3 Assets` ← 識別子化なら 1 単語で |
| `CodePipeline (V2)` ← バージョン情報 | `CodePipeline` |
| `RDS (Multi-AZ)` ← 構成情報 | `RDS` ← Multi-AZ 配置は図上の AZ コンテナで表現 |
| `ECR (api, auth-proxy)` ← 属性リスト | `ECR` |

**チェック方法**:
- 改行検出: `grep "&#xa;" *.drawio | grep "value="`
- 括弧書き補足情報検出: `grep -E 'value="[^"]+\([^)]+\)"' *.drawio | grep -vE 'value="[^"]+\((Public|Admin|API|Migration|Writer|Reader|primary|secondary)\)"'`

いずれかにヒットがあれば違反。

エッジラベルは「何の通信か」が一目で分かる最短表現に留める。属性詳細を図に残したい場合は、ユーザー要望に応じて注釈セル（[layout-algorithm.md §11](layout-algorithm.md) 参照）で提示できるが、**デフォルトでは注釈セルを追加しない**（情報密度を上げると図全体の認知負荷が増えるため）。

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

**長距離エッジへの waypoint 必須**

`abs(source_y - target_y) > 600` かつ source と target を直線結合すると他ノード（特に同じ tier の隣接ノード）を跨ぐ場合、`<Array as="points">` で **明示的な waypoint** を追加して経路を制御する。auto-routing に任せると中間ノードの近傍を通過し、視覚的に「中間ノードから出ている線」と誤読される。

waypoint 座標決定ルール:
- 1点目 x = source の bottom port x（垂直に下がる）
- 1点目 y = `min(target_y - 30, VPC_bottom + 30)`（VPC を回避し target 直前で水平移動）
- 2点目 x = target の top port x
- 2点目 y = 1点目 y と同じ

例: cf_public (730, 200) → s3_assets (100, 1340)（y距離 1140px、間に VPC（y=440〜1290）と cf_admin が存在）

```xml
<mxCell id="e_cfpublic_s3assets" ... source="cf_public" target="s3_assets"
        style="...;exitX=0.5;exitY=1;entryX=0.5;entryY=0">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="760" y="1310"/>   <!-- VPC 直下、左方向へ折り返す前 -->
      <mxPoint x="130" y="1310"/>   <!-- target 列上で下方向へ折り返す前 -->
    </Array>
  </mxGeometry>
</mxCell>
```

これにより線は「cf_public 真下に下がる → VPC 下端を水平移動 → s3_assets 真上に降りる」という決定論的経路になり、cf_admin の近傍を通過しない。

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

### ライン重複・被りの回避（必須）

`exitX/exitY/entryX/entryY` を指定していても、複数エッジが同じ目標点に集中すると線が重なって判読不能になる。以下 3 ルールを必須適用する。

#### B-1. エッジ集約原則（同一 resource type pair は 1 本に集約）

同一 **source resource type → 同一 target resource ID** の複数エッジは **必ず 1 本に集約**する。per-AZ で同じ接続を複数本描かない。

| パターン | 違反例（per-AZ で重複） | 正しい配置（集約） |
|---------|------------------------|-------------------|
| ALB → ECS API | `alb → ecs_api_a` (`:3000`) + `alb → ecs_api_d` (`:3000`) の 2 本（同ラベル重複） | `alb → ecs_api_a` 1 本のみ（subnets[0] AZ）。同 service type の他 AZ ノードへの接続は省略 |
| ECS API → Aurora Writer | `ecs_api_a → aurora_writer` + `ecs_api_d → aurora_writer` の 2 本 | `ecs_api_a → aurora_writer` 1 本のみ（subnets[0] AZ） |
| ECS Worker → SQS | `ecs_worker_a → sqs` + `ecs_worker_d → sqs` の 2 本 | `ecs_worker_a → sqs` 1 本のみ |

**判定 pseudo code:**
```
edges_by_pair = group_edges_by(source.resource_type, target.id)
for pair, edges in edges_by_pair:
    if len(edges) > 1:
        keep_only(edges[0])  # subnets[0] AZ の 1 本のみ残す
        delete(edges[1:])
```

**理由**: per-AZ ノードは「同じ service type が多重 AZ にある」事実を示すための表現であり、エッジは「service type 単位の論理接続」を示す。論理接続は 1 本で十分。

#### B-2. Entry/Exit Point 分散

同一 target に異なる source から複数エッジが入る場合、entry point の Y 座標を分散させて重なりを防ぐ。

| target に入る本数 | entry point Y 座標（または X 座標） |
|------------------|-----------------------------------|
| 1 | `0.5` |
| 2 | `0.33`, `0.67` |
| 3 | `0.25`, `0.5`, `0.75` |
| 4+ | `0.2`, `0.4`, `0.6`, `0.8`, ... （等分） |

source 側からの exit point も同様に分散。

例: Aurora Writer に 3 本のエッジが入る場合
```xml
<!-- Edge 1: ECS API → Aurora Writer -->
<mxCell ... entryX="0" entryY="0.25" .../>
<!-- Edge 2: ECS Worker → Aurora Writer -->
<mxCell ... entryX="0" entryY="0.5" .../>
<!-- Edge 3: ECS Video Worker → Aurora Writer -->
<mxCell ... entryX="0" entryY="0.75" .../>
```

#### B-3. Waypoint で swimlane 化

縦方向に複数エッジが平行に並ぶ場合（例: VPC 内の複数 service → 最下段マネージドサービス）、それぞれのエッジに `±15px` ずつ x オフセットの waypoint を追加して swimlane 化し、線同士の重なりを物理的に回避する。

```xml
<mxGeometry relative="1" as="geometry">
  <Array as="points">
    <mxPoint x="500" y="800"/>  <!-- source 側 swimlane offset -->
    <mxPoint x="500" y="900"/>  <!-- target 側 swimlane offset -->
  </Array>
</mxGeometry>
```

**判定基準**: 同方向（縦/横）に並走するエッジが 2 本以上ある場合、必ず waypoint を追加し、それぞれ x（または y）座標を **15px 以上ずらす**。

#### 自己検証 grep

- 重複エッジ検出: `grep 'edge="1"' file.drawio | grep -oE 'source="[^"]+" target="[^"]+"' | sort | uniq -c | awk '$1 > 1'` （ヒットがあれば B-1 違反）
- 同一 entry point に複数エッジ: `grep 'edge="1"' file.drawio | grep -oE 'target="[^"]+" .* entryY="[^"]+"' | sort | uniq -c | awk '$1 > 1'` （ヒットがあれば B-2 違反）

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

IMAGE_PULL = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#e74c3c;strokeWidth=1;dashed=1;endArrow=classic"
```

エッジにはポート番号をラベルとして付与する（例: 「Port 3000」「Port 5432」）。

### CI/CD 関連エッジの線種分類

CI/CD パイプラインに関わるエッジは、**制御フロー（trigger）とデータフロー（image pull / artifact upload）を線種で区別する**。同じ赤系統の線が交差するとトリガ元と Pull 元が混同されるため。

| エッジの意味 | 使用スタイル | 線種 |
|-------------|-------------|------|
| CodePipeline → CodeBuild / CodeDeploy（トリガ） | `DEPLOY_FLOW` | 赤実線 太 |
| CodeBuild → ECR（push）| `DEPLOY_FLOW` | 赤実線 太 |
| ECS Task Definition `image` → ECR（image pull） | `IMAGE_PULL` | **赤点線 細** |
| CodePipeline → S3 Artifacts（成果物保存） | `STORAGE_FLOW` | 緑実線 |
| EventBridge Scheduler → ECS Task（RunTask）| `DEPLOY_FLOW` | 赤実線 太 |

**ラベル付与の原則**:
- トリガ系: `trigger`, `deploy`, `run` 等の動詞ラベル
- Pull/Data 系: `image pull`, `artifact upload`, `put/get` 等のデータ方向を示すラベル

**判定ルール**:
- `aws_codepipeline.*.action` で参照されているリソース → trigger（実線）
- `aws_ecs_task_definition.container_definitions[*].image` が ECR リポジトリを指す → pull（点線）
- `aws_s3_bucket` が CodePipeline の `artifact_store` である → artifact upload（緑実線）

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
