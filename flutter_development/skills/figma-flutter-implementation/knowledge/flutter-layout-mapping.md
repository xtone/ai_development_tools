# Flutter Layout Mapping Guide

## Overview

FigmaのAuto LayoutプロパティをFlutter Widgetに変換するためのガイドです。

## Auto Layout → Flutter Widget

### 基本的な方向

| Figma Auto Layout | Flutter Widget |
|-------------------|----------------|
| direction: VERTICAL | Column |
| direction: HORIZONTAL | Row |
| Frame with overlapping children | Stack |

### 詳細変換

#### Column (Vertical Layout)

**Figma:**
```
Auto Layout
- Direction: Vertical
- Gap: 16
- Padding: 24
```

**Flutter:**
```dart
Padding(
  padding: EdgeInsets.all(24),
  child: Column(
    children: [
      Widget1(),
      SizedBox(height: 16),
      Widget2(),
      SizedBox(height: 16),
      Widget3(),
    ],
  ),
)
```

#### Row (Horizontal Layout)

**Figma:**
```
Auto Layout
- Direction: Horizontal
- Gap: 8
- Padding: 16
```

**Flutter:**
```dart
Padding(
  padding: EdgeInsets.all(16),
  child: Row(
    children: [
      Widget1(),
      SizedBox(width: 8),
      Widget2(),
      SizedBox(width: 8),
      Widget3(),
    ],
  ),
)
```

#### Stack (Overlapping)

**Figma:**
```
Frame (not Auto Layout)
- Multiple children with absolute positioning
```

**Flutter:**
```dart
Stack(
  children: [
    Positioned(
      top: 0,
      left: 0,
      child: BackgroundWidget(),
    ),
    Positioned(
      bottom: 16,
      right: 16,
      child: OverlayWidget(),
    ),
  ],
)
```

## Alignment Mapping

### Primary Axis (Main Axis)

| Figma primaryAxisAlignItems | Flutter MainAxisAlignment |
|-----------------------------|---------------------------|
| MIN | MainAxisAlignment.start |
| CENTER | MainAxisAlignment.center |
| MAX | MainAxisAlignment.end |
| SPACE_BETWEEN | MainAxisAlignment.spaceBetween |
| SPACE_AROUND | MainAxisAlignment.spaceAround |
| SPACE_EVENLY | MainAxisAlignment.spaceEvenly |

### Counter Axis (Cross Axis)

| Figma counterAxisAlignItems | Flutter CrossAxisAlignment |
|-----------------------------|----------------------------|
| MIN | CrossAxisAlignment.start |
| CENTER | CrossAxisAlignment.center |
| MAX | CrossAxisAlignment.end |
| STRETCH | CrossAxisAlignment.stretch |
| BASELINE | CrossAxisAlignment.baseline |

### 使用例

**Figma:**
```
Auto Layout
- Direction: Horizontal
- Primary Axis: CENTER
- Counter Axis: STRETCH
```

**Flutter:**
```dart
Row(
  mainAxisAlignment: MainAxisAlignment.center,
  crossAxisAlignment: CrossAxisAlignment.stretch,
  children: [...],
)
```

## Size & Constraints

### Width/Height Constraints

| Figma Size | Flutter |
|------------|---------|
| Fixed 100 | SizedBox(width: 100) または width: 100 |
| Fill Container | Expanded() でラップ |
| Hug Contents | デフォルト（指定なし） |

### 使用例

**Fill Container (水平方向):**
```dart
Row(
  children: [
    Expanded(
      child: Container(...),  // Fillとして動作
    ),
    SizedBox(width: 100),     // Fixed
  ],
)
```

**Fill Container (垂直方向):**
```dart
Column(
  children: [
    Expanded(
      child: Container(...),  // Fillとして動作
    ),
    SizedBox(height: 50),     // Fixed
  ],
)
```

### Min/Max Constraints

**Figma:**
```
Width: Min 100, Max 300
Height: Min 50
```

**Flutter:**
```dart
ConstrainedBox(
  constraints: BoxConstraints(
    minWidth: 100,
    maxWidth: 300,
    minHeight: 50,
  ),
  child: ...,
)
```

## Spacing Mapping

### Padding

| Figma Padding | Flutter EdgeInsets |
|---------------|-------------------|
| padding: 16 | EdgeInsets.all(16) |
| paddingTop: 8 | EdgeInsets.only(top: 8) |
| paddingHorizontal: 16, paddingVertical: 8 | EdgeInsets.symmetric(horizontal: 16, vertical: 8) |
| top: 8, right: 16, bottom: 8, left: 16 | EdgeInsets.fromLTRB(16, 8, 16, 8) |

### Gap (Item Spacing)

FigmaのgapはFlutterでは直接サポートされないため、以下の方法で実装：

**方法1: SizedBox**
```dart
Column(
  children: [
    Widget1(),
    SizedBox(height: 16),  // gap: 16
    Widget2(),
    SizedBox(height: 16),
    Widget3(),
  ],
)
```

**方法2: ListView + separatorBuilder**
```dart
ListView.separated(
  itemCount: items.length,
  separatorBuilder: (context, index) => SizedBox(height: 16),
  itemBuilder: (context, index) => ItemWidget(items[index]),
)
```

**方法3: Wrap widget（gap対応）**
```dart
Wrap(
  spacing: 8,      // horizontal gap
  runSpacing: 16,  // vertical gap between lines
  children: [...],
)
```

## Common Patterns

### Card Layout

**Figma:**
```
Frame (Card)
- Auto Layout: Vertical
- Padding: 16
- Gap: 12
- Corner Radius: 8
- Fill: #FFFFFF
- Shadow: ...
```

**Flutter:**
```dart
Container(
  padding: EdgeInsets.all(16),
  decoration: BoxDecoration(
    color: Colors.white,
    borderRadius: BorderRadius.circular(8),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.1),
        blurRadius: 4,
        offset: Offset(0, 2),
      ),
    ],
  ),
  child: Column(
    children: [
      TitleWidget(),
      SizedBox(height: 12),
      ContentWidget(),
      SizedBox(height: 12),
      FooterWidget(),
    ],
  ),
)
```

### List Item Layout

**Figma:**
```
Frame (List Item)
- Auto Layout: Horizontal
- Padding: 16
- Gap: 12
- Counter Axis: CENTER
```

**Flutter:**
```dart
Padding(
  padding: EdgeInsets.all(16),
  child: Row(
    crossAxisAlignment: CrossAxisAlignment.center,
    children: [
      LeadingIcon(),
      SizedBox(width: 12),
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TitleText(),
            SubtitleText(),
          ],
        ),
      ),
      TrailingIcon(),
    ],
  ),
)
```

### Bottom Fixed Button

**Figma:**
```
Frame (Screen)
- Auto Layout: Vertical
- Children:
  - Scrollable Content (Fill)
  - Bottom Bar (Fixed at bottom)
```

**Flutter:**
```dart
Scaffold(
  body: Column(
    children: [
      Expanded(
        child: SingleChildScrollView(
          child: ContentWidget(),
        ),
      ),
      // Bottom fixed area
      Container(
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [...],
        ),
        child: ElevatedButton(
          onPressed: () {},
          child: Text('Button'),
        ),
      ),
    ],
  ),
)
```

## Wrap Layout

**Figma:**
```
Auto Layout
- Direction: Horizontal
- Wrap: true
- Gap: 8
- Run Gap: 16
```

**Flutter:**
```dart
Wrap(
  spacing: 8,       // horizontal gap
  runSpacing: 16,   // vertical gap between lines
  children: [
    Chip1(),
    Chip2(),
    Chip3(),
    // ... more chips that wrap to next line
  ],
)
```

## Responsive Layouts

### MediaQuery Based

```dart
Widget build(BuildContext context) {
  final width = MediaQuery.of(context).size.width;

  if (width < 600) {
    // Mobile: Vertical layout
    return Column(children: [...]);
  } else {
    // Tablet/Desktop: Horizontal layout
    return Row(children: [...]);
  }
}
```

### LayoutBuilder Based

```dart
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      return MobileLayout();
    } else {
      return DesktopLayout();
    }
  },
)
```

## Tips

1. **FigmaのAuto Layout方向を確認**: 最初にVertical/Horizontalを判断
2. **gapは手動で追加**: SizedBoxを使って再現
3. **Fill → Expanded**: コンテナを埋める要素はExpandedでラップ
4. **Stretchを忘れずに**: CrossAxisAlignment.stretchが必要な場合が多い
5. **ネストを意識**: 複雑なレイアウトはColumn/Rowをネストして構築
