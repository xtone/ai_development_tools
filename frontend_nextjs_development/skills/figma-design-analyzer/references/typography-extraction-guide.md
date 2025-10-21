# Typography Extraction Guide

This guide provides methods for extracting and translating typography properties from Figma to React + Tailwind CSS.

## Typography Properties

### 1. Font Family

**Figma Location:**
- Text properties panel → Font family dropdown

**Extraction:**
- Note the exact font family name
- Check if it's a system font, web font, or custom font

**Tailwind Mapping:**
```tsx
// Default Tailwind fonts
font-sans → font-family: ui-sans-serif, system-ui, sans-serif...
font-serif → font-family: ui-serif, Georgia, serif...
font-mono → font-family: ui-monospace, monospace...

// Custom fonts (defined in tailwind.config.js)
font-custom → font-family: 'CustomFont', sans-serif
```

**Important:** Check the project's tailwind.config.js for custom font definitions:
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        'custom': ['CustomFont', 'sans-serif'],
      }
    }
  }
}
```

### 2. Font Size

**Figma Location:**
- Text properties panel → Font size value (px)

**Extraction:**
- Read the pixel value directly

**Tailwind Mapping:**

| Figma (px) | Tailwind Class | rem | Notes |
|------------|---------------|-----|-------|
| 12px | text-xs | 0.75rem | Extra small |
| 14px | text-sm | 0.875rem | Small |
| 16px | text-base | 1rem | Base size |
| 18px | text-lg | 1.125rem | Large |
| 20px | text-xl | 1.25rem | Extra large |
| 24px | text-2xl | 1.5rem | 2x large |
| 30px | text-3xl | 1.875rem | 3x large |
| 36px | text-4xl | 2.25rem | 4x large |
| 48px | text-5xl | 3rem | 5x large |
| 60px | text-6xl | 3.75rem | 6x large |
| 72px | text-7xl | 4.5rem | 7x large |
| 96px | text-8xl | 6rem | 8x large |
| 128px | text-9xl | 8rem | 9x large |

**Custom sizes:**
```tsx
// If exact match not available
fontSize: 22px → className="text-[22px]"
```

### 3. Font Weight

**Figma Location:**
- Text properties panel → Font weight dropdown (Thin, Light, Regular, Medium, Bold, etc.)

**Extraction:**
- Note the weight name or numeric value

**Tailwind Mapping:**

| Figma Weight | Numeric | Tailwind Class |
|--------------|---------|---------------|
| Thin | 100 | font-thin |
| Extra Light | 200 | font-extralight |
| Light | 300 | font-light |
| Regular/Normal | 400 | font-normal |
| Medium | 500 | font-medium |
| Semi Bold | 600 | font-semibold |
| Bold | 700 | font-bold |
| Extra Bold | 800 | font-extrabold |
| Black | 900 | font-black |

### 4. Line Height (Leading)

**Figma Location:**
- Text properties panel → Line height value

**Types:**
- **Auto**: Figma calculates automatically
- **Pixel value**: Fixed line height (e.g., 24px)
- **Percentage**: Relative to font size (e.g., 150%)

**Extraction:**
1. Note the line height type
2. For pixel values: Read directly
3. For percentage: Calculate pixel value = font-size × percentage

**Tailwind Mapping:**

| Line Height | Tailwind Class | Value |
|------------|---------------|-------|
| Tight | leading-tight | 1.25 |
| Snug | leading-snug | 1.375 |
| Normal | leading-normal | 1.5 |
| Relaxed | leading-relaxed | 1.625 |
| Loose | leading-loose | 2 |
| No line height | leading-none | 1 |

**Pixel-specific values:**
```tsx
// Fixed pixel line height
lineHeight: 24px → className="leading-[24px]"
```

**Relative values:**
```tsx
// When line height is 1.5x font size
className="leading-normal"

// Custom relative value
lineHeight: 1.75 → className="leading-[1.75]"
```

### 5. Letter Spacing (Tracking)

**Figma Location:**
- Text properties panel → Letter spacing value

**Types:**
- **Pixel value**: Fixed spacing (e.g., 0.5px)
- **Percentage**: Relative to font size (e.g., 5%)

**Extraction:**
1. Note the value and type
2. For percentage: Convert to em units (5% = 0.05em)

**Tailwind Mapping:**

| Letter Spacing | Tailwind Class | Value |
|---------------|---------------|-------|
| Very tight | tracking-tighter | -0.05em |
| Tight | tracking-tight | -0.025em |
| Normal | tracking-normal | 0 |
| Wide | tracking-wide | 0.025em |
| Wider | tracking-wider | 0.05em |
| Widest | tracking-widest | 0.1em |

**Custom values:**
```tsx
// Pixel value
letterSpacing: 0.5px → className="tracking-[0.5px]"

// Em value
letterSpacing: 0.03em → className="tracking-[0.03em]"
```

### 6. Text Alignment

**Figma Location:**
- Text properties panel → Alignment buttons (left, center, right, justified)

**Tailwind Mapping:**
```tsx
// Horizontal alignment
Left → className="text-left"
Center → className="text-center"
Right → className="text-right"
Justified → className="text-justify"
```

### 7. Text Color

**Figma Location:**
- Text properties panel → Fill color

**Extraction:**
1. Get the color value (hex, RGB, or variable)
2. Check if it's a Figma variable (design token)
3. Note opacity if present

**Tailwind Mapping:**

**Using Tailwind colors:**
```tsx
// Named colors
#000000 → className="text-black"
#FFFFFF → className="text-white"
#EF4444 → className="text-red-500"
#3B82F6 → className="text-blue-500"
```

**Using arbitrary colors:**
```tsx
// Hex color
#1A202C → className="text-[#1A202C]"

// RGB color
rgb(26, 32, 44) → className="text-[rgb(26,32,44)]"
```

**Using design tokens (Figma variables):**
```tsx
// If Figma variable: "text/primary"
// Should map to CSS variable or Tailwind custom color
className="text-primary"
```

**With opacity:**
```tsx
// 50% opacity
className="text-black/50"
className="text-blue-500/50"
```

### 8. Text Decoration

**Figma Location:**
- Text properties panel → Decoration buttons (underline, strikethrough)

**Tailwind Mapping:**
```tsx
Underline → className="underline"
Strikethrough → className="line-through"
None → className="no-underline"
```

### 9. Text Transform

**Figma Location:**
- Text properties panel → Text case dropdown

**Tailwind Mapping:**
```tsx
Uppercase → className="uppercase"
Lowercase → className="lowercase"
Capitalize → className="capitalize"
None → className="normal-case"
```

### 10. Text Overflow

**Figma Location:**
- Text properties panel → Truncate option (...)

**Tailwind Mapping:**
```tsx
// Single line truncate
className="truncate"

// Multi-line clamp (2 lines)
className="line-clamp-2"

// Multi-line clamp (3 lines)
className="line-clamp-3"
```

## Figma Text Styles vs. React Implementation

### Extracting Text Styles

Figma allows designers to create reusable "Text Styles." When analyzing text:

1. **Check if a Text Style is applied**
   - If yes: Note the style name (e.g., "Heading 1", "Body Regular")
   - This indicates a reusable pattern

2. **Extract individual properties**
   - Even if a style is applied, extract individual properties
   - This helps create consistent React components

### Creating Reusable Typography Components

If the same text style is used multiple times, consider creating a reusable component:

```tsx
// Typography.tsx
export const Heading1 = ({ children, className = '' }: Props) => (
  <h1 className={`text-4xl font-bold leading-tight ${className}`}>
    {children}
  </h1>
);

export const BodyText = ({ children, className = '' }: Props) => (
  <p className={`text-base font-normal leading-normal ${className}`}>
    {children}
  </p>
);
```

## Complete Typography Analysis Workflow

When analyzing text in Figma:

1. **Identify the text element**
   - Note its semantic meaning (heading, paragraph, label, etc.)

2. **Extract font properties**
   - Font family
   - Font size
   - Font weight
   - Line height
   - Letter spacing

3. **Extract color and decoration**
   - Text color
   - Text decoration (underline, strikethrough)
   - Text transform (uppercase, lowercase)

4. **Extract alignment and overflow**
   - Text alignment
   - Truncation behavior

5. **Map to Tailwind classes**
   - Use standard Tailwind classes when possible
   - Use arbitrary values `[]` for custom values

6. **Choose appropriate HTML tag**
   - h1-h6 for headings
   - p for paragraphs
   - span for inline text
   - label for form labels

## Common Typography Patterns

### Headings

```tsx
// Heading 1
<h1 className="text-4xl font-bold leading-tight text-gray-900">
  Main Heading
</h1>

// Heading 2
<h2 className="text-3xl font-semibold leading-snug text-gray-800">
  Section Heading
</h2>

// Heading 3
<h3 className="text-2xl font-medium leading-normal text-gray-700">
  Subsection Heading
</h3>
```

### Body Text

```tsx
// Regular body text
<p className="text-base font-normal leading-relaxed text-gray-700">
  Lorem ipsum dolor sit amet...
</p>

// Small text
<p className="text-sm font-normal leading-normal text-gray-600">
  Small description text
</p>

// Large text
<p className="text-lg font-normal leading-relaxed text-gray-800">
  Emphasized body text
</p>
```

### Labels and Captions

```tsx
// Form label
<label className="text-sm font-medium text-gray-700">
  Input Label
</label>

// Caption
<span className="text-xs font-normal text-gray-500">
  Image caption or helper text
</span>
```

### Links

```tsx
// Default link
<a href="#" className="text-blue-600 underline hover:text-blue-800">
  Link text
</a>

// Link without underline
<a href="#" className="text-blue-600 hover:underline">
  Link text
</a>
```

## Responsive Typography

Consider how typography should adapt to different screen sizes:

```tsx
{/* Responsive font size */}
<h1 className="text-2xl md:text-3xl lg:text-4xl font-bold">
  Responsive Heading
</h1>

{/* Responsive line height */}
<p className="leading-normal md:leading-relaxed lg:leading-loose">
  Responsive paragraph
</p>
```

## Design Tokens and Figma Variables

If the design uses Figma variables for typography:

1. **Extract variable names**
   - e.g., "fontSize.heading.large", "color.text.primary"

2. **Map to CSS variables or Tailwind config**
   - Check tailwind.config.js for custom tokens
   - Use semantic class names

3. **Example:**
```tsx
// Figma variable: "text/heading/large"
// Maps to: text-heading-lg (defined in tailwind.config.js)
<h1 className="text-heading-lg font-bold">
  Heading
</h1>
```

## Pitfalls to Avoid

1. **Don't hardcode colors**: Use design tokens when available
2. **Don't use arbitrary values unnecessarily**: Prefer Tailwind's scale for consistency
3. **Don't forget line height**: It affects vertical rhythm significantly
4. **Don't ignore font loading**: Ensure custom fonts are properly loaded
5. **Don't skip semantic HTML**: Use h1-h6, p, etc. appropriately for accessibility
6. **Don't forget responsive typography**: Typography should adapt to screen size

## Tips

- **Use Figma's Inspect Panel**: Hover over text to see all properties at once
- **Check for Text Styles**: Reusable styles indicate design system patterns
- **Verify font availability**: Ensure custom fonts are available in the project
- **Consider accessibility**: Ensure sufficient color contrast (WCAG AA: 4.5:1 for normal text)
- **Use semantic HTML**: Choose the right tag for the content's meaning, not just appearance
- **Document custom values**: If using arbitrary values like `text-[17px]`, document why
- **Test on real devices**: Typography can look different on various screens
