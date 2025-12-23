# Flutter Layout Mapping Guide

This guide provides criteria for mapping Figma designs to appropriate Flutter layout widgets.

## Layout Widget Decision Tree

### 1. Row (Most Common for Horizontal)

Use `Row` when:
- Elements are arranged horizontally
- Elements have consistent spacing
- You need alignment control on both axes

**Figma Indicators:**
- Auto Layout with horizontal direction
- "Hug contents" or "Fill container" on children
- Consistent spacing between items

**Flutter Example:**
```dart
Row(
  mainAxisAlignment: MainAxisAlignment.spaceBetween,
  crossAxisAlignment: CrossAxisAlignment.center,
  children: [
    Text('Label'),
    Icon(Icons.arrow_forward),
  ],
)
```

### 2. Column (Most Common for Vertical)

Use `Column` when:
- Elements are arranged vertically
- Elements have consistent spacing
- You need alignment control on both axes

**Figma Indicators:**
- Auto Layout with vertical direction
- Sequential top-to-bottom arrangement
- Consistent vertical spacing

**Flutter Example:**
```dart
Column(
  mainAxisAlignment: MainAxisAlignment.start,
  crossAxisAlignment: CrossAxisAlignment.stretch,
  children: [
    Text('Title'),
    SizedBox(height: 16),
    Text('Description'),
  ],
)
```

### 3. Stack (For Overlapping Elements)

Use `Stack` when:
- Elements overlap each other
- Elements have absolute positioning
- You need z-index layering

**Figma Indicators:**
- Overlapping layers
- Elements positioned relative to frame edges
- Background images with overlaid content

**Flutter Example:**
```dart
Stack(
  children: [
    Image.asset('background.png'),
    Positioned(
      top: 16,
      right: 16,
      child: IconButton(...),
    ),
  ],
)
```

### 4. Wrap (For Flowing Content)

Use `Wrap` when:
- Elements should wrap to next line
- Dynamic number of items
- Tags, chips, or badges

**Figma Indicators:**
- Multiple rows of similar items
- Items that wrap based on container width
- Tag or chip groups

**Flutter Example:**
```dart
Wrap(
  spacing: 8.0,
  runSpacing: 8.0,
  children: tags.map((tag) => Chip(label: Text(tag))).toList(),
)
```

### 5. ListView (For Scrollable Lists)

Use `ListView` when:
- Content exceeds visible area
- Scrolling is needed
- List of similar items

**Figma Indicators:**
- Scrollable content area indicated
- Repeated list items
- Content extends beyond frame

**Flutter Example:**
```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ListTile(
    title: Text(items[index].title),
  ),
)
```

### 6. GridView (For Grid Layouts)

Use `GridView` when:
- Two-dimensional grid layout
- Consistent item sizes
- Gallery or product grids

**Figma Indicators:**
- Grid structure visible
- Consistent row and column alignment
- Multiple columns of items

**Flutter Example:**
```dart
GridView.count(
  crossAxisCount: 2,
  mainAxisSpacing: 16,
  crossAxisSpacing: 16,
  children: products.map((p) => ProductCard(p)).toList(),
)
```

## Figma Auto Layout → Flutter Mapping

### Direction Mapping

| Figma Direction | Flutter Widget |
|-----------------|----------------|
| Horizontal | `Row` |
| Vertical | `Column` |
| Wrap (horizontal) | `Wrap(direction: Axis.horizontal)` |
| Wrap (vertical) | `Wrap(direction: Axis.vertical)` |

### Alignment Mapping

| Figma Alignment | Flutter MainAxisAlignment |
|-----------------|---------------------------|
| Top / Left | `MainAxisAlignment.start` |
| Center | `MainAxisAlignment.center` |
| Bottom / Right | `MainAxisAlignment.end` |
| Space between | `MainAxisAlignment.spaceBetween` |
| Space around | `MainAxisAlignment.spaceAround` |
| Space evenly | `MainAxisAlignment.spaceEvenly` |

| Figma Cross-Axis | Flutter CrossAxisAlignment |
|------------------|----------------------------|
| Top / Left | `CrossAxisAlignment.start` |
| Center | `CrossAxisAlignment.center` |
| Bottom / Right | `CrossAxisAlignment.end` |
| Stretch | `CrossAxisAlignment.stretch` |
| Baseline | `CrossAxisAlignment.baseline` |

### Sizing Mapping

| Figma Sizing | Flutter Equivalent |
|--------------|-------------------|
| Hug contents | Default (no constraint) |
| Fill container | `Expanded` (in Row/Column) |
| Fixed | `SizedBox(width: X, height: Y)` |
| Fill container (flexible) | `Flexible` |

### Gap/Spacing Handling

**Option 1: SizedBox (Recommended for simple cases)**
```dart
Column(
  children: [
    Text('First'),
    SizedBox(height: 16),
    Text('Second'),
  ],
)
```

**Option 2: gap package (Cleaner for many items)**
```dart
// Using gap package
Column(
  children: [
    Text('First'),
    Gap(16),
    Text('Second'),
  ],
)
```

**Option 3: MainAxisAlignment (For distribution)**
```dart
Row(
  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
  children: [Widget1(), Widget2(), Widget3()],
)
```

## Common Layout Patterns

### Card Component
```dart
Container(
  padding: EdgeInsets.all(16),
  decoration: BoxDecoration(
    color: Colors.white,
    borderRadius: BorderRadius.circular(12),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.1),
        blurRadius: 8,
        offset: Offset(0, 4),
      ),
    ],
  ),
  child: Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text('Title', style: TextStyle(fontWeight: FontWeight.bold)),
      SizedBox(height: 8),
      Text('Description'),
    ],
  ),
)
```

### Header with Logo and Actions
```dart
Row(
  mainAxisAlignment: MainAxisAlignment.spaceBetween,
  children: [
    Image.asset('logo.png', height: 32),
    Row(
      children: [
        IconButton(icon: Icon(Icons.search), onPressed: () {}),
        IconButton(icon: Icon(Icons.menu), onPressed: () {}),
      ],
    ),
  ],
)
```

### Form Field
```dart
Column(
  crossAxisAlignment: CrossAxisAlignment.start,
  children: [
    Text('Email', style: TextStyle(fontWeight: FontWeight.w500)),
    SizedBox(height: 8),
    TextField(
      decoration: InputDecoration(
        hintText: 'Enter your email',
        border: OutlineInputBorder(),
      ),
    ),
  ],
)
```

### Overlay Modal
```dart
Stack(
  children: [
    // Background
    GestureDetector(
      onTap: onClose,
      child: Container(color: Colors.black54),
    ),
    // Modal content
    Center(
      child: Container(
        margin: EdgeInsets.all(32),
        padding: EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Modal Title'),
            SizedBox(height: 16),
            Text('Modal content goes here'),
          ],
        ),
      ),
    ),
  ],
)
```

## Constraints and Sizing

### Container Constraints

| Figma Setting | Flutter Widget/Property |
|---------------|------------------------|
| Fixed width | `SizedBox(width: X)` or `Container(width: X)` |
| Fixed height | `SizedBox(height: Y)` or `Container(height: Y)` |
| Min width | `ConstrainedBox(constraints: BoxConstraints(minWidth: X))` |
| Max width | `ConstrainedBox(constraints: BoxConstraints(maxWidth: X))` |
| Aspect ratio | `AspectRatio(aspectRatio: W/H)` |

### Flexible Sizing in Row/Column

```dart
Row(
  children: [
    // Fixed width
    SizedBox(width: 100, child: Text('Fixed')),
    // Fill remaining space
    Expanded(child: Text('Expanded')),
    // Flexible with flex factor
    Flexible(flex: 2, child: Text('Flex 2')),
  ],
)
```

## Tips

- **Start with Row/Column**: Most layouts can be achieved with Row and Column
- **Use Stack sparingly**: Only for overlapping elements, not for general positioning
- **Prefer Expanded over Flexible**: Unless you need specific flex behavior
- **Use SizedBox for spacing**: It's lightweight and explicit
- **Consider ScrollView**: Wrap Column/Row in SingleChildScrollView if content might overflow
- **Test on different screen sizes**: Use LayoutBuilder for responsive layouts

## Responsive Layout

```dart
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 600) {
      // Mobile layout
      return Column(children: [...]);
    } else {
      // Tablet/Desktop layout
      return Row(children: [...]);
    }
  },
)
```

## Common Mistakes

1. **Using Stack when Row/Column would work**
   - Stack is for overlapping, not for sequential layout

2. **Forgetting MainAxisSize.min**
   - Column/Row take full available space by default

3. **Not using Expanded in Row/Column**
   - Children won't fill available space without it

4. **Nested ScrollViews without proper configuration**
   - Use shrinkWrap: true and physics: NeverScrollableScrollPhysics()
