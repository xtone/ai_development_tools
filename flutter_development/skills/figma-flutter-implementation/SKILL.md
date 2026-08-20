---
name: figma-flutter-implementation
description: "Extracts design specifications from Figma using MCP and generates Flutter implementation plans. Use when you have Figma URLs and need to implement Flutter UI with accurate colors, spacing, and layout from Figma designs."
---

# Figma Flutter Implementation

## Overview

Figma MCPを使用してFigmaデザインからFlutter UIの実装計画を生成するスキル。デザイン情報（レイアウト、色、タイポグラフィ、スペーシング）を正確に抽出し、Flutter実装に変換します。

**Use this skill when:**
- FigmaのURLが提供され、Flutter UIを実装する必要がある
- デザイン通りの正確な色・スペーシング・レイアウトを再現したい
- Figmaデザインを分析して実装計画を立てる必要がある
- 既存のFlutterコードをFigmaデザインに合わせて更新する

## Core Workflow

### Step 1: Figma URL解析・node-id抽出

FigmaのURLからnode-idを抽出します。

```
URL形式: https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}&m=dev
node-id変換: 18364-916699 → 18364:916699 (ハイフンをコロンに変換)
```

**複数のURLが提供された場合:**
- 各URLからnode-idを抽出
- 画面の状態やバリアントを識別（例: 開錠前、開錠後）

### Step 2: get_design_context でデザイン情報取得

Figma MCPの `get_design_context` ツールを使用してデザイン情報を取得します。

```json
{
  "nodeId": "18364:916699",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

**取得できる情報:**
- レイアウト情報（Auto Layout、配置、サイズ）
- スペーシング（padding、gap、margin）
- 色情報（背景色、テキスト色、HEXコード）
- タイポグラフィ（フォントサイズ、ウェイト、行間）
- コンポーネント構造（親子関係）

### Step 3: get_screenshot で視覚確認

`get_screenshot` ツールでスクリーンショットを取得し、視覚的にデザインを確認します。

```json
{
  "nodeId": "18364:916699",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

**目的:**
- デザインの全体像を把握
- コンポーネントの配置を視覚的に確認
- 詳細な要素を識別

### Step 4: 既存コード確認

対象となるFlutterファイルを読み込み、現在の実装を把握します。

**確認ポイント:**
- 既存のWidget構造
- 状態管理の方法（useState、Riverpod等）
- 使用しているコンポーネント
- スタイリングの方法

### Step 5: デザイン→Flutter変換

取得したデザイン情報をFlutterのコードに変換します。

**レイアウト変換ガイド:**
```
Read figma-flutter-implementation/knowledge/flutter-layout-mapping.md
```

**カラー変換ガイド:**
```
Read figma-flutter-implementation/knowledge/flutter-color-extraction.md
```

**主要な変換ルール:**

| Figma | Flutter |
|-------|---------|
| Auto Layout (vertical) | Column |
| Auto Layout (horizontal) | Row |
| Frame with overlap | Stack |
| padding | EdgeInsets |
| gap | SizedBox or mainAxisAlignment |
| fill: #RRGGBB | Color(0xFFRRGGBB) |
| fontSize: 14 | fontSize: 14 |
| fontWeight: 600 | FontWeight.w600 |

### Step 6: 実装計画書生成

テンプレートを使用して実装計画書を作成します。

```
Read figma-flutter-implementation/templates/implementation-plan.md
```

**計画書に含める内容:**
1. 概要（変更の目的と範囲）
2. Figmaデザイン情報（URL、node-id、スクリーンショット）
3. 抽出したプロパティ（レイアウト、スペーシング、カラー、タイポグラフィ）
4. Flutter実装マッピング
5. 具体的な変更内容
6. 変更ファイル一覧

### Step 7: ユーザー確認

生成した実装計画をユーザーに提示し、承認を得ます。

**確認ポイント:**
- デザインの解釈が正しいか
- 実装方針に問題がないか
- 追加の要件や制約がないか

## Figma MCP Tools Reference

### get_design_context

デザインの詳細情報を取得するメインツール。

**パラメータ:**
| パラメータ | 説明 | 例 |
|-----------|------|-----|
| nodeId | FigmaのノードID | "18364:916699" |
| clientLanguages | 対象言語 | "dart" |
| clientFrameworks | 対象フレームワーク | "flutter" |

**返却される情報:**
- コンポーネント階層構造
- Auto Layoutプロパティ
- サイズと位置
- 色とグラデーション
- タイポグラフィスタイル
- 角丸やシャドウ

### get_screenshot

指定ノードのスクリーンショットを取得。

**パラメータ:**
| パラメータ | 説明 | 例 |
|-----------|------|-----|
| nodeId | FigmaのノードID | "18364:916699" |
| clientLanguages | 対象言語 | "dart" |
| clientFrameworks | 対象フレームワーク | "flutter" |

### get_metadata

ノードの基本プロパティ（ID、名前、タイプ、位置、サイズ）を含む簡略化されたXML表現を取得。大規模デザインの処理に有効。

### get_variable_defs

Figma選択範囲で使用されている変数とスタイル（色、スペーシング、タイポグラフィ）を取得。デザイントークンの抽出に有効。

## Flutter Mapping Guide

### レイアウト変換

| Figma Auto Layout | Flutter Widget |
|-------------------|----------------|
| direction: vertical | Column |
| direction: horizontal | Row |
| primaryAxisAlignment: center | mainAxisAlignment: MainAxisAlignment.center |
| primaryAxisAlignment: space-between | mainAxisAlignment: MainAxisAlignment.spaceBetween |
| counterAxisAlignment: center | crossAxisAlignment: CrossAxisAlignment.center |
| counterAxisAlignment: stretch | crossAxisAlignment: CrossAxisAlignment.stretch |
| layoutWrap: wrap | Wrap |

### スペーシング変換

| Figma | Flutter |
|-------|---------|
| padding: 16 | padding: EdgeInsets.all(16) |
| paddingTop: 8, paddingBottom: 16 | padding: EdgeInsets.only(top: 8, bottom: 16) |
| paddingHorizontal: 16, paddingVertical: 8 | padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8) |
| itemSpacing: 8 (gap) | SizedBox(height: 8) または mainAxisAlignment |

### カラー変換

| Figma HEX | Flutter Color |
|-----------|---------------|
| #FFFFFF | Color(0xFFFFFFFF) または Colors.white |
| #000000 | Color(0xFF000000) または Colors.black |
| #e5ecf5 | Color(0xFFE5ECF5) |
| #ff0000 (50%透明) | Color(0x80FF0000) |

**透明度対応表:**
| 透明度 | HEX prefix |
|--------|------------|
| 100% | FF |
| 90% | E6 |
| 80% | CC |
| 70% | B3 |
| 60% | 99 |
| 50% | 80 |
| 40% | 66 |
| 30% | 4D |
| 20% | 33 |
| 10% | 1A |
| 0% | 00 |

### タイポグラフィ変換

| Figma | Flutter |
|-------|---------|
| fontSize: 14 | fontSize: 14 |
| fontWeight: 400 | fontWeight: FontWeight.w400 (normal) |
| fontWeight: 500 | fontWeight: FontWeight.w500 (medium) |
| fontWeight: 600 | fontWeight: FontWeight.w600 (semiBold) |
| fontWeight: 700 | fontWeight: FontWeight.w700 (bold) |
| lineHeight: 1.5 | height: 1.5 |
| letterSpacing: 0.5 | letterSpacing: 0.5 |

### 角丸変換

| Figma | Flutter |
|-------|---------|
| cornerRadius: 8 | borderRadius: BorderRadius.circular(8) |
| topLeftRadius: 8, topRightRadius: 8 | borderRadius: BorderRadius.only(topLeft: Radius.circular(8), topRight: Radius.circular(8)) |

## Best Practices

### 1. 常にスクリーンショットで視覚確認

`get_design_context` だけでなく、`get_screenshot` も取得して視覚的に確認することで、デザインの意図を正確に把握できます。

### 2. 既存コードのパターンを尊重

新しいコードを追加する際は、既存のコードベースのパターン（状態管理、Widget構造、命名規則）に従います。

### 3. 正確な色コードを使用

Figmaから取得した色コード（HEX）を正確にFlutterの `Color` に変換します。近似色ではなく、正確な値を使用してください。

### 4. スペーシングの一貫性

プロジェクトに定義済みのスペーシング定数がある場合はそれを使用し、なければFigmaの値を正確に反映します。

### 5. コンポーネントの再利用

プロジェクト内に既存の類似コンポーネントがある場合は、新規作成せずに再利用することを検討します。

### 6. 実装前に計画を確認

コードを書き始める前に、必ず実装計画をユーザーに確認してもらい、認識のズレを防ぎます。

## Common Patterns

### チェックボックスリスト

```dart
Column(
  children: [
    CheckboxListTile(
      value: isChecked,
      onChanged: (value) => setState(() => isChecked = value ?? false),
      title: Text('チェック項目'),
      controlAffinity: ListTileControlAffinity.leading,
    ),
    // ...
  ],
)
```

### アコーディオン（折りたたみ）

```dart
ExpansionTile(
  title: Text('タイトル'),
  initiallyExpanded: false,
  children: [
    // 展開時のコンテンツ
  ],
)
```

### 背景色付きコンテナ

```dart
Container(
  padding: EdgeInsets.all(16),
  decoration: BoxDecoration(
    color: Color(0xFFE5ECF5),
    borderRadius: BorderRadius.circular(8),
  ),
  child: // ...
)
```

### ボタン活性化条件

```dart
ElevatedButton(
  onPressed: (check1 && check2 && check3) ? () {
    // ボタン押下時の処理
  } : null, // 非活性時はnull
  child: Text('ボタンテキスト'),
)
```

## Resources

### Knowledge Files

- **figma-mcp-usage-guide.md**: Figma MCPツールの詳細な使い方
- **flutter-layout-mapping.md**: Figma Auto Layout → Flutter Widget変換ガイド
- **flutter-color-extraction.md**: 色・透明度の変換ガイド
- **figma_mcp_sample_log.md**: 実際のワークフロー例

### Templates

- **implementation-plan.md**: 実装計画書テンプレート

## Example Usage

### ユーザーのプロンプト例

```
以下のFigmaデザインに基づいて、use_start_preparation_page.dartを更新してください。

C4_01-01.利用開始_開錠前
https://www.figma.com/design/6nSnL8VRmxHmbMj0nwCUtq/三井のカーシェアーズ_デザイン（LightMode）?node-id=18364-916699&m=dev

変更内容:
- チェックボックスセクションを追加
- ボタン活性化条件をチェックボックス全チェックに変更
```

### 期待される流れ

1. FigmaのURLからnode-idを抽出
2. `get_design_context` でデザイン情報取得
3. `get_screenshot` で視覚確認
4. 既存コードを確認
5. 実装計画を生成
6. ユーザー確認後、実装を開始

## Troubleshooting

### Figma MCPツールが見つからない

**Claude Codeの場合:**

ターミナルで以下のコマンドを実行してFigma MCPを追加:
```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

設定確認:
```bash
claude mcp list
```

**デスクトップMCPサーバーの場合:**
1. Figmaデスクトップアプリを起動
2. Dev Modeに切り替え
3. 「Enable desktop MCP server」をクリック
4. `http://127.0.0.1:3845/mcp` でサーバーが起動

### デザイン情報が取得できない

- Figma認証が完了しているか確認
- node-idの形式が正しいか確認（ハイフン → コロン）
- 対象ノードへのアクセス権限があるか確認

### 色が正しく反映されない

- HEXコードの大文字/小文字を確認
- 透明度の計算が正しいか確認
- `0x` プレフィックスが付いているか確認

### 詳細な設定方法

詳しくは公式ドキュメントを参照:
- [Figma MCP Server Guide](https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server)
- [Figma MCP Developer Docs](https://developers.figma.com/docs/figma-mcp-server)
