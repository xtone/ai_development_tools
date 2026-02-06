# Figma Flutter Implementation Skill

Figma MCPを使用してFigmaデザインからFlutter UIの実装計画を生成するスキルです。

## 概要

このスキルは、FigmaのURLを受け取り、MCP (Model Context Protocol) を使用してデザイン情報を自動取得し、Flutterコードへの実装計画を生成します。

## 主な機能

- **デザイン情報の自動取得**: Figma MCPを使用してレイアウト、色、タイポグラフィを取得
- **Flutter変換ガイド**: Figmaプロパティを正確にFlutter Widgetに変換
- **実装計画書の生成**: 構造化された実装計画書を自動生成
- **視覚的確認**: スクリーンショット取得による視覚的なデザイン確認

## クイックスタート

### 1. 基本的な使い方

FigmaのURLを指定してスキルを呼び出します：

```
以下のFigmaデザインに基づいてFlutter実装計画を作成してください。

https://www.figma.com/design/xxxxx/FileName?node-id=123-456&m=dev
```

### 2. 既存ファイルの更新

既存のFlutterファイルをFigmaデザインに合わせて更新：

```
lib/ui/screens/home_page.dart のデザインを以下のFigmaに合わせて更新してください。

https://www.figma.com/design/xxxxx/FileName?node-id=123-456&m=dev

変更内容:
- ヘッダーのデザイン更新
- ボタンスタイルの変更
```

### 3. 複数状態のデザイン

複数の状態（初期/完了等）がある場合：

```
以下の2つのFigmaデザインを参考に実装計画を作成してください。

初期状態:
https://www.figma.com/design/xxxxx/FileName?node-id=123-456&m=dev

完了状態:
https://www.figma.com/design/xxxxx/FileName?node-id=789-012&m=dev
```

## 環境設定

### Figma MCP Server の設定

このスキルを使用するには、Figma公式MCPサーバーの設定が必要です。

#### 方法1: リモートMCPサーバー（推奨）

**Claude Code の場合:**

ターミナルで以下のコマンドを実行:

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

ブラウザでFigma認証画面が開くので、認証を完了してください。

設定確認:
```bash
claude mcp list
```

#### 方法2: デスクトップMCPサーバー

1. Figmaデスクトップアプリを開く
2. Dev Modeに切り替え
3. 検査パネルで「Enable desktop MCP server」をクリック
4. ローカルサーバーが `http://127.0.0.1:3845/mcp` で起動

**Claude Desktop設定 (`~/.claude/claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "figma": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

#### 公式ドキュメント

- [Figma MCP Server Guide](https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server)
- [Figma MCP Developer Docs](https://developers.figma.com/docs/figma-mcp-server)

## スキルのワークフロー

```
1. Figma URL解析
   └─ node-idを抽出

2. デザイン情報取得
   ├─ get_design_context → レイアウト/色/タイポグラフィ
   └─ get_screenshot → 視覚的確認用画像

3. 既存コード確認
   └─ 対象ファイルの現状を把握

4. デザイン→Flutter変換
   ├─ Auto Layout → Column/Row/Stack
   ├─ Colors → Color(0xFFRRGGBB)
   └─ Typography → TextStyle

5. 実装計画書生成
   └─ templates/implementation-plan.md を使用

6. ユーザー確認
   └─ 計画の承認を得る

7. 実装開始
   └─ 承認後にコードを実装
```

## ファイル構成

```
figma-flutter-implementation/
├── SKILL.md                           # メインスキル定義
├── README.md                          # このファイル
├── knowledge/
│   ├── figma-mcp-usage-guide.md      # Figma MCPツールの使い方
│   ├── flutter-layout-mapping.md     # レイアウト変換ガイド
│   ├── flutter-color-extraction.md   # カラー変換ガイド
│   └── figma_mcp_sample_log.md       # 実際のワークフロー例
└── templates/
    └── implementation-plan.md         # 実装計画書テンプレート
```

## ナレッジファイル

### figma-mcp-usage-guide.md

- MCP Server設定方法
- get_design_context / get_screenshot の使い方
- URL → node-id 変換方法
- トラブルシューティング

### flutter-layout-mapping.md

- Auto Layout → Column/Row/Stack マッピング
- MainAxisAlignment/CrossAxisAlignment 対応
- padding/gap → EdgeInsets/SizedBox 変換
- サイズ制約の変換

### flutter-color-extraction.md

- HEX → Color(0xFFRRGGBB) 変換
- 透明度計算（Alpha値）
- FontWeight マッピング
- グラデーション/シャドウ変換

### figma_mcp_sample_log.md

- 実際のワークフロー例
- ツール呼び出しサンプル
- 生成された実装計画の例

## トラブルシューティング

### Figma MCPツールが見つからない

**対処:**
1. `claude mcp add --transport http figma https://mcp.figma.com/mcp` を実行
2. ブラウザでFigma認証を完了
3. `claude mcp list` で設定を確認

### デザイン情報が取得できない

**対処:**
1. Figma認証が完了しているか確認
2. node-idの形式確認（ハイフン → コロン）
3. ファイルへのアクセス権限を確認

### 色が正しくない

**対処:**
1. 大文字/小文字を確認
2. `0xFF` プレフィックスがあるか確認
3. 透明度の計算を確認

## 関連スキル

- **flutter-widget-assistant**: Widget実装のアーキテクチャ決定を支援
- **figma-design-analyzer** (Next.js版): Next.js/React向けのFigmaデザイン分析

## 参考リンク

- [Figma MCP Server Guide](https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server)
- [Figma MCP Developer Docs](https://developers.figma.com/docs/figma-mcp-server)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Flutter Documentation](https://flutter.dev/docs)
