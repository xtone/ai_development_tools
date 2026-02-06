# Figma Variable 活用ルール

## 基本原則

**Figmaで定義されたVariableは必ずDart側でも対応する定数/トークンとして定義し、Widget内でのハードコーディングを禁止する。**

## Figma Variableの取得方法

Figma MCPの `get_variable_defs` を使用して、対象ノードで使用されているVariableを取得します。

```json
{
  "nodeId": "{抽出したnode-id}",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

**返却される情報の例:**
```
{
  "color/background/light": "#FAFAFA",
  "color/surface/light": "#FFFFFF",
  "color/primary": "#6200EE",
  "spacing/sm": "8",
  "spacing/md": "16",
  "typography/body/size": "14"
}
```

## ルール

### 1. Dart定数として定義する

Figma Variableに対応するDart定数を集約ファイルに定義する。

```dart
// lib/ui/theme/app_colors.dart
class AppColors {
  // Light Mode
  static const backgroundLight = Color(0xFFFAFAFA);
  static const surfaceLight = Color(0xFFFFFFFF);
  static const primary = Color(0xFF6200EE);

  // Dark Mode
  static const backgroundDark = Color(0xFF121212);
  static const surfaceDark = Color(0xFF1E1E1E);
}

// lib/ui/theme/app_spacing.dart
class AppSpacing {
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
}

// lib/ui/theme/app_typography.dart
class AppTypography {
  static const bodySize = 14.0;
  static const titleSize = 18.0;
  static const captionSize = 12.0;
}
```

### 2. Widget内でハードコーディングしない

```dart
// NG: ハードコーディング
Container(
  color: Color(0xFFFAFAFA),
  padding: EdgeInsets.all(16),
  child: Text(
    'Hello',
    style: TextStyle(
      fontSize: 14,
      color: Color(0xFF212121),
    ),
  ),
)

// OK: Variable定数を参照
Container(
  color: AppColors.surfaceLight,
  padding: EdgeInsets.all(AppSpacing.md),
  child: Text(
    'Hello',
    style: Theme.of(context).textTheme.bodyMedium,
  ),
)
```

### 3. Theme.of(context) を活用する

テーマ切り替え（Dark/Light）に対応するため、可能な限り `Theme.of(context)` 経由で値を取得する。

```dart
// OK: テーマから取得（Dark/Light自動切り替え対応）
final colorScheme = Theme.of(context).colorScheme;
final textTheme = Theme.of(context).textTheme;

Container(
  color: colorScheme.surface,
  child: Text(
    'Hello',
    style: textTheme.bodyMedium,
  ),
)
```

### 4. 既存の定数定義ファイルを尊重する

プロジェクトに既存の定数定義ファイルがある場合は、そのファイルに追加する。新しいファイルを作成しない。

**確認するファイル:**
- `lib/ui/theme/colors.dart` / `app_colors.dart`
- `lib/ui/theme/theme.dart` / `app_theme.dart`
- `lib/constants/` 配下
- `lib/core/theme/` 配下

### 5. Variable対応表を仕様書に記載する

デザイン仕様書には、Figma Variable名とDart定数名の対応表を必ず記載する。

**対応表テンプレート:**

| Figma Variable名 | Dart定数 | 値 | 用途 |
|------------------|---------|-----|------|
| color/background/light | AppColors.backgroundLight | Color(0xFFFAFAFA) | 画面背景色 |
| color/surface/light | AppColors.surfaceLight | Color(0xFFFFFFFF) | カード背景色 |
| color/primary | AppColors.primary | Color(0xFF6200EE) | プライマリ色 |
| color/on-primary | AppColors.onPrimary | Color(0xFFFFFFFF) | プライマリ上のテキスト色 |
| color/error | AppColors.error | Color(0xFFB00020) | エラー色 |
| spacing/sm | AppSpacing.sm | 8.0 | 小スペーシング |
| spacing/md | AppSpacing.md | 16.0 | 中スペーシング |
| spacing/lg | AppSpacing.lg | 24.0 | 大スペーシング |
| typography/body/size | AppTypography.bodySize | 14.0 | 本文フォントサイズ |

## レビュー時のチェックポイント

- [ ] 全てのFigma VariableがDart定数として定義されているか
- [ ] Widget内に `Color(0xFF...)` のハードコーディングがないか
- [ ] Widget内に数値リテラル（`16.0`, `14` 等）のスペーシング/フォントサイズがないか
- [ ] 定数名がFigma Variable名と対応しているか
- [ ] 既存の定数定義ファイルに追加されているか（新規ファイルを不要に作成していないか）
- [ ] Variable対応表が仕様書に記載されているか
