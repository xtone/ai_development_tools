---
name: light-mode-agent
description: "FigmaのLight Modeデザインを解析し、Flutter UIを実装するTeam Agentスキル。Figma MCPでライトテーマのデザイン情報を抽出し、Flutter実装に変換します。FigmaのLight ModeデザインURLが提供された場合に使用してください。"
---

# Light Mode Agent - FigmaライトモードデザインからFlutter実装

## Overview

FigmaのLight Modeデザインを解析し、Flutter UIを実装するTeam Agentスキルです。Figma MCPを活用してライトテーマのデザイン情報を正確に抽出し、忠実なFlutter実装を行います。

**Use this skill when:**
- FigmaのLight ModeデザインURLが提供された場合
- ライトテーマのFlutter UIを実装する必要がある場合
- Light Mode用のThemeData / ColorSchemeを定義する場合
- 既存のFlutterコードをFigmaのLight Modeデザインに合わせて更新する場合

## チーム構成

以下の3人のチームメイトを生成してください：

### 1. Light Design Analyzer
- **役割**: FigmaのLight Modeデザインを解析し、ライトテーマの仕様を整理
- **タスク**:
  - Figma MCPの `get_design_context` でLight Modeデザイン情報を取得
  - `get_screenshot` でライトモードのスクリーンショットを取得し視覚確認
  - `get_variable_defs` でFigma Variableを取得し、デザイントークンとして整理
  - ライトモード固有のカラーパレットを抽出（背景色、サーフェス色、テキスト色、アクセント色）
  - スペーシング、タイポグラフィ、角丸などのデザイントークンを整理
  - コンポーネント構造を分類
  - Figma Variable名とDart定数名の対応表を作成
- **成果物**: Light Modeデザイン仕様書（docs/light_mode_design_spec.md）

### 2. Light Theme Developer
- **役割**: Light Mode用のFlutterテーマ定義とUI実装
- **タスク**:
  - Light Modeデザイン仕様書に基づいてThemeData / ColorScheme.lightを定義
  - Figma Variableに対応するDart定数を定義（ハードコーディング禁止）
  - 各画面のWidgetをLight Modeデザインに合わせて実装
  - 既存のコンポーネントを再利用し、テーマ対応を確認
- **成果物**: Flutterコード（テーマ定義 + 画面実装）

### 3. Light Mode Reviewer
- **役割**: Light Modeの実装品質をレビュー
- **タスク**:
  - FigmaデザインとFlutter実装の一致度を確認
  - ハードコードされた色・値がないか確認（Figma Variable定数を使用しているか）
  - コントラスト比がアクセシビリティ基準を満たしているか確認
  - Dark/Light切り替え時の表示崩れがないか確認
  - エッジケース（長いテキスト、空状態等）の表示を確認
- **成果物**: Light Modeレビューレポート

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
Read light-mode-agent/knowledge/figma-variable-rules.md
```

### Light Mode カラー変換ルール

| Figma HEX | Flutter Color |
|-----------|---------------|
| #RRGGBB | Color(0xFFRRGGBB) |
| 透明度50% #FF0000 | Color(0x80FF0000) |

**ライトモード特有の注意点:**
- 背景色は純白(#FFFFFF)またはオフホワイト(#FAFAFA, #F5F5F5等)を使用
- テキスト色はダークグレー(#212121, #333333等)で十分なコントラストを確保
- サーフェスの階層はシャドウで表現
- アクセント色はライト背景上で視認性を確保できる彩度・明度に調整
- ボーダーやディバイダーは薄いグレー(#E0E0E0, #EEEEEE等)を使用

### ColorScheme.light 設定例

```dart
ColorScheme.light(
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
)
```

## ワークフロー

1. **Light Design Analyzer** がFigmaのLight Modeデザインを解析し、仕様書を作成
2. **Light Theme Developer** が仕様書に基づいてテーマ定義・UI実装
3. **Light Mode Reviewer** が実装をレビューし、Figmaデザインとの一致度を確認
4. 必要に応じて修正・再レビュー

## Resources

### Knowledge Files

- **figma-variable-rules.md**: Figma Variableの取得方法とハードコーディング禁止ルール、OK/NGコード例
