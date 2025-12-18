# テーマ・デザインコンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| Liquid Glass | 26+ | 26+ | 26+ | iOS 7以来最大のUI刷新 |
| .liquidGlass() | 26+ | 26+ | 26+ | Liquid Glassエフェクト |
| .depthLayer() | 26+ | 26+ | 26+ | 深度レイヤー設定 |
| .adaptiveTint() | 26+ | 26+ | 26+ | 適応型ティント |

---

## Liquid Glass (iOS 26+)

iOS 7以来最大のUI刷新。visionOSにインスパイアされた半透明・ガラス風デザイン。

### 概要

- 光、コンテンツ、入力に反応する動的なUI要素
- 標準UIKit/SwiftUIコンポーネントは自動的に新デザインに適用
- カスタムUIは調整が必要な場合あり

### 基本的な使用法

```swift
// Liquid Glass エフェクトの適用
View()
    .liquidGlass(.prominent)
    .depthLayer(.background)
    .adaptiveTint(.system)
```

### スタイルオプション

```swift
// 目立つスタイル
.liquidGlass(.prominent)

// 控えめなスタイル
.liquidGlass(.subtle)

// カスタムティント
.liquidGlass(.prominent)
    .tint(.blue)
```

### 深度レイヤー

```swift
// 背景レイヤー
.depthLayer(.background)

// 前面レイヤー
.depthLayer(.foreground)

// オーバーレイレイヤー
.depthLayer(.overlay)
```

---

## 移行オプション

### 猶予期間

- Xcode 26では1年間の猶予期間あり
- Liquid Glassを無効化して従来UIを維持可能
- 段階的な移行を推奨

### 無効化方法

```swift
// Info.plistで設定
// UIDisableLiquidGlass = YES
```

---

## デザインガイドライン

### 推奨事項

- 全面画像背景の活用を推奨
- コンテンツの読みやすさを確保
- 既存のブラー効果との競合に注意

### 注意点

- カスタムビューの透明度やブラー効果を見直す必要がある可能性
- 既存のカスタムUIがLiquid Glassと調和するか確認
- ダークモード・ライトモード両方でテスト

### 自動適用されるコンポーネント

以下の標準コンポーネントは自動的にLiquid Glassスタイルが適用されます：

- NavigationBar
- TabBar
- ToolBar
- Alert
- ActionSheet
- Sheets

---

## 後方互換性

```swift
var body: some View {
    if #available(iOS 26.0, *) {
        content
            .liquidGlass(.prominent)
    } else {
        content
            .background(.ultraThinMaterial)
    }
}
```

---

## 関連ドキュメント

- [What's new in SwiftUI - WWDC25](https://developer.apple.com/videos/play/wwdc2025/)
- [Human Interface Guidelines - Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
