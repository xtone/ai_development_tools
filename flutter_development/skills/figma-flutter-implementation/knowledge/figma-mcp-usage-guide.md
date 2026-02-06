# Figma MCP Usage Guide

## Overview

Figma MCP (Model Context Protocol) を使用して、FigmaデザインからFlutter実装に必要な情報を取得する方法を説明します。

## MCP Server Setup

Figma公式のMCPサーバーを使用します。2つの接続方法があります。

### 方法1: リモートMCPサーバー（推奨）

Figma公式のリモートMCPサーバーに接続します。

**Claude Code の場合:**

ターミナルで以下のコマンドを実行:

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

実行後、ブラウザでFigmaの認証画面が開きます。認証を完了すると設定が完了します。

**VS Code / Cursor の場合:**

`.vscode/mcp.json` または `~/.cursor/mcp.json` に以下を追加:

```json
{
  "servers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

### 方法2: デスクトップMCPサーバー

Figmaデスクトップアプリを使用してローカルサーバーを起動します。

1. Figmaデスクトップアプリを開く
2. Dev Modeに切り替え
3. 検査パネルで「Enable desktop MCP server」をクリック
4. ローカルサーバーが `http://127.0.0.1:3845/mcp` で起動

**Claude Desktop の場合 (`~/.claude/claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "figma": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

## 公式ドキュメント

詳細は以下の公式ドキュメントを参照:
- [Figma MCP Server Guide](https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server)
- [Figma MCP Server Developer Documentation](https://developers.figma.com/docs/figma-mcp-server)

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

Figma MCPサーバーでは以下のツールが提供されています。

### 1. get_design_context（メイン）

デザインの詳細情報とコード生成を行うメインツール。

**機能:**
- デザイン層の変換機能を提供
- デフォルトはReact + Tailwindだが、フレームワーク指定で他言語にも対応
- 「generate my Figma selection in Flutter」のように指定可能

**返却される情報:**
- **Layout**: Auto Layout設定、方向、配置
- **Size**: 幅、高さ、制約
- **Spacing**: padding、gap（itemSpacing）
- **Colors**: fill、stroke、opacity
- **Typography**: fontFamily、fontSize、fontWeight、lineHeight
- **Effects**: shadow、blur
- **Corner Radius**: 角丸設定

### 2. get_screenshot

選択範囲のスクリーンショットを撮影。レイアウト忠実度向上に推奨。

**用途:**
- デザインの視覚的確認
- レイアウトの全体像把握
- 細かい要素の識別
- 実装結果との比較

### 3. get_metadata

選択範囲の基本プロパティを含む簡略化されたXML表現を返却。

**返却される情報:**
- 層ID
- 名前
- タイプ
- 位置
- サイズ

**用途:** 大規模デザインの処理に有効

### 4. get_variable_defs

Figma選択範囲で使用されている変数とスタイルを返却。

**返却される情報:**
- 色の変数
- スペーシングの変数
- タイポグラフィの変数

**用途:** デザイントークン一覧の取得

### 5. get_code_connect_map / add_code_connect_map

FigmaノードIDとコードコンポーネント間のマッピング管理。

**用途:** 設計とコード実装の連携を強化

### 6. create_design_system_rules

デザインシステムの規則ファイルを生成。

**用途:** エージェントが設計をコード化する際のコンテキスト提供

### 7. その他のツール

- `whoami`: 現在のユーザー情報（リモート専用）
- `get_code_connect_suggestions`: Code Connect提案の取得
- `send_code_connect_mappings`: Code Connectマッピングの送信
- `get_figjam`: FigJam図表の処理
- `generate_diagram`: Mermaid構文からの図生成

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

### MCPサーバーに接続できない

**リモートMCPサーバーの場合:**
1. `claude mcp add` コマンドを再実行
2. ブラウザでFigma認証を完了しているか確認
3. ネットワーク接続を確認

**デスクトップMCPサーバーの場合:**
1. Figmaデスクトップアプリが起動しているか確認
2. Dev Modeが有効か確認
3. 「Enable desktop MCP server」がクリックされているか確認
4. `http://127.0.0.1:3845/mcp` にアクセス可能か確認

### 認証エラー

1. Figmaアカウントへのログイン状態を確認
2. `claude mcp add` コマンドを再実行して再認証
3. ブラウザのCookieをクリアして再試行

### 取得情報が不完全

1. ノードIDが正しいか確認（ハイフン → コロン変換）
2. 対象ノードがFrameまたはComponentか確認
3. Figmaでノードが選択されているか確認

### MCP設定の確認

Claude Codeの場合、以下のコマンドで設定を確認:
```bash
claude mcp list
```

## Reference

- [Figma MCP Server Guide](https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server)
- [Figma MCP Server Developer Documentation](https://developers.figma.com/docs/figma-mcp-server)
- [Model Context Protocol](https://modelcontextprotocol.io/)
