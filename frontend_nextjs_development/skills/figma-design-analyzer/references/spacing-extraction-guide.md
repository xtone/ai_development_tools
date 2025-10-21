# Spacing Extraction Guide

This guide provides methods for extracting and translating spacing values from Figma to Tailwind CSS.

## Spacing Types

### 1. Padding (Internal Spacing)

Padding is the space between a container's edge and its content.

**Figma Indicators:**
- Auto Layout padding values
- Distance from frame edge to first child element
- Uniform or directional padding (top, right, bottom, left)

**Extraction Method:**
1. Select the container frame
2. Check Auto Layout panel for padding values
3. Note if padding is uniform or differs by direction

**Tailwind Mapping:**
```tsx
// Uniform padding
padding: 16px → className="p-4"

// Directional padding
paddingX: 16px, paddingY: 8px → className="px-4 py-2"

// Individual sides
paddingTop: 16px → className="pt-4"
paddingRight: 16px → className="pr-4"
paddingBottom: 16px → className="pb-4"
paddingLeft: 16px → className="pl-4"
```

### 2. Margin (External Spacing)

Margin is the space around an element, separating it from adjacent elements.

**Figma Indicators:**
- Space between sibling elements (when not using Auto Layout gap)
- Constraints-based positioning with specific distances

**Important:** In modern Figma and React development, **margin is rarely used**. Use `gap` in Flexbox/Grid layouts instead.

**Tailwind Mapping:**
```tsx
// Top margin
marginTop: 16px → className="mt-4"

// Horizontal centering
marginX: auto → className="mx-auto"
```

### 3. Gap (Spacing Between Items)

Gap is the space between flex or grid items.

**Figma Indicators:**
- Auto Layout "Spacing between items" value
- Consistent distance between sibling elements in Auto Layout

**Extraction Method:**
1. Select the container with Auto Layout
2. Check "Spacing between items" value
3. For grid layouts, check both row and column gaps

**Tailwind Mapping:**
```tsx
// Uniform gap
gap: 16px → className="gap-4"

// Directional gap (Flexbox column)
gap: 16px → className="gap-y-4" (vertical gap in column layout)

// Grid with different row/column gaps
rowGap: 16px, columnGap: 8px → className="gap-y-4 gap-x-2"
```

## Tailwind Spacing Scale

Understand the Tailwind spacing scale for accurate conversion:

| Tailwind | rem | px (default) |
|----------|-----|--------------|
| 0 | 0 | 0 |
| px | 1px | 1px |
| 0.5 | 0.125rem | 2px |
| 1 | 0.25rem | 4px |
| 1.5 | 0.375rem | 6px |
| 2 | 0.5rem | 8px |
| 2.5 | 0.625rem | 10px |
| 3 | 0.75rem | 12px |
| 3.5 | 0.875rem | 14px |
| 4 | 1rem | 16px |
| 5 | 1.25rem | 20px |
| 6 | 1.5rem | 24px |
| 7 | 1.75rem | 28px |
| 8 | 2rem | 32px |
| 9 | 2.25rem | 36px |
| 10 | 2.5rem | 40px |
| 11 | 2.75rem | 44px |
| 12 | 3rem | 48px |
| 14 | 3.5rem | 56px |
| 16 | 4rem | 64px |
| 20 | 5rem | 80px |
| 24 | 6rem | 96px |
| 28 | 7rem | 112px |
| 32 | 8rem | 128px |

## Conversion Process

### Step 1: Extract Pixel Values from Figma

Use Figma MCP tools to get the design context:
```
get_design_context → Returns spacing values in the design
```

### Step 2: Convert to Tailwind Classes

1. **Exact Match**: If the pixel value matches Tailwind scale exactly, use that class
   - Example: 16px → `p-4`, 24px → `p-6`

2. **Close Match**: If within 1-2px, round to nearest Tailwind value
   - Example: 15px → `p-4` (16px), 23px → `p-6` (24px)

3. **Custom Value**: If no close match and pixel-perfect accuracy is required
   - Example: 18px → `p-[18px]`

4. **Design System**: If the project has a custom spacing scale, use that
   - Check tailwind.config.js for custom spacing values

### Step 3: Verify Consistency

Check if spacing is consistent across the design:
- If a spacing value (e.g., 16px) is used frequently, prefer Tailwind's standard scale
- If a spacing value is unique to one component, consider if it's intentional or a design inconsistency

## Auto Layout Analysis

### Reading Auto Layout Properties

When analyzing a Figma frame with Auto Layout:

1. **Direction**: Horizontal or Vertical
   - Determines `flex-row` or `flex-col`

2. **Spacing Between Items**: Gap value
   - Maps to `gap-{size}`

3. **Padding**: Top, Right, Bottom, Left
   - Maps to `p-{size}`, `px-{size}`, `py-{size}`, or individual `pt-/pr-/pb-/pl-`

4. **Alignment**:
   - Primary (main) axis: Maps to `justify-{align}`
   - Counter (cross) axis: Maps to `items-{align}`

### Example Auto Layout Translation

**Figma:**
```
Auto Layout: Vertical
Spacing: 16px
Padding: 24px (all sides)
Alignment: Center (counter axis)
```

**React + Tailwind:**
```tsx
<div className="flex flex-col gap-4 p-6 items-center">
  {/* children */}
</div>
```

## Nested Spacing

When dealing with nested components:

1. **Outer Container**: Typically has padding
2. **Inner Container**: Typically has gap between children
3. **Individual Items**: Typically have no margin (gap handles spacing)

### Example:

```tsx
{/* Outer container with padding */}
<div className="p-6">
  {/* Inner container with gap */}
  <div className="flex flex-col gap-4">
    {/* Individual items - no margin needed */}
    <div>Item 1</div>
    <div>Item 2</div>
    <div>Item 3</div>
  </div>
</div>
```

## Responsive Spacing

Consider how spacing should adapt to different screen sizes:

```tsx
{/* Responsive padding: smaller on mobile, larger on desktop */}
<div className="p-4 md:p-6 lg:p-8">
  {/* Responsive gap */}
  <div className="flex flex-col gap-2 md:gap-4 lg:gap-6">
    {/* children */}
  </div>
</div>
```

## Common Patterns

### Card Spacing
```tsx
// Typically: padding + gap for internal elements
<div className="p-6 flex flex-col gap-4">
  <h2>Title</h2>
  <p>Content</p>
</div>
```

### List Spacing
```tsx
// Typically: gap between items, no margin on items
<ul className="flex flex-col gap-2">
  <li>Item 1</li>
  <li>Item 2</li>
</ul>
```

### Section Spacing
```tsx
// Typically: large padding on sections
<section className="py-16 px-8">
  {/* content */}
</section>
```

## Pitfalls to Avoid

1. **Don't use margin when gap is available**: In Flexbox/Grid, use `gap` instead of margin on children
2. **Don't mix spacing methods**: Stick to one approach (gap vs margin) within a container
3. **Don't use arbitrary values unnecessarily**: Prefer Tailwind's scale when possible for consistency
4. **Don't forget responsive spacing**: Consider how spacing should change across breakpoints
5. **Don't ignore design system**: If the project has custom spacing, use it consistently

## Tips

- **Inspect carefully**: Always check both padding and gap values in Figma
- **Use gap by default**: Modern Flexbox/Grid layouts should use gap, not margin
- **Round to Tailwind scale**: Unless pixel-perfect accuracy is required, use standard Tailwind values
- **Document custom values**: If using arbitrary values like `p-[18px]`, document why
- **Check design system**: Verify if the project has custom spacing tokens in tailwind.config.js
