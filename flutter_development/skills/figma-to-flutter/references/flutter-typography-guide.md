# Flutter Typography Guide

This guide provides methods for extracting typography from Figma and converting to Flutter TextStyle.

## TextStyle Mapping

### Basic Figma to Flutter Conversion

| Figma Property | Flutter TextStyle Property |
|----------------|---------------------------|
| Font family | `fontFamily` |
| Font size | `fontSize` |
| Font weight | `fontWeight` |
| Line height (%) | `height` (ratio) |
| Letter spacing | `letterSpacing` |
| Color | `color` |
| Text decoration | `decoration` |
| Text case | (handled separately) |

### Complete TextStyle Example

**Figma shows:**
```
Font: Roboto
Size: 16px
Weight: Semi Bold (600)
Line height: 150%
Letter spacing: 0.5px
Color: #1A1A1A
```

**Flutter conversion:**
```dart
TextStyle(
  fontFamily: 'Roboto',
  fontSize: 16,
  fontWeight: FontWeight.w600,
  height: 1.5, // 150% / 100
  letterSpacing: 0.5,
  color: Color(0xFF1A1A1A),
)
```

## Font Weight Mapping

| Figma Weight | Flutter FontWeight |
|--------------|-------------------|
| Thin (100) | `FontWeight.w100` |
| Extra Light (200) | `FontWeight.w200` |
| Light (300) | `FontWeight.w300` |
| Regular (400) | `FontWeight.w400` or `FontWeight.normal` |
| Medium (500) | `FontWeight.w500` |
| Semi Bold (600) | `FontWeight.w600` |
| Bold (700) | `FontWeight.w700` or `FontWeight.bold` |
| Extra Bold (800) | `FontWeight.w800` |
| Black (900) | `FontWeight.w900` |

## Line Height Conversion

Figma shows line height as:
- **Percentage**: 150% → `height: 1.5`
- **Pixels**: 24px (for 16px font) → `height: 1.5` (24/16)
- **Auto**: Use default (omit height property)

```dart
// Figma: Line height 150%
TextStyle(
  fontSize: 16,
  height: 1.5, // Always a ratio, not pixels
)

// Figma: Line height 24px with 16px font
TextStyle(
  fontSize: 16,
  height: 24 / 16, // = 1.5
)
```

## Color Conversion

### Hex to Color

```dart
// Figma: #2196F3
Color(0xFF2196F3) // Add 0xFF prefix for full opacity

// Figma: #2196F3 with 80% opacity
Color(0xFF2196F3).withOpacity(0.8)
// or
Color(0xCC2196F3) // CC = 80% of FF (204/255)

// Figma: rgba(33, 150, 243, 0.8)
Color.fromRGBO(33, 150, 243, 0.8)
```

### Opacity Hex Values

| Opacity | Hex Value |
|---------|-----------|
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

## Text Decoration

| Figma Decoration | Flutter Decoration |
|------------------|-------------------|
| Underline | `decoration: TextDecoration.underline` |
| Strikethrough | `decoration: TextDecoration.lineThrough` |
| None | `decoration: TextDecoration.none` |

```dart
TextStyle(
  decoration: TextDecoration.underline,
  decorationColor: Colors.red,
  decorationStyle: TextDecorationStyle.dashed,
  decorationThickness: 2,
)
```

## Text Transform

Flutter doesn't have a TextStyle property for text transform. Handle it in the Text widget:

```dart
// Uppercase
Text(text.toUpperCase())

// Lowercase
Text(text.toLowerCase())

// Capitalize (first letter of each word)
Text(text.split(' ').map((word) =>
  word.isNotEmpty ? '${word[0].toUpperCase()}${word.substring(1)}' : ''
).join(' '))
```

## Material Design TextTheme Integration

Map Figma typography to Material TextTheme:

| Figma Text Style | Material TextTheme |
|------------------|-------------------|
| Display Large | `displayLarge` (57sp) |
| Display Medium | `displayMedium` (45sp) |
| Display Small | `displaySmall` (36sp) |
| Headline Large | `headlineLarge` (32sp) |
| Headline Medium | `headlineMedium` (28sp) |
| Headline Small | `headlineSmall` (24sp) |
| Title Large | `titleLarge` (22sp) |
| Title Medium | `titleMedium` (16sp) |
| Title Small | `titleSmall` (14sp) |
| Body Large | `bodyLarge` (16sp) |
| Body Medium | `bodyMedium` (14sp) |
| Body Small | `bodySmall` (12sp) |
| Label Large | `labelLarge` (14sp) |
| Label Medium | `labelMedium` (12sp) |
| Label Small | `labelSmall` (11sp) |

**Usage:**
```dart
Text(
  'Hello',
  style: Theme.of(context).textTheme.headlineMedium,
)
```

## Custom Font Setup

### 1. Add font files to pubspec.yaml

```yaml
flutter:
  fonts:
    - family: Roboto
      fonts:
        - asset: fonts/Roboto-Regular.ttf
        - asset: fonts/Roboto-Medium.ttf
          weight: 500
        - asset: fonts/Roboto-Bold.ttf
          weight: 700
    - family: CustomFont
      fonts:
        - asset: fonts/CustomFont-Regular.ttf
        - asset: fonts/CustomFont-Bold.ttf
          weight: 700
```

### 2. Use in TextStyle

```dart
TextStyle(
  fontFamily: 'CustomFont',
  fontSize: 16,
  fontWeight: FontWeight.w700,
)
```

### 3. Using Google Fonts package

```dart
// pubspec.yaml: google_fonts: ^6.1.0

import 'package:google_fonts/google_fonts.dart';

Text(
  'Hello',
  style: GoogleFonts.roboto(
    fontSize: 16,
    fontWeight: FontWeight.w600,
  ),
)

// Or in theme
ThemeData(
  textTheme: GoogleFonts.robotoTextTheme(),
)
```

## Typography System Definition

Create a centralized typography system:

```dart
abstract class AppTypography {
  // Headings
  static const TextStyle h1 = TextStyle(
    fontFamily: 'Roboto',
    fontSize: 32,
    fontWeight: FontWeight.w700,
    height: 1.25,
    letterSpacing: -0.5,
  );

  static const TextStyle h2 = TextStyle(
    fontFamily: 'Roboto',
    fontSize: 24,
    fontWeight: FontWeight.w600,
    height: 1.33,
  );

  // Body
  static const TextStyle bodyLarge = TextStyle(
    fontFamily: 'Roboto',
    fontSize: 16,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontFamily: 'Roboto',
    fontSize: 14,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );

  // Labels
  static const TextStyle labelLarge = TextStyle(
    fontFamily: 'Roboto',
    fontSize: 14,
    fontWeight: FontWeight.w500,
    height: 1.43,
    letterSpacing: 0.1,
  );
}
```

## Common Typography Patterns

### Button Text
```dart
TextStyle(
  fontSize: 14,
  fontWeight: FontWeight.w600,
  letterSpacing: 0.5,
)
```

### Input Placeholder
```dart
TextStyle(
  fontSize: 16,
  fontWeight: FontWeight.w400,
  color: Colors.grey,
)
```

### Caption/Helper Text
```dart
TextStyle(
  fontSize: 12,
  fontWeight: FontWeight.w400,
  color: Colors.grey[600],
  height: 1.33,
)
```

### Error Text
```dart
TextStyle(
  fontSize: 12,
  fontWeight: FontWeight.w400,
  color: Colors.red,
)
```

## Rich Text

For mixed styling within a single text block:

```dart
RichText(
  text: TextSpan(
    style: TextStyle(color: Colors.black),
    children: [
      TextSpan(text: 'Normal text '),
      TextSpan(
        text: 'bold text',
        style: TextStyle(fontWeight: FontWeight.bold),
      ),
      TextSpan(text: ' and '),
      TextSpan(
        text: 'colored text',
        style: TextStyle(color: Colors.blue),
      ),
    ],
  ),
)
```

## Text Overflow

| Figma Behavior | Flutter TextOverflow |
|----------------|---------------------|
| Truncate with ... | `overflow: TextOverflow.ellipsis` |
| Clip | `overflow: TextOverflow.clip` |
| Fade | `overflow: TextOverflow.fade` |
| Visible (overflow) | `overflow: TextOverflow.visible` |

```dart
Text(
  'Long text that might overflow',
  overflow: TextOverflow.ellipsis,
  maxLines: 2,
)
```

## Tips

1. **Use const for static TextStyles:**
   ```dart
   static const TextStyle bodyText = TextStyle(...);
   ```

2. **Inherit and modify:**
   ```dart
   Theme.of(context).textTheme.bodyLarge?.copyWith(
     color: Colors.red,
   )
   ```

3. **Line height is a ratio:**
   Always divide Figma's pixel value by font size

4. **Use Theme for consistency:**
   Define TextTheme in ThemeData for app-wide consistency

5. **Consider accessibility:**
   - Respect user's text scaling: `MediaQuery.textScaleFactorOf(context)`
   - Minimum 12sp for body text
