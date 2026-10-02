---
name: terraform-architecture-diagram
description: TerraformコードからDraw.io形式（.drawio）のクラウドアーキテクチャ図を自動生成するスキル。AWS、Google Cloudに対応。決定論的レイアウトアルゴリズムにより安定した図を生成。「Terraformからアーキテクチャ図を作成」「インフラ構成図を生成」「.tfファイルから図を作成」「アーキテクチャ図を更新」「インフラ変更の差分レポート」などのリクエスト時に使用。
---

# Terraform Architecture Diagram Generator

Terraform（`.tf`）コードを解析し、決定論的レイアウトで draw.io アーキテクチャ図を生成する。

## ⛔ 最重要ルール TOP-12（生成前に必ず確認・例外なし）

以下は LLM の解釈余地を残さず厳守する rule。違反は reject 対象。本リストは「落としやすい・忘れがちな」最重要 rule の早見表。詳細は各リンク先 reference。

| # | ルール | 違反例 |
|---|-------|--------|
| 1 | **エッジラベルは whitelist 以外絶対禁止** | `image pull`, `Aurora replication`, `poll`, `push`, `webhook` 等を付与（→ [drawio-xml-guide.md §エッジラベル付与の判定基準](references/drawio-xml-guide.md)） |
| 2 | **ノードラベルは 1 行・最短表現** （`&#xa;`/`<br>` 改行 **および** 同一行内括弧書き補足情報の両方禁止。例外: `(Public)`/`(Admin)`/`(Writer)` 等の 1 単語識別子のみ許可）| ① 改行: `ECR&#xa;(api, auth-proxy, video-gen)`、`Aurora Writer&#xa;PostgreSQL Serverless v2` ② 括弧書き補足: `ALB (Blue/Green)`, `CodePipeline (V2)`, `S3 (assets, signed)`, `RDS (Multi-AZ)`（→ §エッジラベル可読性確保 #3） |
| 3 | **CI/CD container 必須**（`aws_codepipeline` 等が存在する場合） | CI/CD コンテナ枠を省略する（→ [layout-algorithm.md §9.9](references/layout-algorithm.md)） |
| 4 | **ECS Multi-AZ Spanning Service は subnets[0] AZ 内に 1 アイコン + 注釈**（`desired_count != subnets` の場合）| ① `desired_count=1` の Video Worker を priv_sub_a / priv_sub_d 両方に配置 ② AZ コンテナ外（`parent="vpc"`、最下段の S3/SQS と同列等）に配置 ③ 注釈テキスト省略（→ §9.7 絶対禁止条項） |
| 5 | **Compute と Database の同 y 横並び禁止** | priv_sub 内で `[ECS API] [ECS Worker] [Aurora Writer]` を同じ y で並べる（→ §1 Tier 5 細分化） |
| 6 | **凡例以外の注釈セル追加禁止**（例外: §9.7 で必須化された Multi-AZ Spanning service の注釈のみ）| `Network` info callout、`ECS Cluster (Fargate)` italic 注釈、`Aurora Cluster (Multi-AZ)` 説明文 |
| 7 | **エッジ色は固定パレットのみ**: `#0066CC`(青)/`#7AA116`(緑)/`#e74c3c`(赤)/`#666666`(灰)/`#C925D1`(紫)/`#8B4513`(茶) | 独自色（黒、オレンジ、独自紫等）を新規追加 |
| 8 | **外部サービスは SVG 必須**（GitHub / Firebase Hosting 等） | plain 矩形 / `mxgraph.signs.tech.*` で代用（→ [external-service-icons.md](references/external-service-icons.md)） |
| 9 | **全エッジに `exit/entry` 必須**（auto-routing 禁止） | `exitX/exitY/entryX/entryY` 未指定 → drawio 自動経路で他ノード貫通 |
| 10 | **CloudFront 全 origin にエッジ必須**（`default_cache_behavior` + 全 `ordered_cache_behavior`） | S3 Assets origin へのエッジ欠落、`signed cookie` ラベルだけ宙浮き（→ [layout-algorithm.md §9.6 絶対必須条項](references/layout-algorithm.md)） |
| 11 | **Step 6.5 セルフ検証必須** | Step 6 の XML 生成後、grep チェックを実行せずに Step 7 へ進む |
| 12 | **同一 whitelist ラベル文字列は図全体で 1 回のみ表示**（同じ操作を表す複数 edge があっても、ラベルは正規 edge 1 本のみに付与し、他は `value=""`）| EventBridge Scheduler から ECS Worker と ECS Video Worker への 2 本の RunTask edge 両方に `value="RunTask"` 付与 → 図上に `RunTask` が 2 箇所表示。正解は 1 本目に `value="RunTask"`、2 本目に `value=""` |

⚠️ **重要**: これら 12 個は「common architecture diagram convention」に反する場合がある（例: 通常はラベルを付ける線にも本 skill ではラベル省略する）。**「分かりやすさのため」「補足情報として」等の理由で個別判断による例外を作ることを絶対に禁止**。

---

## ワークフロー

### Step 1: .tf ファイル読み込み

指定ディレクトリの全 `.tf` ファイルを読み込む。

```bash
find {path} -name "*.tf" -type f
```

モジュール参照（`source = "./modules/xxx"`）がある場合はモジュール内も展開する。

### Step 2: リソース・依存関係の抽出

各 `.tf` ファイルから以下を抽出:
- `resource` ブロック（タイプ + 名前）
- `module` ブロック（モジュール参照）
- 依存関係:
  - `depends_on` による明示的依存
  - 参照式（`aws_instance.web.id` 等）
  - LBターゲット、セキュリティグループ関連

### Step 3: プロバイダー判定

リソースプレフィックスで判定:
- `aws_*` → AWS
- `google_*` → Google Cloud
- 両方存在 → マルチクラウド構成

### Step 4: リソース分類

リソースをTier階層に分類する。分類はリソースタイプ名から機械的に判定。

| 分類 | 配置場所 | 代表的なリソース |
|------|---------|----------------|
| user_traffic | VPC上部中央（上→下フローの起点） | Internet（ユーザーアクセスのエントリーポイント） |
| edge | VPC上部中央寄せ横並び | Route53, CloudFront, WAF, ACM, Cloud DNS, Cloud CDN |
| public | パブリックサブネット | NAT Gateway, Cloud NAT, Cloud Router |
| alb | VPC直下（AZ横断） | ALB（サブネットに属さず、AZ間の中央に配置） |
| private | プライベートサブネット | EC2, ECS, EKS, Lambda, RDS, Aurora, Cloud Run, GKE, Cloud SQL |
| vpc_endpoint | VPC直下（AZ間集約） | VPC Endpoints（1アイコンに集約、テキストで内訳表示） |
| amplify | VPC外・左上（独立コンテナ） | Amplify（内部にCloudFront + Lambda SSR + S3） |
| managed | VPC外下部 | S3, ECR, Secrets Manager, CloudWatch, Cloud Storage, Pub/Sub |
| side | 右側 | CodePipeline, CodeBuild, Step Functions, Cloud Build |
| skip | 図示省略（配線的存在） | IAMロール/ポリシー, セキュリティグループルール, ルートテーブル, IGW, LBリスナー |

分類に該当しないリソースは `managed` にフォールバック。

#### サービスグルーピング

リソース分類後、以下のグルーピングを判定する:
- **Multi-AZサービス**: 同一リソースタイプが複数AZに存在する場合、破線コンテナ（`strokeColor=#ED7100`）で囲む
- **Single AZサービス**: 同一AZ内の密接に関連するリソース群を破線コンテナで囲む
- **DBクラスタ**: Aurora Cluster、RDS Multi-AZは破線コンテナ（`strokeColor=#5A30B5`）で囲む
- **ECSクラスタ**: ECS Service + Task Definitionは破線コンテナで囲む

詳細な分類ルールは [references/layout-algorithm.md](references/layout-algorithm.md) セクション4.1を参照。

### Step 5: 決定論的レイアウト計算

**重要**: 座標計算は以下のルールに厳密に従い、LLMの裁量による配置を行わない。

1. **AZ数の判定**: サブネットリソースのAZ指定から推定
2. **コンテナサイズの動的計算**: リソース数に応じてサブネット→AZ→VPCのサイズを自動計算
3. **座標の決定論的計算**: 全座標を固定ルールで計算し、10の倍数にグリッド配置
4. **リソース配置順序**: 優先順位（Compute→DB→Cache→Storage）とアルファベット順で決定
5. **ALBのAZ横断配置**: ALBはVPC直下（`parent=vpc`）に配置し、AZ間の中央・Public/Private境界に水平配置
6. **VPC Endpointsの集約**: 複数VPC Endpointは1アイコンに集約し、テキストラベルで内訳（ECR, Secrets, Logs等）を表示。AZ群の下部に配置
7. **Amplifyの独立コンテナ**: AWS AmplifyはVPC外に独立コンテナとして配置し、内部にCloudFront CDN + Lambda SSR + S3 Static Contentを含む

詳細は [references/layout-algorithm.md](references/layout-algorithm.md) を参照。

### Step 6: draw.io XML生成

以下のルールでXMLを生成:

- **コンテナ**: `parent` 属性で親子関係を定義。`container=1;pointerEvents=0;collapsible=0;` を付与
- **アイコン**: AWS は `mxgraph.aws4.*` 形式（`sketch=0`、サイズ50-60px）、GCP は SVG埋め込み形式
- **3rd Party サービス（非 AWS / 非 GCP）**: GitHub・Firebase Hosting 等は **必ず SVG 埋め込み形式**で描画する（[references/external-service-icons.md](references/external-service-icons.md) 参照）。`mxgraph.signs.tech.*` 等のシェイプは Desktop 版で fallback され単色矩形になるため禁止。Plain 矩形での代替表現も禁止
- **カテゴリ別色分け**: アイコンの `fillColor` でAWSカテゴリを色分け（ネットワーク=#8C4FFF、コンピュート=#ED7100、セキュリティ=#DD344C、ストレージ=#7AA116、DB=#5A30B5）
- **ラベル分離**: アイコンの `value` は空文字列にし、ラベルは別の `text` セルとして下に配置
- **User Traffic**: `shape=mxgraph.aws4.internet` でエントリーポイントを明示（VPC上部中央に配置、上→下フローの起点）
- **エッジ**: `edgeStyle=orthogonalEdgeStyle;rounded=1;` を使用。最終直線セグメント20px以上確保。接続線は色分け（データフロー=#0066CC青、デプロイ=#e74c3c赤、コンソール=#8B4513茶）
  - **全エッジに `exitX/exitY/entryX/entryY` を必ず指定**（auto-routing 禁止、線の始点曖昧さによる誤読防止）
  - **エッジラベルは原則省略**。線色＋target アイコンで意味判別する設計。残す条件: URL path / port（複数ポートが収束/分岐する場合のみ）/ 主従区別 / デプロイ方式の差別化 / 認証機構 / 特定の実行アクションのみ
  - 残った全エッジラベルに `fontBackgroundColor=#ffffff` を必ず付与（重なっても判読可能化）
  - 詳細: [drawio-xml-guide.md §エッジラベル付与の判定基準](references/drawio-xml-guide.md) および §エッジラベルの可読性確保
- **注釈テキスト**: **デフォルトでは追加しない**。ユーザーが明示的に「補足情報を追加して」と指示した場合のみ `fillColor=#ffe6cc` の背景付きテキストセルを使用。
  - 唯一の例外: **凡例セル（必須）** — [layout-algorithm.md §11.5](references/layout-algorithm.md#115-エッジ色凡例必須) 参照、ダイアグラムで使用している全線色・線種を漏れなく列挙
  - 追加する場合の禁止事項: サーバースペック（CPU/Memory/ACU/instance_type/task数/Auto Scaling閾値/バックアップ保持等）は記載しない（詳細は [layout-algorithm.md §11.4](references/layout-algorithm.md#114-注釈として記載してはいけない内容)）
- **グリッド**: 全座標を10の倍数に配置

AWSリソースマッピング: [references/aws-resources.md](references/aws-resources.md)
GCPリソースマッピング: [references/gcp-resources.md](references/gcp-resources.md)
GCP SVGアイコン: [references/gcp-svg-icons.md](references/gcp-svg-icons.md)
外部サービス（GitHub / Firebase 等）SVG: [references/external-service-icons.md](references/external-service-icons.md)
XML生成ルール全体: [references/drawio-xml-guide.md](references/drawio-xml-guide.md)

#### ⛔ 禁止事項（生成前に必ず確認）— 例外なし

以下のパターンを skill 出力に含めてはならない。「具体的な action だから」「重要だから」「データの流れを示すから」等の理由で **個別判断による例外を絶対に作らない**。reject 対象：

| 禁止 | 具体例（これ自体も禁止） | 理由 / 代替 |
|------|------------------------|------------|
| **エッジラベルは whitelist 以外絶対禁止** | `image pull`, `push`, `pull`, `poll`, `Aurora replication`, `replication`, `HTTPS`, `HTTP`, `webhook`, `trigger build`, `trigger deploy`, `failure event`, `alert`, `DLQ alarm`, `access logs`, `logs`, `origin`, `master_user_secret`, `DB credentials`, `artifacts`, `put/get`, `get`, `put`, `read`, `write` | 凡例＋線色＋target アイコンで意味判別可能。**許可される唯一のラベル種別は drawio-xml-guide.md §エッジラベル付与の判定基準 の whitelist のみ**（URL path / port / `default origin` / `Blue/Green` 等）|
| **多行ノードラベル（`&#xa;`、`<br>`、`\n` 含む）絶対禁止** | `ECR&#xa;(api, auth-proxy, video-gen)`、`CloudFront (Public)&#xa;Frontend + S3 OAC`、`GitHub&#xa;xtone/repo (branch: main)`、`Aurora Writer&#xa;PostgreSQL Serverless v2`、`CodePipeline (V2)&#xa;Source → Build → Deploy` | ラベルは **1 行・最短表現** に絶対固定。集約リソースの内訳・バージョン・stage 一覧等の副情報は付けない。詳細はユーザー要望時のみ注釈セルで提示 |
| **凡例以外の注釈セル** | `Network` info callout、`Security` info callout、`Aurora Serverless v2 Cluster (Multi-AZ)` 説明文、その他「補足情報」と称する `fillColor=#ffe6cc` ブロック | デフォルト追加禁止。ユーザーが「補足情報を追加して」と明示要望した場合のみ追加可 |
| **案件固有識別子のラベル** | リポジトリ名（`xtone/softbank-ourpick`）、AWS アカウント ID、ブランチ名（`branch: main`）、環境 path（`infra/environments/prod`）、Terraform module path | 図の汎用性を損ねる。タイトルもパス情報を含めず `<プロジェクト名> <env> Architecture` 形式 |
| **`mxgraph.signs.tech.*` 等のフォールバック描画される shape** | GitHub / Firebase Hosting / Slack 等を plain 矩形 / 単色四角形で代用 | Desktop 版で正しく描画されない。必ず external-service-icons.md の SVG 埋め込み形式を使用 |
| **不要なポート番号ラベル** | 全エッジに `:443`, `:80`, `:3000`, `:5432` を付与 | port 情報は **同一 source/target 間で複数ポート区別が必要な場合のみ** 付与。単一接続でのポート明示は禁止 |
| **`auto-routing` 依存エッジ** | `<mxCell ... edge="1" style="...">` で `exitX/exitY/entryX/entryY` 未指定 | 線の始点が曖昧になり中間ノード近傍を通過して誤読される。全エッジに必ず付与 |
| **ECS Multi-AZ サービスの重複描画** | `desired_count=1` の Video Worker を `priv_sub_a` と `priv_sub_d` の両方にアイコン配置 | `desired_count` が subnet 数と一致しない場合は **VPC 直下に 1 アイコンのみ**。両 AZ への重複配置禁止（[layout-algorithm.md §9.7](references/layout-algorithm.md) 絶対禁止条項参照）|
| **Compute と Database の同 y 横並び配置** | priv_sub 内で `[ECS API] [ECS Worker] [Aurora Writer]` のように Compute と DB を同じ y で並べる | Compute は **上段**（subnet 相対 y=50〜130）、Database は **下段**（subnet 相対 y=220〜300）。階層を分ける（[layout-algorithm.md §1 Tier 5 細分化ルール](references/layout-algorithm.md) 参照）|

### Step 6.5: セルフ検証（必須・違反検出時は修正してから Step 7 へ）

Step 6 で生成した `.drawio` ファイルに対し、以下の **3 つの grep ベースチェック** を必ず実行する。違反が 1 件でも検出された場合、該当セルを修正したうえで本 Step 6.5 を **0 件になるまでループ**。検証を省略して Step 7 へ進むことを禁止する。

#### Check 1: ラベル違反検出（改行 + 同一行内括弧書き補足情報）

```bash
# (1a) 改行ラベル検出
grep '&#xa;' <生成ファイル>.drawio | grep 'value='

# (1b) 同一行内括弧書き補足情報検出（識別子の 1 単語例外を除外）
grep -E 'value="[^"]+\([^)]+\)"' <生成ファイル>.drawio | grep -vE 'value="[^"]+\((Public|Admin|API|Migration|Writer|Reader|primary|secondary)\)"'
```

- **期待 (1a)**: ヒットなし
- **期待 (1b)**: ヒットなし（1 単語識別子のみ許可）
- **違反時の対応**:
  - (1a) 該当 mxCell の `value` から `&#xa;` 以降を削除。1 行・最短表現に修正
  - (1b) 該当 mxCell の `value` から括弧書き部分を削除。デプロイ方式・属性リスト等の補足情報はノードラベルに含めず、edge ラベル (whitelist 内) または注釈セルで表現する
- **例**:
  - (1a) `value="ECR&#xa;(api, auth-proxy, video-gen)"` → `value="ECR"`
  - (1b) `value="ALB (Blue/Green)"` → `value="ALB"`（Blue/Green 情報は CodeDeploy → ECS API edge のラベルで表現済み）
  - (1b) `value="CodePipeline (V2)"` → `value="CodePipeline"`
  - (1b) 例外: `value="CloudFront (Public)"` は許可（Public/Admin の 1 単語識別子で同一 resource type の複数インスタンスを区別）

#### Check 2: 禁止エッジラベル検出（whitelist 違反）

```bash
grep 'edge="1"' <生成ファイル>.drawio | grep -v 'value=""' | sed -E 's/.*value="([^"]+)".*/\1/' | sort -u
```

- **期待**: 出力に含まれるラベルが [drawio-xml-guide.md §エッジラベル付与の判定基準](references/drawio-xml-guide.md) の whitelist 3 カテゴリのみ：
  - **URL path pattern**（`/api/client/*`, `/admin/*` 等）
  - **Deploy method**（`Blue/Green`, `Rolling`, `Canary`）
  - **AWS API call name**（`RunTask`, `Invoke` 等の Terraform に紐づく specific call）
- **違反時の対応**: whitelist 外のラベル（実装詳細: `:3000`, `:5432`, `signed cookie`, `mTLS`, `OAuth`, `default origin` / 自明動詞: `image pull`, `Aurora replication`, `poll`, `push`, `webhook`, `failure event`, `alert`, `access logs`, `replication`, `HTTPS`, `HTTP` / target 自明: `master_user_secret`, `DB credentials`, `artifacts`, `origin`, `logs`, `DLQ alarm` 等）が検出された場合、該当 mxCell の `value` を `""` に変更

#### Check 3: 凡例以外の注釈セル検出

```bash
grep 'fillColor=#ffe6cc' <生成ファイル>.drawio | wc -l
```

- **期待**: 凡例セルの数（通常 1 〜 2、`legend` と `legend_content` の text セル）
- **違反時の対応**: 凡例以外で `fillColor=#ffe6cc` を持つセル（`Network` info callout、`Security` info callout、`Aurora Serverless v2 Cluster (Multi-AZ)` 説明文等）を全て削除

#### Check 4: CI/CD container 存在検証（aws_codepipeline 等が TF にある場合のみ）

```bash
grep 'value="CI/CD"' <生成ファイル>.drawio | wc -l
```

- **期待**: `aws_codepipeline` / `aws_codebuild_project` / `aws_codedeploy_app` / `aws_codedeploy_deployment_group` のいずれかが Terraform に存在する場合、ヒット数 ≥ 1
- **違反時の対応**: `<mxCell id="cicd" value="CI/CD" style="rounded=1;...strokeColor=#C925D1;dashed=1;...container=1;..." vertex="1" parent="1">` を追加し、GitHub / CodePipeline / CodeBuild / CodeDeploy を `parent="cicd"` に再配置（[layout-algorithm.md §9.9](references/layout-algorithm.md) 参照）

#### Check 5: ECS Multi-AZ Spanning Service の配置検証

```bash
# (5a) Video Worker など desired_count != subnets の service について、複数アイコン配置を検出
grep -oE 'id="ecs_video[^"]*"' <生成ファイル>.drawio | sort -u | wc -l

# (5b) Multi-AZ Spanning ECS service の parent が AZ コンテナ内 Private Subnet であることを検証
grep -E '<mxCell id="ecs_video"' <生成ファイル>.drawio | grep -oE 'parent="[^"]+"'

# (5c) AZ Spanning 注釈テキストの存在検証
grep -E 'subnets=\[.+\].+desired_count' <生成ファイル>.drawio | wc -l
```

- **期待 (5a)**: 1（`desired_count=1` で複数 AZ subnets 指定の場合、`ecs_video` 1 アイコンのみ）
- **期待 (5b)**: `parent="priv_sub_<az>"` 形式（subnets リスト先頭の AZ の Private Subnet コンテナ ID）。`parent="vpc"` / `parent="1"` / `parent="root"` は違反
- **期待 (5c)**: ≥ 1（Multi-AZ Spanning service には注釈テキストが必須）
- **違反時の対応**:
  - (5a) `ecs_video_a` / `ecs_video_d` 等の重複アイコンを削除し、`ecs_video` 1 つに統合
  - (5b) `parent` 属性を `subnets` リスト先頭の AZ 内 Private Subnet コンテナ ID に変更し、座標を Tier 5 上段（ECS API/Worker と同列、例: Private Subnet 相対 x=320, y=50）に再配置
  - (5c) Video Worker アイコン直下に italic 注釈「※ subnets=[a,d] / desired_count=1 / 両AZにまたがり最大1タスク」を追加

#### Check 6: 注釈テキスト（italic 等）検出

```bash
grep -E 'fontStyle=2|<i>' <生成ファイル>.drawio
```

- **期待**: ヒットなし（または以下の例外のみ許可）
  - 凡例内の意図的な装飾
  - Multi-AZ Spanning ECS service の AZ Spanning 注釈（§9.7・Check 5c で必須化されたもの。`subnets=[...]` と `desired_count=` を含むテキスト）
- **違反時の対応**: `ECS Cluster (Fargate)` のような italic 注釈テキスト、`<i>` タグを含むセルを削除（上記例外に該当しないもの）

#### Check 7: エッジ色パレット遵守検証

```bash
grep 'edge="1"' <生成ファイル>.drawio | grep -oE 'strokeColor=#[0-9A-Fa-f]+' | sort -u
```

- **期待**: 出力色がすべて承認パレット内：
  - `#0066CC`（青実線: データフロー）
  - `#7AA116`（緑実線: ストレージアクセス）
  - `#e74c3c`（赤実線/破線: CI/CD・image pull）
  - `#666666`（灰破線: 依存・通知）
  - `#C925D1`（紫破線: Aurora replication / CI/CD container）
  - `#8B4513`（茶実線: コンソール/管理アクセス）
- **違反時の対応**: パレット外の色（独自オレンジ、黒、独自紫等）を持つエッジを承認色に変更

#### Check 8: CloudFront origin エッジ生成検証

```bash
# CloudFront Distribution mxCell の id を取得
grep -oE 'id="cf_[^"]+"' <生成ファイル>.drawio

# 各 CloudFront について、source 属性で発信されているエッジ数を取得
grep -E 'edge="1"' <生成ファイル>.drawio | grep -oE 'source="cf_[^"]+"' | sort | uniq -c
```

- **期待**: 各 CloudFront から発信されるエッジ数 = `default_cache_behavior.target_origin_id` 1 個 + `ordered_cache_behavior.target_origin_id` の数
  - 例: `default_cache_behavior` が Firebase Hosting、`ordered_cache_behavior` が ALB と S3 Assets の場合、CloudFront (Public) から 3 本のエッジが発信されている必要がある
- **違反時の対応**:
  - エッジが欠落している origin を特定（Terraform の `origin` ブロックと `<mxCell edge="1" source="cf_*"` を比較）
  - 欠落エッジを生成（例: `<mxCell edge="1" source="cf_public" target="s3_assets" value="" ...>`、ラベルは空文字列）
  - default origin の場合は `strokeWidth=3` を必ず付与（hierarchy を線太さで表現）

#### Check 9: 孤立エッジ & 宙浮きラベルセル & ラベル重複検出

```bash
# (9a) 全エッジから source / target ID を抽出
grep -E 'edge="1"' <生成ファイル>.drawio | grep -oE '(source|target)="[^"]+"' | sort -u

# 全 mxCell の id を抽出
grep -oE '<mxCell id="[^"]+"' <生成ファイル>.drawio | sort -u

# (9b) 宙浮き label cell 検出（whitelist ラベル/path pattern を value に持つが edge="1" が無い全セル）
# style や cell type に依存せず、edge="1" の有無のみで判定（vertex="1"、text セル、style=text;... 全て検出）
grep -E 'value="(RunTask|Blue/Green|Rolling|Canary|Invoke)"' <生成ファイル>.drawio | grep -v 'edge="1"'
grep -E 'value="/[^"]+"' <生成ファイル>.drawio | grep -v 'edge="1"'

# (9c) 同一 whitelist ラベルの重複セル検出（edge と宙浮きラベルが両方存在するケース）
# 同じ value 文字列が複数の mxCell に存在する場合は違反（ラベル位置のズレ・edge 重複・宙浮き残存等を網羅検出）
for label in "RunTask" "Blue/Green" "Rolling" "Canary" "Invoke"; do
  count=$(grep -c "value=\"$label\"" <生成ファイル>.drawio)
  echo "$label: $count"
done

# URL path pattern の重複も検出
grep -oE 'value="/[^"]+"' <生成ファイル>.drawio | sort | uniq -c | awk '$1 > 1'
```

- **期待 (9a)**: エッジの全 source/target ID が、`<mxCell id="...">` で定義されている vertex ID のいずれかに一致
- **期待 (9b)**: ヒットなし（whitelist ラベルテキストは必ず edge="1" のセルに付与されている。`vertex="1"`、text セル等の任意の cell type で edge="1" 以外に値が乗っていないこと）
- **期待 (9c)**: 各 whitelist ラベル文字列の出現回数 = 1（B-1 エッジ集約原則準拠で、同じ操作を表す edge は 1 本のみ。ラベル重複は edge 重複または宙浮きラベル残存のサイン）
- **違反時の対応**:
  - (9a) source/target ID が定義済み ID リストに存在しないエッジ（typo、削除済みノード参照等）を削除
  - (9b) 宙浮きラベルセル（`edge="1"` ではないが whitelist ラベルテキストを持つもの）を削除。元の edge を再生成する必要があれば、source/target ID を指定して `<mxCell ... edge="1" source="..." target="...">` で再作成
  - (9b) 例: `<mxCell value="RunTask" vertex="1">` のような text-only セルが図の左下等に残存していたら削除し、EventBridge Scheduler → ECS Worker の edge 実体（`<mxCell value="RunTask" edge="1" source="eventbridge" target="ecs_worker">`）を生成する
  - (9c) 同一 value が 2 個以上の cell に存在する場合の対応手順:
    1. 全該当 edge cell を抽出し、source ID のアルファベット順で並べる
    2. **先頭 1 本のみ value 維持、残り全てを `value=""` に変更**（edge 自体は削除しない、ラベル文字列だけ消す）
    3. 例外: 宙浮き label cell（`edge="1"` ではない vertex/text セル）は完全削除
  - (9c) 具体例: EventBridge Scheduler から RunTask edge が 2 本（target が ECS Worker と ECS Video Worker）ある場合
    - 1 本目: `<mxCell ... edge="1" source="eventbridge" target="ecs_worker" value="RunTask" ...>` ← value 維持
    - 2 本目: `<mxCell ... edge="1" source="eventbridge" target="ecs_video" value="" ...>` ← value="" に変更（edge は残す）
    - **理由**: 同じ操作（RunTask）を 2 回ラベル表示すると視覚的にラベル重複となる。正規 edge を残しつつラベルだけ重複排除する。
  - (9c) 同様に Blue/Green / Rolling 等の deploy method ラベルも、複数 edge にまたがる場合は 1 本のみラベル付与

#### Check 10: Blue/Green エッジの target 検証

```bash
# Blue/Green ラベル付きエッジの target を抽出
grep -E 'edge="1"' <生成ファイル>.drawio | grep 'value="Blue/Green"' | grep -oE 'target="[^"]+"'

# 同色（赤実線 #e74c3c）の Blue/Green エッジ全件抽出
grep -E 'edge="1"' <生成ファイル>.drawio | grep 'strokeColor=#e74c3c' | grep -v 'dashed=1' | grep -oE 'target="[^"]+"'
```

- **期待**: Blue/Green エッジの target が `deployment_controller.type == "CODE_DEPLOY"` の ECS service のみ。Rolling Update（typeが`"ECS"`または未設定）の Worker / Video Worker / Batch service への接続はゼロ
- **違反時の対応**:
  - Terraform の各 ECS service の `deployment_controller.type` を確認
  - `CODE_DEPLOY` 以外の service への Blue/Green エッジを削除（[layout-algorithm.md §9.8](references/layout-algorithm.md) 参照）

#### Check 11: エッジ集約検証（per-AZ 重複の検出）

```bash
# 同一 source resource type → 同一 target ID の重複 edge 検出
# 例: alb → ecs_api_a と alb → ecs_api_d の 2 本がヒットした場合は B-1 違反
grep 'edge="1"' <生成ファイル>.drawio \
  | grep -oE 'source="[^"]+" target="[^"]+"' \
  | sed -E 's/source="([^"]+)_[a-z]+"/source="\1"/; s/target="([^"]+)_[a-z]+"/target="\1"/' \
  | sort | uniq -c | awk '$1 > 1'
```

- **期待**: ヒットなし（同一 resource type pair の per-AZ 重複なし）
- **違反時の対応**:
  - subnets[0] AZ の 1 本のみ残し、他 AZ ノードからの同種 edge は削除
  - 例: `alb → ecs_api_a` と `alb → ecs_api_d` の 2 本が検出された場合、`alb → ecs_api_a` のみ残し `alb → ecs_api_d` を削除（[drawio-xml-guide.md §B-1 エッジ集約原則](references/drawio-xml-guide.md) 参照）
  - 集約後は `:3000`/`:5432` 等の重複ラベルも自動的に解消される（whitelist 削減で既にこれらのラベル自体が禁止されているため、重複は発生しないはずだが、保険として検証）

#### Check 12: resIcon 命名規則の遵守検証

```bash
# (12a) 派生名の禁止パターン検出（LLM が推測で誤った命名をしていないか）
grep -E 'resIcon=mxgraph\.aws4\.(elastic_container_registry|elastic_container_service|simple_storage_service|simple_queue_service|simple_notification_service|elastic_load_balancer|elastic_load_balancing_v2|relational_database_service|aws_lambda|cloudwatch_logs)' <生成ファイル>.drawio

# (12b) ECR の fillColor が誤って #E7157B (Application Integration ピンク) になっていないか
grep -E 'resIcon=mxgraph\.aws4\.ecr' <生成ファイル>.drawio | grep 'fillColor=#E7157B'
```

- **期待 (12a)**: ヒットなし（aws-resources.md 対応表記載の正規 shape 名のみ使用）
- **期待 (12b)**: ヒットなし（ECR の fillColor は `#ED7100` オレンジ）
- **違反時の対応**:
  - (12a) 派生名を [aws-resources.md §resIcon 命名規則の絶対遵守](references/aws-resources.md) の対応表に従い正規名に修正。例: `elastic_container_registry` → `ecr`
  - (12b) ECR の `fillColor` を `#ED7100` に修正
  - 一般原則: aws-resources.md 対応表の「Style」列をそのままコピーペーストしてフィールド単位で書き直さない

#### 修正後の再実行

12 個の check が全て期待値になるまで上記を繰り返す。**Step 7 へ進む条件**:
- Check 1: ラベル違反なし（改行 + 同一行内括弧書き補足情報の両方ヒット 0）
- Check 2: エッジラベルが全て whitelist 3 カテゴリ内（path pattern / Deploy method / AWS API call name）
- Check 3: 注釈セル数 = 凡例セル数
- Check 4: CI/CD container 存在（CI/CD リソースがある場合）
- Check 5: ECS Multi-AZ Spanning Service 配置（subnets[0] AZ 内 + 注釈）
- Check 6: italic / `<i>` 注釈テキストなし（§9.7 例外を除く）
- Check 7: エッジ色がすべて承認パレット内
- Check 8: CloudFront origin エッジが全 origin に対して生成済み
- Check 9: 孤立エッジなし & 宙浮きラベルセルなし & 同一 whitelist ラベル文字列の出現は各 1 回のみ
- Check 10: Blue/Green エッジの target が CODE_DEPLOY service のみ
- Check 11: 同一 source resource type → 同一 target ID の重複エッジなし（per-AZ 集約済み）
- Check 12: resIcon 命名規則遵守（派生名なし）& ECR fillColor が `#ED7100`

このセルフ検証は **LLM の "解釈" による rule 違反を grep の決定論的判定で機械的に潰す** ためのもの。判断の余地を残さず、機械的に違反を検出 → 修正 → 再検証する。

### Step 7: 出力

`<mxfile>` 形式で `.drawio` ファイルに書き出し → `open` コマンドで開く（macOS では draw.io Desktop が起動する。Desktop 未インストールの環境では [draw.io](https://app.diagrams.net/) にファイルをドラッグ＆ドロップで閲覧可）。

```bash
open {filename}.drawio
```

## 差分レポート生成（オプション機能）

再生成時に前回との変更点を `.md` ファイルとして出力する機能。納品資料・レビュー資料として利用可能。詳細手順・出力フォーマット例は [references/diff-report.md](references/diff-report.md) を参照。
