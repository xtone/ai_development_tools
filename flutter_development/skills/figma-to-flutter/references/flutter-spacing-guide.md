# Flutter Spacing Guide

This guide provides methods for extracting spacing values from Figma and converting them to Flutter EdgeInsets and spacing widgets.

## EdgeInsets Mapping

### Basic Patterns

| Figma Padding | Flutter EdgeInsets |
|---------------|-------------------|
| All sides equal | `EdgeInsets.all(16)` |
| Horizontal + Vertical | `EdgeInsets.symmetric(horizontal: 24, vertical: 16)` |
| Individual sides | `EdgeInsets.only(left: 16, top: 8, right: 16, bottom: 24)` |
| Left/Right only | `EdgeInsets.symmetric(horizontal: 16)` |
| Top/Bottom only | `EdgeInsets.symmetric(vertical: 16)` |

### Figma to EdgeInsets Conversion

**Figma shows:**
```
Padding: 16, 24, 16, 24 (top, right, bottom, left)
```

**Flutter conversion:**
```dart
// If top == bottom AND left == right
EdgeInsets.symmetric(horizontal: 24, vertical: 16)

// If all different
EdgeInsets.fromLTRB(24, 16, 24, 16) // left, top, right, bottom
```

### Common EdgeInsets Patterns

```dart
// Zero padding
EdgeInsets.zero

// All sides equal
EdgeInsets.all(16)

// Symmetric
EdgeInsets.symmetric(horizontal: 24, vertical: 16)

// Only specific sides
EdgeInsets.only(top: 16, bottom: 24)

// LTRB (Left, Top, Right, Bottom)
EdgeInsets.fromLTRB(16, 8, 16, 24)
```

## Gap/Spacing Between Elements

### Using SizedBox

**For vertical spacing in Column:**
```dart
Column(
  children: [
    Text('First'),
    SizedBox(height: 16),
    Text('Second'),
    SizedBox(height: 8),
    Text('Third'),
  ],
)
```

**For horizontal spacing in Row:**
```dart
Row(
  children: [
    Icon(Icons.star),
    SizedBox(width: 8),
    Text('Label'),
  ],
)
```

### Using the gap Package

```dart
// pubspec.yaml: gap: ^3.0.1

Column(
  children: [
    Text('First'),
    Gap(16),
    Text('Second'),
    Gap(8),
    Text('Third'),
  ],
)
```

### Using MainAxisAlignment for Distribution

```dart
Row(
  mainAxisAlignment: MainAxisAlignment.spaceBetween,
  children: [Widget1(), Widget2(), Widget3()],
)

// Results in equal space between widgets, widgets at edges
```

| MainAxisAlignment | Behavior |
|-------------------|----------|
| `spaceBetween` | Equal space between, first/last at edges |
| `spaceAround` | Equal space around each widget |
| `spaceEvenly` | Equal space everywhere including edges |

## Border Radius

### Figma to Flutter Mapping

| Figma Border Radius | Flutter BorderRadius |
|--------------------|---------------------|
| All corners equal | `BorderRadius.circular(12)` |
| Top corners only | `BorderRadius.vertical(top: Radius.circular(12))` |
| Bottom corners only | `BorderRadius.vertical(bottom: Radius.circular(12))` |
| Left corners only | `BorderRadius.horizontal(left: Radius.circular(12))` |
| Individual corners | `BorderRadius.only(topLeft: Radius.circular(12), ...)` |

### Common Patterns

```dart
// All corners equal
BorderRadius.circular(12)

// Pill shape (half of height)
BorderRadius.circular(24) // for 48px height button

// Top corners only (for bottom sheets)
BorderRadius.vertical(top: Radius.circular(24))

// Individual corners
BorderRadius.only(
  topLeft: Radius.circular(12),
  topRight: Radius.circular(12),
  bottomLeft: Radius.circular(0),
  bottomRight: Radius.circular(0),
)
```

## Margin vs Padding

In Flutter, "margin" is typically achieved with:

### 1. Container margin property
```dart
Container(
  margin: EdgeInsets.all(16),
  child: Content(),
)
```

### 2. Padding widget (around the element)
```dart
Padding(
  padding: EdgeInsets.all(16),
  child: Content(),
)
```

### 3. SizedBox for specific spacing
```dart
Column(
  children: [
    SizedBox(height: 16), // Top margin
    Content(),
    SizedBox(height: 16), // Bottom margin
  ],
)
```

## Spacing Scale Recommendation

Consider using a consistent spacing scale:

```dart
abstract class AppSpacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double xxl = 48;
}

// Usage
EdgeInsets.all(AppSpacing.md)
SizedBox(height: AppSpacing.lg)
```

## Figma Auto Layout Spacing

### Item Spacing (Gap)

Figma's "Item spacing" in Auto Layout translates to:

**Option 1: SizedBox between items**
```dart
Column(
  children: [
    Item1(),
    SizedBox(height: 16), // Item spacing
    Item2(),
    SizedBox(height: 16),
    Item3(),
  ],
)
```

**Option 2: Use List.separated**
```dart
ListView.separated(
  itemCount: items.length,
  separatorBuilder: (_, __) => SizedBox(height: 16),
  itemBuilder: (context, index) => ItemWidget(items[index]),
)
```

### Padding

Figma's "Padding" in Auto Layout translates to Container/Padding:

```dart
Container(
  padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
  child: Column(children: [...]),
)
```

## Responsive Spacing

For responsive spacing, consider screen size:

```dart
EdgeInsets responsivePadding(BuildContext context) {
  final width = MediaQuery.of(context).size.width;
  if (width < 600) {
    return EdgeInsets.all(16); // Mobile
  } else if (width < 1200) {
    return EdgeInsets.all(24); // Tablet
  } else {
    return EdgeInsets.all(32); // Desktop
  }
}
```

## Common Spacing Values

| Use Case | Typical Value |
|----------|---------------|
| Tight spacing (icons, badges) | 4-8 |
| Normal spacing (list items) | 12-16 |
| Section spacing | 24-32 |
| Page padding (mobile) | 16-20 |
| Page padding (tablet) | 24-32 |
| Card padding | 16-24 |
| Button padding (horizontal) | 16-24 |
| Button padding (vertical) | 8-16 |

## Tips

1. **Use const for static EdgeInsets:**
   ```dart
   static const padding = EdgeInsets.all(16);
   ```

2. **Prefer EdgeInsets.symmetric when applicable:**
   It's more readable than LTRB

3. **Create spacing constants:**
   Define a spacing scale for consistency

4. **Consider SafeArea:**
   For screen-level padding, use SafeArea widget

5. **Use MediaQuery.padding for system UI:**
   ```dart
   final systemPadding = MediaQuery.of(context).padding;
   ```
