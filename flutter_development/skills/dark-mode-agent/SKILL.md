---
name: dark-mode-agent
description: "FigmaのDark Modeデザインを解析し、Flutter UIを実装するTeam Agentスキル。Figma MCPでダークテーマのデザイン情報を抽出し、色味差異の回避策を適用してFlutter実装に変換します。FigmaのDark ModeデザインURLが提供された場合に使用してください。"
---

# Dark Mode Agent - FigmaダークモードデザインからFlutter実装

## Overview

FigmaのDark Modeデザインを解析し、Flutter UIを実装するTeam Agentスキルです。Figma MCPを活用してダークテーマのデザイン情報を正確に抽出し、FigmaとFlutter間の色味差異を回避しながら忠実な実装を行います。

**Use this skill when:**
- FigmaのDark ModeデザインURLが提供された場合
- ダークテーマのFlutter UIを実装する必要がある場合
- FigmaとFlutterでDark Modeの色味が合わない問題を解決したい場合
- Dark Mode用のThemeData / ColorSchemeを定義する場合

## チーム構成

以下の3人のチームメイトを生成してください：

### 1. Dark Design Analyzer
- **役割**: FigmaのDark Modeデザインを解析し、ダークテーマの仕様を整理
- **タスク**:
  - Figma MCPの `get_design_context` でDark Modeデザイン情報を取得
  - `get_screenshot` でダークモードのスクリーンショットを取得し視覚確認
  - `get_variable_defs` でFigma Variableを取得し、デザイントークンとして整理
  - ダークモード固有のカラーパレットを抽出（背景色、サーフェス色、テキスト色、アクセント色）
  - スペーシング、タイポグラフィ、角丸などのデザイントークンを整理
  - コンポーネント構造を分類
  - Figma Variable名とDart定数名の対応表を作成
- **成果物**: Dark Modeデザイン仕様書（docs/dark_mode_design_spec.md）

### 2. Dark Theme Developer
- **役割**: Dark Mode用のFlutterテーマ定義とUI実装
- **タスク**:
  - Dark Modeデザイン仕様書に基づいてThemeData / ColorScheme.darkを定義
  - Figma Variableに対応するDart定数を定義（ハードコーディング禁止）
  - 色味差異の回避策を適用（knowledge/dark-mode-color-discrepancy.md参照）
  - 各画面のWidgetをDark Modeデザインに合わせて実装
  - 既存のコンポーネントを再利用し、テーマ対応を確認
- **成果物**: Flutterコード（テーマ定義 + 画面実装）

### 3. Dark Mode Reviewer
- **役割**: Dark Modeの実装品質をレビュー
- **タスク**:
  - FigmaデザインとFlutter実装の一致度を確認
  - ハードコードされた色・値がないか確認（Figma Variable定数を使用しているか）
  - 色味差異チェックリスト（knowledge/dark-mode-color-discrepancy.md）に基づく検証
  - コントラスト比がアクセシビリティ基準を満たしているか確認
  - Dark/Light切り替え時の表示崩れがないか確認
  - エッジケース（長いテキスト、空状態等）の表示を確認
- **成果物**: Dark Modeレビューレポート

## Figma MCP活用ガイド

### node-id抽出ルール
```
URL: https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}&m=dev
変換: 18364-916699 → 18364:916699 (ハイフンをコロンに変換)
```

### get_design_context パラメータ
```json
{
  "nodeId": "{抽出したnode-id}",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

### Figma Variable の活用（必須ルール）

**`get_variable_defs` で変数定義を取得し、ハードコーディングを禁止する。**

```
Read dark-mode-agent/knowledge/figma-variable-rules.md
```

### Dark Mode カラー変換ルール

| Figma HEX | Flutter Color |
|-----------|---------------|
| #RRGGBB | Color(0xFFRRGGBB) |
| 透明度50% #FF0000 | Color(0x80FF0000) |

**ダークモード特有の注意点:**
- 背景色は純黒(#000000)を避け、ダークグレー(#121212, #1E1E1E等)を推奨
- テキスト色は純白(#FFFFFF)を避け、少し抑えた白(#E0E0E0, #F5F5F5等)を推奨
- サーフェスの階層はエレベーションで表現（暗い→明るい）
- アクセント色は明るめに調整して視認性を確保

### FigmaとFlutterの色味差異の回避方法

Dark Modeでは同じHEX値でもFigmaとFlutterで色味が異なることがあります。原因と回避方法の詳細:

```
Read dark-mode-agent/knowledge/dark-mode-color-discrepancy.md
```

### ColorScheme.dark 設定例

```dart
ColorScheme.dark(
  primary: Color(0xFF{primary}),
  secondary: Color(0xFF{secondary}),
  surface: Color(0xFF{surface}),
  background: Color(0xFF{background}),
  error: Color(0xFF{error}),
  onPrimary: Color(0xFF{onPrimary}),
  onSecondary: Color(0xFF{onSecondary}),
  onSurface: Color(0xFF{onSurface}),
  onBackground: Color(0xFF{onBackground}),
  onError: Color(0xFF{onError}),
  // Material 3 自動生成を防ぐため、Container系も明示指定
  primaryContainer: Color(0xFF{primaryContainer}),
  onPrimaryContainer: Color(0xFF{onPrimaryContainer}),
  secondaryContainer: Color(0xFF{secondaryContainer}),
  onSecondaryContainer: Color(0xFF{onSecondaryContainer}),
  surfaceTint: Colors.transparent, // エレベーションオーバーレイ無効化
)
```

## ワークフロー

1. **Dark Design Analyzer** がFigmaのDark Modeデザインを解析し、仕様書を作成
2. **Dark Theme Developer** が仕様書に基づいてテーマ定義・UI実装
3. **Dark Mode Reviewer** が実装をレビューし、Figmaデザインとの一致度を確認
4. 必要に応じて修正・再レビュー

## Resources

### Knowledge Files

- **dark-mode-color-discrepancy.md**: FigmaとFlutterでDark Modeの色味が異なる5つの原因と具体的な回避方法、検証チェックリスト
- **figma-variable-rules.md**: Figma Variableの取得方法とハードコーディング禁止ルール、OK/NGコード例
