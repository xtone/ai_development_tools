# FigmaとFlutterでDark Modeの色味が異なる問題と回避方法

## Overview

同じHEX値を指定してもFigmaとFlutterで色味が異なって見えることがあります。Dark Modeでは特にこの差異が目立ちます。以下に主な原因と回避方法を記載します。

## 原因1: Material Design エレベーションオーバーレイ

FlutterのMaterial DesignではDark Mode時にエレベーション（高さ）に応じて**白いオーバーレイが自動的に加算**されます。これによりCard, AppBar, Dialog等がFigmaより明るく表示されます。

**影響を受けるWidget:** Card, AppBar, Dialog, BottomSheet, NavigationBar, Drawer, FloatingActionButton 等

**回避方法:**
```dart
ThemeData.dark().copyWith(
  // Material 3のサーフェスティントを無効化
  colorScheme: ColorScheme.dark(...).copyWith(
    surfaceTint: Colors.transparent,
  ),
  // 個別Widgetのエレベーションオーバーレイも制御
  cardTheme: CardTheme(
    surfaceTintColor: Colors.transparent,
    elevation: 0, // Figmaに合わせてシャドウなしにする場合
  ),
  appBarTheme: AppBarTheme(
    surfaceTintColor: Colors.transparent,
    backgroundColor: AppColors.appBarDark, // 明示的に指定
  ),
  dialogTheme: DialogTheme(
    surfaceTintColor: Colors.transparent,
    backgroundColor: AppColors.dialogDark,
  ),
  bottomSheetTheme: BottomSheetThemeData(
    surfaceTintColor: Colors.transparent,
    backgroundColor: AppColors.bottomSheetDark,
  ),
)
```

## 原因2: カラースペースの違い（sRGB vs Display P3）

FigmaはsRGBで色を定義しますが、iOS/macOSのFlutterは**Display P3**カラースペースでレンダリングするため、特に鮮やかな色（赤、緑、青の高彩度色）で差異が生じます。

**差異が目立つケース:**
- 鮮やかなアクセント色（赤、青、緑系）
- 高彩度のブランドカラー
- ネオン系の色

**回避方法:**
- 実機（iPhone / Android）でFigmaと並べて色味を比較する（シミュレータでは不正確）
- 差異が目立つ場合は、実機で見た目が合うようにHEX値を微調整する
- 微調整した値をコメントで記録する

```dart
// Figma上の値: #3366FF
// 実機で合わせた値: #3060F5（Display P3環境での補正）
static const accentBlue = Color(0xFF3060F5);
```

## 原因3: Material 3 のトーンパレット自動生成

`useMaterial3: true` の場合、primaryやsecondaryからトーンパレットが自動生成され、**指定した色と異なるトーンがWidget各所に適用**されます。

**影響を受けるプロパティ:**
- primaryContainer / onPrimaryContainer
- secondaryContainer / onSecondaryContainer
- tertiaryContainer / onTertiaryContainer
- surfaceVariant / onSurfaceVariant

**回避方法:**

```dart
// 方法1: ColorSchemeの全プロパティを明示的に指定（推奨）
ColorScheme.dark(
  primary: Color(0xFF...),
  onPrimary: Color(0xFF...),
  primaryContainer: Color(0xFF...), // 自動生成させず明示指定
  onPrimaryContainer: Color(0xFF...),
  secondary: Color(0xFF...),
  onSecondary: Color(0xFF...),
  secondaryContainer: Color(0xFF...),
  onSecondaryContainer: Color(0xFF...),
  tertiary: Color(0xFF...),
  onTertiary: Color(0xFF...),
  tertiaryContainer: Color(0xFF...),
  onTertiaryContainer: Color(0xFF...),
  surface: Color(0xFF...),
  onSurface: Color(0xFF...),
  surfaceVariant: Color(0xFF...),
  onSurfaceVariant: Color(0xFF...),
  surfaceTint: Colors.transparent,
  outline: Color(0xFF...),
  outlineVariant: Color(0xFF...),
)

// 方法2: Figmaの色を厳密に再現したい場合はMaterial 2を使用
ThemeData(
  useMaterial3: false,
  brightness: Brightness.dark,
  // ...
)
```

## 原因4: Widgetのデフォルト色・透明度

FlutterのMaterial Widgetは独自のデフォルト色を持っています。`ElevatedButton`, `Card`, `AppBar` 等はテーマ設定と別に内部でデフォルト色を適用する場合があります。

**よくある問題:**
- ElevatedButton の背景色がテーマと異なる
- IconButton の splash/hover 色がデフォルトで付く
- TextField の underline/border 色がデフォルトで付く
- ListTile の selected 色がデフォルトで付く

**回避方法:**

```dart
ThemeData.dark().copyWith(
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: AppColors.buttonBgDark,
      foregroundColor: AppColors.buttonFgDark,
      elevation: 0,
      shadowColor: Colors.transparent,
    ),
  ),
  textButtonTheme: TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: AppColors.textButtonDark,
    ),
  ),
  iconButtonTheme: IconButtonThemeData(
    style: IconButton.styleFrom(
      foregroundColor: AppColors.iconDark,
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    fillColor: AppColors.inputBgDark,
    focusedBorder: OutlineInputBorder(
      borderSide: BorderSide(color: AppColors.inputBorderFocusDark),
    ),
    enabledBorder: OutlineInputBorder(
      borderSide: BorderSide(color: AppColors.inputBorderDark),
    ),
  ),
  cardTheme: CardTheme(
    color: AppColors.cardBgDark,
    surfaceTintColor: Colors.transparent,
  ),
)
```

## 原因5: 半透明色の背景依存ブレンディング

Dark Modeでは半透明色の見た目が背景色に依存して大きく変わります。Figmaのプレビュー背景とFlutterの実際の背景が異なると色味が変わります。

**例:**
- `Color(0x33FFFFFF)` (白 20%透明) → 暗い背景だと薄いグレーに見える
- 同じ色でもFigmaのプレビュー背景と実装の背景色が微妙に違うと見た目が変わる

**回避方法:**
- 半透明色は避け、Figmaで最終的にフラット化された色（背景とブレンド済み）を使用する
- Figmaで色を選択 → 右クリック → 「Flatten」で実際の表示色を確認
- フラット化した色のHEX値をFlutterに使用する

```dart
// NG: 半透明色を使用（背景によって見た目が変わる）
Container(color: Color(0x33FFFFFF))

// OK: フラット化した色を使用（背景に依存しない）
// Figmaで「Flatten」した結果: #383838（背景#1E1E1Eに白20%を重ねた色）
Container(color: AppColors.overlayDark) // Color(0xFF383838)
```

## Dark Mode 色味検証チェックリスト

実装完了後、以下を確認してください：

- [ ] `surfaceTintColor: Colors.transparent` を設定したか
- [ ] ColorSchemeの全プロパティを明示指定したか（自動生成に頼っていないか）
- [ ] Card, AppBar, Dialog等の背景色を個別に明示指定したか
- [ ] ElevatedButton等のデフォルトスタイルをオーバーライドしたか
- [ ] 半透明色をフラット化した値に置き換えたか
- [ ] ハードコードされた色がないか（全てVariable定数を参照しているか）
- [ ] 実機でFigmaと並べて色味を比較したか
- [ ] コントラスト比がWCAG AA基準（4.5:1以上）を満たしているか
