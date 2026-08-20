# Flutter Color Extraction Guide

## Table of Contents

- [Overview](#overview)
- [HEX → Flutter Color 変換](#hex--flutter-color-変換)
- [透明度 (Opacity) の扱い](#透明度-opacity-の扱い)
- [よく使う色](#よく使う色)
- [FontWeight マッピング](#fontweight-マッピング)
- [グラデーション](#グラデーション)
- [Shadow](#shadow)
- [Border Color](#border-color)
- [Tips](#tips)

## Overview

FigmaデザインからFlutterのColor値への変換ガイドです。

## HEX → Flutter Color 変換

### 基本形式

```
Figma HEX: #RRGGBB
Flutter:   Color(0xFFRRGGBB)
```

**重要:** Flutterの Color は `0x` プレフィックスと透明度（Alpha）値が必要です。

### 変換例

| Figma HEX | Flutter Color |
|-----------|---------------|
| #FFFFFF | Color(0xFFFFFFFF) |
| #000000 | Color(0xFF000000) |
| #e5ecf5 | Color(0xFFE5ECF5) |
| #3366FF | Color(0xFF3366FF) |
| #FF0000 | Color(0xFFFF0000) |

### 変換ルール

1. `#` を `0xFF` に置き換え
2. HEX値を大文字に変換（推奨）
3. `Color()` でラップ

```dart
// 手動変換
final color = Color(0xFFE5ECF5);  // #e5ecf5

// 16進文字列から変換
final hexString = 'e5ecf5';
final color = Color(int.parse('0xFF$hexString'));
```

## 透明度 (Opacity) の扱い

### Figmaでの透明度指定

Figmaでは透明度を以下の形式で指定：
- パーセンテージ: 50%
- 小数: 0.5

### Flutter Alpha値への変換

透明度をHEXの最初の2桁（Alpha値）に変換：

```
Alpha = 透明度 × 255 → 16進数に変換
```

### 透明度対応表

| 透明度 | Alpha (10進) | Alpha (HEX) | 例: #FF0000 |
|--------|--------------|-------------|-------------|
| 100% | 255 | FF | Color(0xFFFF0000) |
| 95% | 242 | F2 | Color(0xF2FF0000) |
| 90% | 230 | E6 | Color(0xE6FF0000) |
| 85% | 217 | D9 | Color(0xD9FF0000) |
| 80% | 204 | CC | Color(0xCCFF0000) |
| 75% | 191 | BF | Color(0xBFFF0000) |
| 70% | 179 | B3 | Color(0xB3FF0000) |
| 65% | 166 | A6 | Color(0xA6FF0000) |
| 60% | 153 | 99 | Color(0x99FF0000) |
| 55% | 140 | 8C | Color(0x8CFF0000) |
| 50% | 128 | 80 | Color(0x80FF0000) |
| 45% | 115 | 73 | Color(0x73FF0000) |
| 40% | 102 | 66 | Color(0x66FF0000) |
| 35% | 89 | 59 | Color(0x59FF0000) |
| 30% | 77 | 4D | Color(0x4DFF0000) |
| 25% | 64 | 40 | Color(0x40FF0000) |
| 20% | 51 | 33 | Color(0x33FF0000) |
| 15% | 38 | 26 | Color(0x26FF0000) |
| 10% | 26 | 1A | Color(0x1AFF0000) |
| 5% | 13 | 0D | Color(0x0DFF0000) |
| 0% | 0 | 00 | Color(0x00FF0000) |

### 計算式

```dart
int alphaFromOpacity(double opacity) {
  return (opacity * 255).round();
}

String alphaHex(double opacity) {
  return alphaFromOpacity(opacity).toRadixString(16).padLeft(2, '0').toUpperCase();
}

// 使用例
// opacity 0.5 → 128 → "80"
// 結果: Color(0x80RRGGBB)
```

## 代替方法: withOpacity()

透明度を後から適用する方法：

```dart
// 方法1: Color.withOpacity()
Color(0xFFFF0000).withOpacity(0.5)

// 方法2: Color.withAlpha()
Color(0xFFFF0000).withAlpha(128)  // 128 = 50%

// 方法3: 直接Alpha値を指定
Color(0x80FF0000)  // 0x80 = 128 = 50%
```

**推奨:** パフォーマンスの観点から、可能な限り直接Alpha値を指定する方が効率的です。

## よく使う色

### 標準カラー

```dart
// 白/黒
Colors.white       // Color(0xFFFFFFFF)
Colors.black       // Color(0xFF000000)
Colors.transparent // Color(0x00000000)

// グレースケール
Colors.grey        // Color(0xFF9E9E9E)
Colors.grey[100]   // Color(0xFFF5F5F5)
Colors.grey[200]   // Color(0xFFEEEEEE)
Colors.grey[300]   // Color(0xFFE0E0E0)
Colors.grey[400]   // Color(0xFFBDBDBD)
Colors.grey[500]   // Color(0xFF9E9E9E)
Colors.grey[600]   // Color(0xFF757575)
Colors.grey[700]   // Color(0xFF616161)
Colors.grey[800]   // Color(0xFF424242)
Colors.grey[900]   // Color(0xFF212121)
```

### プロジェクト定義色

多くのFlutterプロジェクトでは、アプリ固有の色を定義しています：

```dart
// lib/ui/theme/colors.dart などを確認
class AppColors {
  static const primary = Color(0xFF3366FF);
  static const secondary = Color(0xFF6C757D);
  static const error = Color(0xFFDC3545);
  static const success = Color(0xFF28A745);
  static const warning = Color(0xFFFFC107);
  static const info = Color(0xFF17A2B8);

  static const background = Color(0xFFF5F5F5);
  static const surface = Color(0xFFFFFFFF);
  static const textPrimary = Color(0xFF212121);
  static const textSecondary = Color(0xFF757575);
}
```

**ベストプラクティス:** プロジェクトに定義済みの色がある場合は、直接HEX値ではなく定義済み定数を使用してください。

## FontWeight マッピング

Figmaのfont-weightをFlutterに変換：

| Figma fontWeight | Flutter FontWeight |
|------------------|-------------------|
| 100 (Thin) | FontWeight.w100 |
| 200 (Extra Light) | FontWeight.w200 |
| 300 (Light) | FontWeight.w300 |
| 400 (Regular) | FontWeight.w400 / FontWeight.normal |
| 500 (Medium) | FontWeight.w500 |
| 600 (Semi Bold) | FontWeight.w600 |
| 700 (Bold) | FontWeight.w700 / FontWeight.bold |
| 800 (Extra Bold) | FontWeight.w800 |
| 900 (Black) | FontWeight.w900 |

### 使用例

```dart
Text(
  'Sample Text',
  style: TextStyle(
    color: Color(0xFF212121),
    fontSize: 16,
    fontWeight: FontWeight.w600,  // Semi Bold
  ),
)
```

## グラデーション

### Linear Gradient

**Figma:**
```
Linear Gradient
- From: #FF0000 (0%)
- To: #0000FF (100%)
- Angle: 90°
```

**Flutter:**
```dart
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [
        Color(0xFFFF0000),
        Color(0xFF0000FF),
      ],
    ),
  ),
)
```

### Radial Gradient

**Figma:**
```
Radial Gradient
- Center: #FF0000
- Edge: #0000FF
```

**Flutter:**
```dart
Container(
  decoration: BoxDecoration(
    gradient: RadialGradient(
      colors: [
        Color(0xFFFF0000),
        Color(0xFF0000FF),
      ],
    ),
  ),
)
```

## Shadow

**Figma:**
```
Drop Shadow
- Color: #000000
- Opacity: 10%
- X: 0, Y: 2
- Blur: 4
```

**Flutter:**
```dart
Container(
  decoration: BoxDecoration(
    boxShadow: [
      BoxShadow(
        color: Color(0x1A000000),  // 10% opacity
        offset: Offset(0, 2),
        blurRadius: 4,
      ),
    ],
  ),
)
```

## Border Color

**Figma:**
```
Stroke
- Color: #E0E0E0
- Width: 1
```

**Flutter:**
```dart
Container(
  decoration: BoxDecoration(
    border: Border.all(
      color: Color(0xFFE0E0E0),
      width: 1,
    ),
  ),
)
```

## Tips

1. **大文字統一:** HEX値は大文字で統一すると可読性が向上
2. **定義済み色を優先:** プロジェクト内の色定義を確認して使用
3. **透明度は事前計算:** withOpacity()より直接Alpha値を指定
4. **命名規則:** 用途がわかる名前で色を定義（primary, error等）
5. **ダークモード対応:** 必要に応じてテーマで色を切り替え
