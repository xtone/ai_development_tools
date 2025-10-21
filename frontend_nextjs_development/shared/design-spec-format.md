# Design Specification Format

This document defines the format for design specifications that bridge the `figma-design-analyzer` and `nextjs-react-implementation` skills.

## Overview

Design specifications are Markdown documents with YAML front matter that contain structured design information extracted from Figma. These specifications serve as the contract between design analysis and implementation.

## File Naming Convention

```
{ComponentName}.design.md
```

Examples:
- `Button.design.md`
- `SearchBar.design.md`
- `NavigationHeader.design.md`

## Document Structure

### 1. Front Matter (Required)

YAML metadata at the top of the document:

```yaml
---
componentName: Button
atomicCategory: Atom
semanticElement: button
figmaNodeId: "123:456"
figmaUrl: "https://figma.com/design/fileKey/fileName?node-id=123-456"
dateCreated: 2025-10-21
lastUpdated: 2025-10-21
---
```

**Required Fields:**
- `componentName`: PascalCase component name
- `atomicCategory`: `Atom` | `Molecule` | `Organism`
- `semanticElement`: HTML element name (e.g., `button`, `div`, `section`)
- `figmaNodeId`: Figma node ID (format: "123:456")

**Optional Fields:**
- `figmaUrl`: Full Figma URL for reference
- `dateCreated`: ISO date string
- `lastUpdated`: ISO date string
- `designerNotes`: Any notes from the designer

### 2. Overview Section (Required)

Brief description of the component and its purpose:

```markdown
# Button Component Specification

## Overview
A primary action button component used for user interactions throughout the application.
Supports multiple variants and sizes to accommodate different use cases.
```

### 3. Atomic Design Classification (Required)

Explanation of why the component fits its atomic category:

```markdown
## Atomic Design Classification
- **Category**: Atom
- **Reason**: Single, indivisible interactive element with no sub-components
```

### 4. Layout Section (Required)

Layout method and properties:

```markdown
## Layout
- **Method**: Flexbox
- **Direction**: row
- **Justify Content**: center
- **Align Items**: center
- **Flex Wrap**: nowrap
```

**Common Layout Methods:**
- Flexbox
- CSS Grid
- Absolute Positioning
- Static/Relative

### 5. Spacing Section (Required)

All spacing values mapped to Tailwind classes:

```markdown
## Spacing
- **Padding**: px-6 py-3
- **Gap**: gap-2
- **Margin**: None (avoid margins, use gap instead)
- **Border Radius**: rounded-lg
```

**Tailwind Spacing Reference:**
- `p-4` = 16px (1rem)
- `px-6` = horizontal padding 24px
- `py-3` = vertical padding 12px
- `gap-2` = 8px gap between items
- Use arbitrary values for custom: `p-[18px]`

### 6. Typography Section (Required)

Text styling properties:

```markdown
## Typography
- **Font Family**: font-sans (System UI)
- **Font Size**: text-base (16px)
- **Font Weight**: font-semibold (600)
- **Line Height**: leading-normal (1.5)
- **Letter Spacing**: tracking-normal
- **Text Color**: text-white
- **Text Alignment**: text-center
- **Text Transform**: None
- **Text Decoration**: None
```

### 7. Colors Section (Required)

Color values for all states:

```markdown
## Colors
- **Background**: bg-blue-500
- **Hover Background**: hover:bg-blue-600
- **Active Background**: active:bg-blue-700
- **Disabled Background**: disabled:bg-gray-300
- **Text Color**: text-white
- **Border Color**: border-transparent
```

### 8. Visual Properties Section (Required)

Additional visual styling:

```markdown
## Visual Properties
- **Border Width**: border-0
- **Border Radius**: rounded-lg
- **Box Shadow**: shadow-md
- **Opacity**: opacity-100
- **Transition**: transition-colors duration-200
```

### 9. Semantic HTML Section (Required)

HTML element and accessibility:

```markdown
## Semantic HTML
- **Root Element**: `button`
- **ARIA Attributes**:
  - `aria-label`: Required when button has no text content (icon-only)
  - `aria-disabled`: Set to "true" when disabled
- **Role**: button (implicit from element)
```

### 10. Variants Section (Required if applicable)

All component variants and their properties:

```markdown
## Variants

### Variant Types

#### variant (primary | secondary | tertiary)
- **primary**:
  - Background: bg-blue-500
  - Text: text-white
  - Hover: hover:bg-blue-600
- **secondary**:
  - Background: bg-white
  - Text: text-blue-500
  - Border: border-2 border-blue-500
  - Hover: hover:bg-blue-50
- **tertiary**:
  - Background: bg-transparent
  - Text: text-blue-500
  - Hover: hover:bg-blue-50

#### size (small | medium | large)
- **small**: px-4 py-2 text-sm
- **medium**: px-6 py-3 text-base
- **large**: px-8 py-4 text-lg
```

### 11. States Section (Required)

Interaction states:

```markdown
## States

### Default
As specified in the Colors and Visual Properties sections above.

### Hover
- Background: bg-blue-600
- Cursor: cursor-pointer

### Active
- Background: bg-blue-700
- Transform: scale-95 (subtle press effect)

### Focus
- Outline: ring-2 ring-blue-500 ring-offset-2
- Outline Style: ring-offset-white

### Disabled
- Background: bg-gray-300
- Text: text-gray-500
- Cursor: cursor-not-allowed
- Opacity: opacity-50
```

### 12. Responsive Behavior Section (Required if applicable)

Breakpoint-specific changes:

```markdown
## Responsive Behavior

### Mobile (default, < 768px)
- Width: w-full
- Padding: px-4 py-2
- Font Size: text-sm

### Tablet (md, >= 768px)
- Width: w-auto
- Padding: md:px-6 md:py-3
- Font Size: md:text-base

### Desktop (lg, >= 1024px)
- Padding: lg:px-8 lg:py-4
- Font Size: lg:text-lg
```

### 13. Accessibility Section (Required)

Accessibility considerations:

```markdown
## Accessibility

### Keyboard Navigation
- **Focus**: Tab key to focus
- **Activation**: Enter or Space key to activate
- **Focus Indicator**: Visible ring outline

### Screen Reader
- **Announced As**: "Button, {button text}"
- **State Announcements**: "disabled" when disabled

### Color Contrast
- **Text/Background**: 7.2:1 (WCAG AAA)
- **Focus Indicator**: 3:1 minimum

### Additional
- Must have accessible name (text content or aria-label)
- Disabled state must be programmatically determinable
```

### 14. Assets Section (Required if applicable)

Referenced assets:

```markdown
## Assets

### Icons
- **Arrow Icon**: `/public/assets/icons/arrow-right.svg`
  - Size: 20×20px
  - Color: Inherits text color

### Images
None

### Fonts
- **Primary**: Inter (Google Fonts)
- **Fallback**: system-ui, sans-serif
```

### 15. Component Hierarchy Section (Required for Molecules/Organisms)

Child components and composition:

```markdown
## Component Hierarchy

### Child Components
1. **Icon** (Atom)
   - Import: `@/components/atoms/Icon`
   - Props: `name`, `size`, `color`
2. **Text** (Atom)
   - Import: `@/components/atoms/Text`
   - Props: `children`, `variant`, `size`

### Composition
```tsx
<Button>
  <Icon name="arrow-right" size="sm" />
  <Text variant="button">{children}</Text>
</Button>
```
```

### 16. Implementation Notes Section (Optional)

Additional guidance for implementation:

```markdown
## Implementation Notes

### Best Practices
- Always use semantic `<button>` element
- Avoid using `<a>` styled as button (unless it's truly a link)
- Include loading state if used for async actions
- Disable button during async operations

### Common Patterns
- Form submit buttons should have `type="submit"`
- Cancel/close buttons should have `type="button"`
- Use `onClick` for custom actions

### Edge Cases
- Icon-only buttons must have `aria-label`
- Long button text should truncate with ellipsis on mobile
- Multi-line button text should be avoided

### Performance Considerations
- Memoize click handlers in parent components
- Use React.memo if button is re-rendering unnecessarily
```

### 17. Design Tokens Section (Optional)

If using design tokens from Figma variables:

```markdown
## Design Tokens

### Colors
- `--color-primary-500`: #3B82F6
- `--color-primary-600`: #2563EB
- `--color-primary-700`: #1D4ED8

### Spacing
- `--spacing-2`: 8px
- `--spacing-3`: 12px
- `--spacing-6`: 24px

### Typography
- `--font-base`: 16px
- `--font-semibold`: 600
- `--leading-normal`: 1.5

### Shadows
- `--shadow-md`: 0 4px 6px -1px rgb(0 0 0 / 0.1)
```

## Complete Example

See `Button.design.md.example` for a complete example specification.

## Validation Checklist

Before passing a specification to the implementation skill, verify:

- [ ] All required sections are present
- [ ] Front matter is valid YAML
- [ ] Component name is in PascalCase
- [ ] Atomic category is correctly assigned
- [ ] All Tailwind classes are valid
- [ ] All variants are documented
- [ ] All states are specified
- [ ] Accessibility requirements are clear
- [ ] No contradictions or ambiguities
- [ ] Assets are referenced with correct paths

## Usage

1. **figma-design-analyzer** creates this specification from Figma analysis
2. **nextjs-react-implementation** reads this specification to generate code
3. Designers and developers can review and modify the specification if needed
4. Specification serves as single source of truth for the component design
