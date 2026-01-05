---
name: figma-to-flutter
description: Extract and analyze Figma designs to create Flutter-specific design specifications. Use this skill when you need to analyze Figma nodes, extract design properties (layout, spacing, typography), classify components using Atomic Design principles, and generate design specification documents optimized for Flutter implementation.
---

# Figma to Flutter Design Analyzer

## Overview

Systematically analyze Figma designs and extract structured design specifications optimized for Flutter implementation. This skill focuses on understanding design intent, extracting accurate properties, and creating comprehensive design specification documents that serve as blueprints for Flutter widgets.

**Use this skill when:**
- Analyzing Figma designs for Flutter implementation
- Extracting design tokens and component specifications for Flutter
- Classifying components according to Atomic Design principles
- Creating design specification documents for Flutter developers
- Converting Figma Auto Layout to Flutter Row/Column/Stack

## Core Workflow

### Step 1: Extract Figma Design Information

When given a Figma URL or node ID, use Figma MCP tools to extract design data:

1. **Parse the Figma URL to extract node ID:**
   ```
   URL: https://figma.com/design/fileKey/fileName?node-id=1-2
   Node ID: 1:2 (replace - with :)
   ```

2. **Extract node design context:**
   ```
   mcp__figma-dev__get_design_context(
     nodeId: "1:2",
     dirForAssetWrites: "/absolute/path/to/project/assets",
     clientLanguages: "dart",
     clientFrameworks: "flutter"
   )
   ```

3. **Get component metadata for structure overview:**
   ```
   mcp__figma-dev__get_metadata(
     nodeId: "1:2",
     clientLanguages: "dart",
     clientFrameworks: "flutter"
   )
   ```

4. **Check for Figma variables (design tokens):**
   ```
   mcp__figma-dev__get_variable_defs(
     nodeId: "1:2",
     clientLanguages: "dart",
     clientFrameworks: "flutter"
   )
   ```

5. **Verify Code Connect mappings:**
   ```
   mcp__figma-dev__get_code_connect_map(
     nodeId: "1:2",
     clientLanguages: "dart",
     clientFrameworks: "flutter"
   )
   ```

### Step 2: Handle Component Instances and Variants

**Important:** When the node is a component instance:

1. **Identify if it's an instance:**
   - Check metadata for "component instance" type
   - Note the main component ID

2. **Get the main component:**
   - Use `get_design_context` on the main component node
   - Extract the base structure and properties

3. **Extract instance-specific properties:**
   - Get the instance's specific size, device, and variant settings
   - Note any overrides (text, images, colors, etc.)

4. **Handle variants:**
   - If the main component uses variants, identify the variant mode
   - Extract the correct variant values for the instance
   - Document variant properties for Flutter constructor parameters

### Step 3: Classify the Component

Use Atomic Design principles to classify the component:

1. **Read the classification guide:**
   ```
   Read references/flutter-atomic-design.md
   ```

2. **Apply the decision tree:**
   - **Atom**: Indivisible, single purpose (button, text field, icon, text)
   - **Molecule**: 2-5 atoms, simple combination (search bar, form field)
   - **Organism**: Complex, multiple molecules/atoms (app bar, card, form)

3. **Determine the Flutter widget category:**
   - Document: `atomicCategory: Atom | Molecule | Organism`
   - Map to Flutter directory: `atoms/`, `molecules/`, `organisms/`

### Step 4: Analyze Layout and Map to Flutter

Extract layout information and map to Flutter widgets:

1. **Read layout mapping guide:**
   ```
   Read references/flutter-layout-mapping.md
   ```

2. **Map Figma Auto Layout to Flutter:**

   | Figma Auto Layout | Flutter Widget |
   |-------------------|----------------|
   | Horizontal direction | `Row` |
   | Vertical direction | `Column` |
   | Spacing between items | `SizedBox` or `MainAxisAlignment.spaceEvenly` |
   | Wrap | `Wrap` |
   | Overlapping elements | `Stack` + `Positioned` |

3. **Map Figma sizing to Flutter:**

   | Figma Setting | Flutter Equivalent |
   |---------------|-------------------|
   | Hug contents | Default (no constraint) |
   | Fill container | `Expanded` or `Flexible` |
   | Fixed width/height | `SizedBox(width: X, height: Y)` |
   | Min/Max constraints | `ConstrainedBox` |

4. **Map alignment:**

   | Figma Alignment | Flutter |
   |-----------------|---------|
   | Left/Top | `CrossAxisAlignment.start` / `MainAxisAlignment.start` |
   | Center | `CrossAxisAlignment.center` / `MainAxisAlignment.center` |
   | Right/Bottom | `CrossAxisAlignment.end` / `MainAxisAlignment.end` |
   | Space Between | `MainAxisAlignment.spaceBetween` |

5. **Document in specification:**
   ```markdown
   ## Layout
   - Widget: Column
   - MainAxisAlignment: start
   - CrossAxisAlignment: center
   - Children spacing: 16.0

   ## Sizing
   - Width: Expanded (fill parent)
   - Height: Hug contents (intrinsic)
   ```

### Step 5: Extract Spacing and Padding

Extract spacing values for Flutter:

1. **Read spacing guide:**
   ```
   Read references/flutter-spacing-guide.md
   ```

2. **Extract padding values:**
   - Map Figma padding to `EdgeInsets`
   - Use `EdgeInsets.all()`, `EdgeInsets.symmetric()`, or `EdgeInsets.only()`

3. **Extract gap/spacing values:**
   - Convert gaps to `SizedBox(width: X)` or `SizedBox(height: Y)`
   - Consider using `gap` package for cleaner code

4. **Extract border radius:**
   - Map to `BorderRadius.circular()` or `BorderRadius.only()`

5. **Document in specification:**
   ```markdown
   ## Spacing
   - Padding: EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0)
   - Children spacing: 12.0 (use SizedBox)
   - Border Radius: BorderRadius.circular(12.0)
   ```

### Step 6: Extract Typography

Extract text styling for Flutter:

1. **Read typography guide:**
   ```
   Read references/flutter-typography-guide.md
   ```

2. **Map to TextStyle:**
   ```dart
   TextStyle(
     fontFamily: 'Roboto',
     fontSize: 16.0,
     fontWeight: FontWeight.w600,
     height: 1.5, // line height ratio
     letterSpacing: 0.5,
     color: Color(0xFF1A1A1A),
   )
   ```

3. **Consider ThemeData integration:**
   - Map to `Theme.of(context).textTheme.bodyLarge`
   - Check if custom TextTheme is needed

4. **Document in specification:**
   ```markdown
   ## Typography
   - Style: TextStyle
     - fontFamily: 'Roboto'
     - fontSize: 16.0
     - fontWeight: FontWeight.w600
     - height: 1.5
     - color: Color(0xFF1A1A1A)
   - Theme mapping: bodyLarge (if applicable)
   ```

### Step 7: Extract Colors and Visual Properties

Extract colors and visual styling for Flutter:

1. **Extract color values:**
   - Convert hex colors to `Color(0xFFRRGGBB)` format
   - Note opacity values

2. **Map to ColorScheme:**
   - Check if colors match Material Design ColorScheme
   - Document custom colors

3. **Extract visual properties:**
   - Box shadow → `BoxShadow`
   - Border → `Border` or `BorderSide`
   - Gradient → `LinearGradient` or `RadialGradient`

4. **Document in specification:**
   ```markdown
   ## Colors
   - Background: Color(0xFF2196F3)
   - Text: Color(0xFFFFFFFF)
   - Border: Color(0xFF1976D2)

   ## Visual Properties
   - Shadow: BoxShadow(
       color: Color(0x1A000000),
       blurRadius: 8.0,
       offset: Offset(0, 4),
     )
   - Border: Border.all(color: Color(0xFF1976D2), width: 1.0)
   - Border Radius: BorderRadius.circular(8.0)
   ```

### Step 8: Determine Widget Type and State Management

Based on the design, determine the appropriate Flutter widget approach:

1. **Widget type decision:**
   - **StatelessWidget**: No internal state changes
   - **StatefulWidget**: Has internal state (animations, form inputs)
   - **HooksConsumerWidget**: Needs Riverpod + hooks
   - **ConsumerWidget**: Needs Riverpod only

2. **Identify required callbacks:**
   - `onTap`, `onPressed`, `onChanged`, etc.
   - Document callback signatures

3. **Identify constructor parameters:**
   - Required parameters
   - Optional parameters with defaults
   - Variant-based parameters

4. **Document in specification:**
   ```markdown
   ## Widget Architecture
   - Type: StatelessWidget
   - Riverpod: Not required

   ## Constructor Parameters
   - required String label
   - VoidCallback? onPressed
   - ButtonVariant variant = ButtonVariant.primary
   - ButtonSize size = ButtonSize.medium
   ```

### Step 9: Handle Responsive Design

When multiple Figma nodes represent different device sizes:

1. **Extract all node IDs** from provided URLs
   - Mobile node
   - Tablet node
   - Desktop node (if applicable for Flutter Web)

2. **Analyze each node:**
   - Layout changes
   - Spacing changes
   - Typography changes
   - Hidden/shown elements

3. **Document responsive variations:**
   ```markdown
   ## Responsive Behavior
   - Mobile (< 600): Column layout, smaller padding
   - Tablet (>= 600): Row layout, larger spacing
   - Use LayoutBuilder or MediaQuery for breakpoints
   ```

### Step 10: Identify Native Platform Requirements

Check if the design requires native platform features:

1. **Identify platform-specific elements:**
   - Camera access
   - Biometric authentication
   - Push notifications
   - Platform-specific UI (Cupertino for iOS)

2. **Document native requirements:**
   ```markdown
   ## Native Integration
   - iOS: Requires camera access (AVFoundation)
   - Android: Requires camera permission (Camera2 API)
   - MethodChannel: app.example/camera

   ## Related Skills
   - For iOS implementation: Use ios-development/swiftui-components
   - For Android implementation: Use android-development skills
   ```

### Step 11: Generate Design Specification Document

Create a comprehensive design specification:

```markdown
---
widgetName: PrimaryButton
atomicCategory: Atom
figmaNodeId: "123:456"
figmaUrl: "https://figma.com/design/..."
---

# PrimaryButton Widget Specification

## Overview
A primary action button widget for the application.

## Atomic Design Classification
- Category: Atom
- Reason: Single, indivisible interactive element
- Directory: lib/presentation/widgets/atoms/

## Widget Architecture
- Type: StatelessWidget
- Riverpod: Not required

## Constructor Parameters
```dart
const PrimaryButton({
  super.key,
  required this.label,
  this.onPressed,
  this.variant = ButtonVariant.primary,
  this.size = ButtonSize.medium,
  this.isLoading = false,
});
```

## Layout
- Widget: Container → InkWell → Row
- MainAxisAlignment: center
- CrossAxisAlignment: center
- MainAxisSize: min

## Sizing
- Height: 48.0 (medium), 40.0 (small), 56.0 (large)
- Width: Hug contents (intrinsic)
- Min Width: 120.0

## Spacing
- Padding: EdgeInsets.symmetric(horizontal: 24.0, vertical: 12.0)
- Icon-Label gap: 8.0

## Typography
- Style: TextStyle
  - fontSize: 16.0
  - fontWeight: FontWeight.w600
  - color: Colors.white

## Colors
- Primary:
  - Background: Color(0xFF2196F3)
  - Text: Color(0xFFFFFFFF)
- Secondary:
  - Background: Color(0xFFFFFFFF)
  - Text: Color(0xFF2196F3)
  - Border: Color(0xFF2196F3)

## Visual Properties
- Border Radius: BorderRadius.circular(8.0)
- Shadow (elevated): BoxShadow(
    color: Color(0x1A000000),
    blurRadius: 4.0,
    offset: Offset(0, 2),
  )

## States
- Default: As specified above
- Pressed: Slightly darker background (0.9 opacity)
- Disabled: 0.5 opacity, no interaction
- Loading: Show CircularProgressIndicator, disable tap

## Variants
```dart
enum ButtonVariant { primary, secondary, tertiary }
enum ButtonSize { small, medium, large }
```

## Accessibility
- Semantics label for screen readers
- Sufficient touch target (minimum 48x48)
- Color contrast meets WCAG AA

## Assets
- Icons: Use Icons.* or custom SVG

## Native Integration
- None required

## Implementation Notes
- Use InkWell for tap ripple effect
- Wrap with Semantics for accessibility
- Consider using Material Design 3 FilledButton as base
```

## Special Workflows

### Breaking Down a Full Screen

When given a full screen Figma node:

1. **Get screen metadata** to understand structure
2. **Identify major sections:**
   - AppBar
   - Body content
   - Bottom navigation
   - FAB (Floating Action Button)

3. **For each section:**
   - Classify as Organism
   - Identify child Molecules and Atoms
   - Extract design properties
   - Create individual specifications

4. **Create widget tree:**
   ```
   Screen (Scaffold)
   ├─ AppBar (Organism)
   │  ├─ BackButton (Atom)
   │  ├─ Title (Atom)
   │  └─ ActionButtons (Molecule)
   ├─ Body (Organism)
   │  ├─ HeaderSection (Molecule)
   │  └─ ContentList (Organism)
   │     └─ ListItem (Molecule) × N
   └─ BottomNavigation (Organism)
      └─ NavItem (Atom) × 4
   ```

5. **Generate specifications from bottom-up:**
   - Create Atom specifications first
   - Build Molecule specifications
   - Assemble Organism specifications

### Comparing Design with Implementation

When asked to compare an existing widget with Figma:

1. **Read the existing widget code**
2. **Extract Figma design properties** using MCP tools
3. **Compare systematically:**
   - Layout (Row/Column vs Figma Auto Layout)
   - Spacing values
   - Typography
   - Colors
4. **Generate a diff report**

## Best Practices

1. **Always read guides before starting:**
   - Layout mapping guide for Flutter widget selection
   - Spacing guide for EdgeInsets extraction
   - Typography guide for TextStyle creation
   - Atomic Design guide for classification

2. **Prioritize pixel-perfect accuracy:**
   - Use exact spacing values from Figma
   - Match typography precisely
   - Verify colors match design tokens

3. **Consider Flutter conventions:**
   - Use const constructors where possible
   - Follow Flutter naming conventions (camelCase)
   - Use Material Design widgets as base when appropriate

4. **Document thoroughly:**
   - Include all variants and states
   - Document responsive behavior
   - Note accessibility considerations
   - Include constructor parameters

5. **Consider the flutter-widget-assistant:**
   - For complex architecture decisions, recommend using flutter-widget-assistant skill
   - This skill focuses on design extraction, not architecture decisions

## Resources

This skill includes comprehensive guides:

### references/

- **flutter-layout-mapping.md**: Mapping Figma Auto Layout to Flutter widgets
- **flutter-spacing-guide.md**: Converting Figma spacing to EdgeInsets
- **flutter-typography-guide.md**: Creating TextStyle from Figma
- **flutter-atomic-design.md**: Atomic Design classification for Flutter

**Usage:** Always read relevant guides before starting analysis.

## Common Pitfalls

1. **Not handling component instances properly:**
   - Always get the main component when working with instances
   - Extract instance-specific properties separately

2. **Ignoring variants:**
   - Check for variant properties in Figma
   - Document all variant options as enums

3. **Wrong layout widget selection:**
   - Read the layout guide
   - Don't use Stack when Row/Column would work

4. **Forgetting responsive behavior:**
   - Check for responsive variants in Figma
   - Document breakpoint changes

5. **Missing state considerations:**
   - Document all interactive states
   - Consider loading, error, empty states

6. **Not considering native requirements:**
   - Identify platform-specific features early
   - Document MethodChannel requirements

## Output Format

The final output should be a Markdown document with:

1. **Front matter** with metadata
2. **Overview** section
3. **Widget architecture** decisions
4. **Constructor parameters**
5. **Layout and spacing** specifications
6. **Typography and colors** specifications
7. **States and variants** documentation
8. **Responsive behavior** notes
9. **Native integration** requirements (if any)
10. **Accessibility** considerations

This specification document will be used by the `flutter-implementation` skill to generate actual Flutter code.
