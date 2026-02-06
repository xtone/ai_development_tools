# Figma MCP Usage Guide

## Overview

Figma MCP (Model Context Protocol) を使用して、FigmaデザインからFlutter実装に必要な情報を取得する方法を説明します。

## MCP Server Setup

### claude_desktop_config.json

Claude DesktopまたはClaude CodeでFigma MCPを使用するには、以下の設定が必要です。

**設定ファイルの場所:**
- macOS: `~/.claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**設定例:**
```json
{
  "mcpServers": {
    "figma-dev-mode-mcp-server": {
      "command": "npx",
      "args": ["-y", "figma-dev-mode-mcp-server"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "figd_xxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

### Figma Access Token の取得

1. Figmaにログイン
2. 右上のプロフィールアイコン → Settings
3. Personal access tokens セクション
4. "Generate new token" をクリック
5. 生成されたトークンをコピー

**注意:** トークンは一度しか表示されません。安全な場所に保存してください。

## URL → node-id 変換

### URL形式

```
https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}&m=dev
```

**例:**
```
https://www.figma.com/design/6nSnL8VRmxHmbMj0nwCUtq/三井のカーシェアーズ_デザイン（LightMode）?node-id=18364-916699&m=dev
```

### node-id抽出

1. URLの `node-id=` パラメータを見つける
2. ハイフン `-` をコロン `:` に変換

**変換例:**
| URL内のnode-id | MCPで使用するnodeId |
|----------------|---------------------|
| 18364-916699 | 18364:916699 |
| 4981-781555 | 4981:781555 |
| 1-2 | 1:2 |

## Available Tools

### 1. get_design_context

デザインの詳細情報を取得するメインツール。

**パラメータ:**
```json
{
  "nodeId": "18364:916699",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

| パラメータ | 必須 | 説明 |
|-----------|------|------|
| nodeId | Yes | FigmaノードID（コロン形式） |
| clientLanguages | No | 対象言語（dart, typescript, swift等） |
| clientFrameworks | No | 対象フレームワーク（flutter, react, swiftui等） |

**返却される情報:**
- **Layout**: Auto Layout設定、方向、配置
- **Size**: 幅、高さ、制約
- **Spacing**: padding、gap（itemSpacing）
- **Colors**: fill、stroke、opacity
- **Typography**: fontFamily、fontSize、fontWeight、lineHeight
- **Effects**: shadow、blur
- **Corner Radius**: 角丸設定

**Flutter/Dart指定の利点:**
- FlutterのWidget構造に近い形式で情報が返される
- Dartの型に合わせた値の形式

### 2. get_screenshot

指定ノードのスクリーンショット画像を取得。

**パラメータ:**
```json
{
  "nodeId": "18364:916699",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

**用途:**
- デザインの視覚的確認
- レイアウトの全体像把握
- 細かい要素の識別
- 実装結果との比較

### 3. get_node

ノードのメタデータを取得。

**パラメータ:**
```json
{
  "nodeId": "18364:916699"
}
```

**返却される情報:**
- ノード名
- ノードタイプ（FRAME, COMPONENT, INSTANCE等）
- 親子関係
- コンポーネントの場合はvariant情報

## Best Practices

### 1. 常に両方のツールを使用

```
1. get_design_context → 詳細なデザイン情報
2. get_screenshot → 視覚的確認
```

両方を使用することで、デザインの意図を正確に把握できます。

### 2. 複数画面の同時取得

複数のFigmaノードがある場合、並列で取得できます：

```
// 並列実行
get_design_context(nodeId: "18364:916699", ...)
get_design_context(nodeId: "4981:781555", ...)
get_screenshot(nodeId: "18364:916699", ...)
get_screenshot(nodeId: "4981:781555", ...)
```

### 3. エラーハンドリング

**よくあるエラーと対処:**

| エラー | 原因 | 対処 |
|--------|------|------|
| Invalid token | トークン無効 | 新しいトークンを生成 |
| Node not found | nodeIdが不正 | URLからnodeIdを再確認 |
| Access denied | 権限不足 | ファイルへのアクセス権を確認 |

### 4. レート制限

Figma APIにはレート制限があります。大量のリクエストを短時間で行わないようにしてください。

## Example Workflow

### Step 1: URLからnode-idを抽出

```
入力URL:
https://www.figma.com/design/6nSnL8VRmxHmbMj0nwCUtq/FileName?node-id=18364-916699&m=dev

抽出結果:
nodeId = "18364:916699"
```

### Step 2: デザイン情報を取得

```json
// get_design_context呼び出し
{
  "nodeId": "18364:916699",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

### Step 3: スクリーンショットを取得

```json
// get_screenshot呼び出し
{
  "nodeId": "18364:916699",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

### Step 4: 取得情報を分析

返却されたデザイン情報から以下を抽出：
- レイアウト構造（Column/Row/Stack）
- スペーシング値（padding、gap）
- カラーコード
- タイポグラフィ設定

### Step 5: Flutter実装に変換

抽出した情報をFlutter Widgetコードに変換

## Troubleshooting

### MCP Serverが起動しない

1. Node.jsがインストールされているか確認
2. npxが使用可能か確認: `npx --version`
3. 設定ファイルのJSON形式が正しいか確認

### トークンエラー

1. トークンの有効期限を確認
2. トークンのスコープを確認（read accessが必要）
3. 新しいトークンを生成して再設定

### 取得情報が不完全

1. ノードIDが正しいか確認
2. 対象ノードがFrameまたはComponentか確認
3. clientLanguages/clientFrameworksを指定してみる

## Reference

- [Figma Dev Mode MCP Server](https://github.com/nicholasoxford/figma-dev-mode-mcp-server)
- [Figma API Documentation](https://www.figma.com/developers/api)
- [Model Context Protocol](https://modelcontextprotocol.io/)
