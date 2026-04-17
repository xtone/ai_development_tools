---
name: terraform-architecture-diagram
description: TerraformコードからDraw.io形式（.drawio）のクラウドアーキテクチャ図を自動生成するスキル。AWS、Google Cloudに対応。決定論的レイアウトアルゴリズムにより安定した図を生成。「Terraformからアーキテクチャ図を作成」「インフラ構成図を生成」「.tfファイルから図を作成」「アーキテクチャ図を更新」「インフラ変更の差分レポート」などのリクエスト時に使用。
---

# Terraform Architecture Diagram Generator

Terraform（`.tf`）コードを解析し、決定論的レイアウトで draw.io アーキテクチャ図を生成する。

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
| public | パブリックサブネット | NAT Gateway, IGW, Cloud NAT, Cloud Router |
| alb | VPC直下（AZ横断） | ALB（サブネットに属さず、AZ間の中央に配置） |
| private | プライベートサブネット | EC2, ECS, EKS, Lambda, RDS, Aurora, Cloud Run, GKE, Cloud SQL |
| vpc_endpoint | VPC直下（AZ間集約） | VPC Endpoints（1アイコンに集約、テキストで内訳表示） |
| amplify | VPC外・左上（独立コンテナ） | Amplify（内部にCloudFront + Lambda SSR + S3） |
| managed | VPC外下部 | S3, ECR, Secrets Manager, CloudWatch, Cloud Storage, Pub/Sub |
| side | 右側 | CodePipeline, CodeBuild, Step Functions, Cloud Build |
| skip | 図示省略 | IAMロール/ポリシー, セキュリティグループルール, ルートテーブル, LBリスナー |

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
- **カテゴリ別色分け**: アイコンの `fillColor` でAWSカテゴリを色分け（ネットワーク=#8C4FFF、コンピュート=#ED7100、セキュリティ=#DD344C、ストレージ=#7AA116、DB=#5A30B5）
- **ラベル分離**: アイコンの `value` は空文字列にし、ラベルは別の `text` セルとして下に配置
- **User Traffic**: `shape=mxgraph.aws4.internet` でエントリーポイントを明示（VPC上部中央に配置、上→下フローの起点）
- **エッジ**: `edgeStyle=orthogonalEdgeStyle;rounded=1;` を使用。最終直線セグメント20px以上確保。接続線は色分け（データフロー=#0066CC青、デプロイ=#e74c3c赤、コンソール=#8B4513茶）。ポート番号をラベル付与
- **注釈テキスト**: `fillColor=#ffe6cc` の背景付きテキストセルで補足情報を表示。**ネットワーク/セキュリティ構造のみ記載し、サーバースペック（CPU/Memory/ACU/instance_type/task数/Auto Scaling閾値/バックアップ保持等）は記載しない**（詳細は [layout-algorithm.md §11.4](references/layout-algorithm.md#114-注釈として記載してはいけない内容)）
- **グリッド**: 全座標を10の倍数に配置

AWSリソースマッピング: [references/aws-resources.md](references/aws-resources.md)
GCPリソースマッピング: [references/gcp-resources.md](references/gcp-resources.md)
GCP SVGアイコン: [references/gcp-svg-icons.md](references/gcp-svg-icons.md)
XML生成ルール全体: [references/drawio-xml-guide.md](references/drawio-xml-guide.md)

### Step 7: 出力

`<mxfile>` 形式で `.drawio` ファイルに書き出し → `open` コマンドで開く（macOS では draw.io Desktop が起動する。Desktop 未インストールの環境では [draw.io](https://app.diagrams.net/) にファイルをドラッグ＆ドロップで閲覧可）。

```bash
open {filename}.drawio
```

## 差分レポート生成

再生成時に前回との変更点を `.md` ファイルとして出力する。

### 差分の基準点

| 方式 | コマンド例 | 使用場面 |
|------|-----------|---------|
| デフォルト | `git diff main..HEAD -- '*.tf'` | 開発中のレビュー |
| タグ指定 | `git diff v1.2.0..HEAD -- '*.tf'` | リリース時の納品資料 |
| コミット指定 | `git diff abc1234..HEAD -- '*.tf'` | 柔軟な比較 |

ユーザーが基準を指定しない場合はデフォルト（main ブランチとの差分）を使用する。

### 差分解析手順

1. `git diff` で `.tf` ファイルの差分を取得
2. 差分から追加/削除/変更された resource/module ブロックを抽出
3. 接続関係の変更を特定
4. マークダウン形式でレポート生成

### 出力ファイル

ファイル名: `{diagram-name}-diff.md`

```markdown
# アーキテクチャ変更サマリー

- 基準: main ブランチ (commit: abc1234)
- 現在: feature/xxx ブランチ (commit: def5678)
- 生成日: YYYY-MM-DD

## 追加されたリソース

| リソース | タイプ | 配置先 |
|---------|--------|--------|
| cache | aws_elasticache_cluster | Private Subnet |

## 削除されたリソース

| リソース | タイプ | 元の配置先 |
|---------|--------|-----------|
| old_db | aws_db_instance | Private Subnet |

## 変更されたリソース

| リソース | 属性 | 変更前 | 変更後 |
|---------|------|--------|--------|
| api | desired_count | 2 | 4 |

## 追加された接続

- aws_ecs_service.api → aws_elasticache_cluster.cache

## 削除された接続

- aws_ecs_service.api → aws_db_instance.old_db
```

## 注意事項

- 複雑な構成では主要リソースのみ図示し、IAMロール・ポリシー等は省略
- 同一タイプのリソースが多数ある場合はグループ化して表示
- モジュール内リソースも展開して表示
- XMLコメント内で `--` を使わない（XML仕様違反）
- GCPアイコンは `mxgraph.gcp2.*` ではなく SVG埋め込み形式を使用（Desktop版互換性）
