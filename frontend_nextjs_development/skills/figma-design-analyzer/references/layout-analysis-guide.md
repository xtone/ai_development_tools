# Layout Analysis Guide

This guide provides criteria for determining the appropriate CSS layout method when converting Figma designs to React components.

## Layout Method Decision Tree

### 1. Flexbox (Most Common)

Use Flexbox when:
- Elements are arranged in a single direction (row or column)
- Elements have consistent spacing (gap)
- Elements need to wrap
- Elements need dynamic sizing (flex-grow, flex-shrink)
- Vertical or horizontal centering is required

**Figma Indicators:**
- Auto Layout with single direction
- Consistent spacing between items
- "Hug contents" or "Fill container" settings
- Alignment properties (top, center, bottom, left, right)

**Example:**
```tsx
<div className="flex flex-col gap-4">
  <div>Item 1</div>
  <div>Item 2</div>
</div>
```

### 2. CSS Grid

Use Grid when:
- Elements are arranged in a two-dimensional layout (rows AND columns)
- Complex alignment is needed across multiple axes
- Explicit row/column sizing is required
- Elements span multiple rows or columns

**Figma Indicators:**
- Grid layout visible in design
- Elements aligned to both rows and columns
- Consistent grid structure across the design
- Elements with specific row/column positioning

**Example:**
```tsx
<div className="grid grid-cols-3 gap-4">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</div>
```

### 3. Absolute Positioning

Use absolute positioning when:
- Elements overlap each other
- Elements have fixed positions relative to a container
- Elements need to be positioned independently of document flow

**Figma Indicators:**
- Overlapping layers
- Constraints set to specific distances from edges
- Elements floating above other content
- Fixed positioning relative to parent frame

**Example:**
```tsx
<div className="relative">
  <div className="absolute top-4 right-4">
    Overlay content
  </div>
</div>
```

### 4. Float (Rare, Legacy)

Generally avoid float in modern React development. Use Flexbox instead.

Only consider float for:
- Text wrapping around images (though even this can be done with Grid)

### 5. Table (Rare, Semantic Only)

Use table layout only for actual tabular data, not for layout purposes.

**When to use:**
- Displaying data in rows and columns with headers
- Semantic table markup is needed for accessibility

## Component Layout Patterns

### Auto Layout → Flexbox Mapping

| Figma Auto Layout | Tailwind CSS |
|------------------|--------------|
| Horizontal direction | `flex-row` |
| Vertical direction | `flex-col` |
| Spacing between items | `gap-{size}` |
| Padding | `p-{size}` or `px-{size} py-{size}` |
| Hug contents | (no specific class, use content-based sizing) |
| Fill container | `flex-1` or `w-full h-full` |
| Align items (cross-axis) | `items-{start\|center\|end\|stretch}` |
| Justify content (main-axis) | `justify-{start\|center\|end\|between\|around}` |

### Constraints → Positioning Mapping

| Figma Constraint | CSS Approach |
|-----------------|--------------|
| Left + Right | `w-full` or specific width with margins |
| Top + Bottom | `h-full` or specific height with margins |
| Left + Top | Default (top-left aligned) |
| Center | `mx-auto` (horizontal) or flexbox centering |
| Scale | `w-full h-full object-contain` or responsive units |

## Analysis Workflow

When analyzing a Figma node's layout:

1. **Check for Auto Layout**
   - If present: Use Flexbox
   - Direction → `flex-row` or `flex-col`
   - Spacing → `gap-{size}`
   - Alignment → `items-{align}` and `justify-{justify}`

2. **Check for Grid Structure**
   - If elements align to both rows and columns: Use CSS Grid
   - Count columns and rows
   - Measure gaps

3. **Check for Overlapping Elements**
   - If elements overlap: Use `relative` + `absolute` positioning
   - Measure distances from edges

4. **Check for Responsive Behavior**
   - Analyze constraints
   - Determine if width/height should be fixed or flexible
   - Consider breakpoints for responsive design

5. **Nested Layouts**
   - Analyze each nesting level separately
   - Parent might be Grid, children might be Flexbox
   - Apply layout methods independently at each level

## Common Patterns

### Card Component
```tsx
// Typically Flexbox with column direction
<div className="flex flex-col gap-4 p-6 rounded-lg shadow">
  <h2>Title</h2>
  <p>Description</p>
</div>
```

### Header with Logo and Navigation
```tsx
// Flexbox with space-between
<header className="flex items-center justify-between px-8 py-4">
  <img src="logo.png" alt="Logo" />
  <nav className="flex gap-6">
    <a href="#">Link 1</a>
    <a href="#">Link 2</a>
  </nav>
</header>
```

### Image Gallery
```tsx
// CSS Grid for consistent layout
<div className="grid grid-cols-3 gap-4">
  <img src="1.jpg" />
  <img src="2.jpg" />
  <img src="3.jpg" />
</div>
```

### Overlay Modal
```tsx
// Absolute positioning for overlay
<div className="relative">
  <div className="absolute inset-0 bg-black/50">
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
      Modal content
    </div>
  </div>
</div>
```

## Tips

- **Start with Flexbox**: When in doubt, start with Flexbox. It's the most flexible and commonly used.
- **Prefer Semantic Layout**: Use Grid for grid-like structures, not Flexbox workarounds.
- **Minimize Absolute Positioning**: Use it only when necessary. It breaks document flow and makes responsive design harder.
- **Analyze Nesting**: Each nesting level can use a different layout method. Don't force a single method for the entire component.
- **Consider Responsiveness**: Think about how the layout should adapt to different screen sizes. Use Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`, etc.) when needed.
