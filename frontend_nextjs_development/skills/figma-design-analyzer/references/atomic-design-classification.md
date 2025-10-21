# Atomic Design Classification Guide

This guide provides criteria for classifying React components according to Atomic Design principles when extracting from Figma designs.

## Atomic Design Overview

Atomic Design is a methodology for creating design systems with five distinct levels:

1. **Atoms** - Basic building blocks
2. **Molecules** - Simple combinations of atoms
3. **Organisms** - Complex combinations of molecules and atoms
4. **Templates** - Page-level layouts (wireframes)
5. **Pages** - Specific instances of templates with real content

For component libraries, focus primarily on Atoms, Molecules, and Organisms.

## Classification Criteria

### Atoms

**Definition:** The smallest, indivisible UI components that cannot be broken down further without losing meaning.

**Characteristics:**
- Single responsibility
- No internal state (usually)
- Highly reusable
- Self-contained
- Cannot be broken down further

**Examples:**
- Button
- Input field
- Label
- Icon
- Image
- Heading (h1, h2, etc.)
- Paragraph
- Link
- Checkbox
- Radio button
- Badge
- Avatar
- Spinner/Loader

**Figma Indicators:**
- Figma components with no nested components
- Simple, single-purpose elements
- Elements that appear repeatedly across designs
- Base design tokens (colors, typography, spacing)

**React Example:**
```tsx
// Button Atom
export const Button = ({ children, onClick, variant = 'primary' }: Props) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 rounded ${variant === 'primary' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
  >
    {children}
  </button>
);
```

### Molecules

**Definition:** Simple combinations of atoms that work together as a unit.

**Characteristics:**
- Composed of 2-5 atoms
- Has a single, clear purpose
- Still relatively simple
- Reusable across contexts
- May have simple internal logic

**Examples:**
- Search bar (Input + Button)
- Form field (Label + Input + Error message)
- Card header (Heading + Badge)
- Social share buttons (Multiple icon buttons)
- Breadcrumb navigation (Multiple links + separators)
- Input with icon
- Select dropdown with label
- Toast notification (Icon + Text + Close button)

**Figma Indicators:**
- Figma components containing 2-5 child components
- Grouped elements that always appear together
- Repeated patterns across different pages

**React Example:**
```tsx
// SearchBar Molecule
export const SearchBar = ({ onSearch, placeholder }: Props) => (
  <div className="flex gap-2">
    <Input placeholder={placeholder} onChange={handleChange} />
    <Button onClick={onSearch}>Search</Button>
  </div>
);
```

### Organisms

**Definition:** Complex UI components composed of molecules and atoms, forming distinct sections of an interface.

**Characteristics:**
- Composed of multiple molecules and/or atoms
- Complex structure
- May have significant internal logic and state
- Represents a distinct section of the UI
- Often context-specific

**Examples:**
- Header (Logo + Navigation + Search bar + User menu)
- Footer (Multiple link groups + Social icons + Copyright)
- Product card (Image + Title + Description + Price + Button)
- Comment section (Avatar + Name + Timestamp + Text + Action buttons)
- Navigation menu (Multiple links + dropdown menus)
- Form (Multiple form fields + Submit button)
- Modal dialog (Header + Content + Footer with buttons)
- Table with pagination (Table + Pagination controls)
- Sidebar (Logo + Navigation links + User profile)

**Figma Indicators:**
- Figma components with multiple nested components
- Large, complex frames
- Represents a complete UI section
- Contains both structure and content

**React Example:**
```tsx
// ProductCard Organism
export const ProductCard = ({ product }: Props) => (
  <div className="flex flex-col gap-4 p-6 border rounded">
    <Image src={product.image} alt={product.name} />
    <Heading level={3}>{product.name}</Heading>
    <Paragraph>{product.description}</Paragraph>
    <div className="flex items-center justify-between">
      <Badge>{product.price}</Badge>
      <Button onClick={() => addToCart(product)}>Add to Cart</Button>
    </div>
  </div>
);
```

### Templates (Optional)

**Definition:** Page-level layouts that define content structure without actual content.

**Characteristics:**
- Arranges organisms into page layouts
- Uses placeholder content
- Defines grid and spacing
- Reusable across multiple pages

**Examples:**
- Blog post layout template
- Dashboard layout template
- Product page layout template

**Figma Indicators:**
- Full-page frames
- Uses placeholder content (Lorem ipsum, sample images)
- Defines overall page structure

**React Example:**
```tsx
// BlogPostTemplate
export const BlogPostTemplate = ({ header, content, sidebar }: Props) => (
  <div className="grid grid-cols-12 gap-6">
    <header className="col-span-12">{header}</header>
    <main className="col-span-8">{content}</main>
    <aside className="col-span-4">{sidebar}</aside>
  </div>
);
```

### Pages (Optional)

**Definition:** Specific instances of templates with real content.

**Characteristics:**
- Uses actual content
- Represents a specific page in the application
- May include page-specific logic (data fetching, etc.)

**Note:** Pages are typically not part of a component library. They are application-specific implementations.

## Classification Decision Tree

When analyzing a Figma component, ask these questions:

### Is it an Atom?

1. ✅ Can it be broken down further?
   - **NO** → It's an Atom
   - **YES** → Continue

2. ✅ Does it have a single, indivisible purpose?
   - **YES** → It's an Atom
   - **NO** → Continue

### Is it a Molecule?

3. ✅ Is it composed of 2-5 atoms?
   - **YES** → Likely a Molecule
   - **NO** → Continue

4. ✅ Does it serve a single, simple purpose?
   - **YES** → It's a Molecule
   - **NO** → Continue

### Is it an Organism?

5. ✅ Is it composed of multiple molecules and/or atoms?
   - **YES** → It's an Organism

6. ✅ Does it represent a distinct section of the interface?
   - **YES** → It's an Organism

### Special Cases

**Ambiguous cases:**
- If a component could be either an Atom or Molecule, prefer **Atom** if it's highly reusable
- If a component could be either a Molecule or Organism, prefer **Molecule** if it's simple

**Context matters:**
- Classification can vary based on project scope
- What's an Organism in one project might be a Molecule in another (with larger scale)

## Naming Conventions

Follow consistent naming patterns for each category:

### Atoms
```
Button
Input
Label
Icon
Badge
Avatar
Heading
Paragraph
```

### Molecules
```
SearchBar
FormField
InputWithIcon
SocialShareButtons
Breadcrumb
```

### Organisms
```
Header
Footer
ProductCard
CommentSection
NavigationMenu
Sidebar
```

## Directory Structure

Organize components by Atomic Design category:

```
src/
  components/
    atoms/
      Button/
        Button.tsx
        Button.test.tsx
        Button.stories.tsx
    molecules/
      SearchBar/
        SearchBar.tsx
        SearchBar.test.tsx
        SearchBar.stories.tsx
    organisms/
      Header/
        Header.tsx
        Header.test.tsx
        Header.stories.tsx
```

## Analysis Workflow

When extracting components from Figma:

1. **Identify component boundaries**
   - Look for logical groupings
   - Check Figma component instances
   - Identify repeated patterns

2. **Count the atoms**
   - How many basic elements does it contain?
   - 1 atom → Atom
   - 2-5 atoms → Molecule candidate
   - 6+ atoms → Organism candidate

3. **Assess complexity**
   - Simple structure → Atom or Molecule
   - Complex structure → Organism

4. **Check purpose**
   - Single, simple purpose → Atom or Molecule
   - Multiple purposes or section of UI → Organism

5. **Verify reusability**
   - Highly reusable across contexts → Atom or Molecule
   - Context-specific → Organism

6. **Make classification decision**
   - Use the decision tree above
   - Document reasoning if ambiguous

## Common Patterns and Classifications

### Forms

- **Atoms**: Input, Label, Checkbox, Radio, Button
- **Molecules**: FormField (Label + Input + Error)
- **Organisms**: LoginForm (Multiple FormFields + Button)

### Navigation

- **Atoms**: Link, Icon
- **Molecules**: NavItem (Link + Icon)
- **Organisms**: NavigationMenu (Multiple NavItems + Dropdown)

### Cards

- **Atoms**: Image, Heading, Paragraph, Button, Badge
- **Molecules**: CardHeader (Image + Badge), CardFooter (Button)
- **Organisms**: ProductCard (CardHeader + Content + CardFooter)

### Lists

- **Atoms**: ListItem (single item)
- **Molecules**: ListItemWithIcon (Icon + ListItem)
- **Organisms**: UserList (Multiple ListItemWithIcon + Header + Pagination)

## Edge Cases and Guidelines

### When a component feels too simple for Molecule

If a "Molecule" only combines 2 atoms without adding meaningful functionality:
- Consider if it should be an Atom
- Or, accept it as a simple Molecule for consistency

**Example:**
```tsx
// This might feel too simple for a Molecule, but it's valid
const IconButton = ({ icon, onClick }: Props) => (
  <Button onClick={onClick}>
    <Icon name={icon} />
  </Button>
);
```

### When a component feels too complex for Organism

If an "Organism" is extremely complex with many nested components:
- Consider breaking it down into smaller Organisms
- Or, accept it as a complex Organism if it represents a single, cohesive UI section

### Reusing components across categories

It's normal for:
- Organisms to use Molecules
- Molecules to use Atoms
- Organisms to use Atoms directly (skip Molecules if simpler)

**Don't force categorization** - the goal is organization and reusability, not rigid adherence.

## Benefits of Proper Classification

1. **Better organization**: Easy to find components
2. **Improved reusability**: Atoms and Molecules are highly reusable
3. **Easier testing**: Smaller components are easier to test
4. **Consistent design**: Enforces design system patterns
5. **Team communication**: Shared vocabulary for discussing components
6. **Scalability**: Easier to maintain as the system grows

## Tips

- **Start small**: Begin with Atoms, then build up to Molecules and Organisms
- **Be consistent**: Once you classify a pattern, stick with it
- **Document decisions**: If classification is ambiguous, document why you chose a category
- **Iterate**: It's okay to reclassify components as you learn more about the system
- **Prioritize reusability**: When in doubt, prefer smaller, more reusable components
- **Don't over-engineer**: Not every UI element needs to be a separate Atom
- **Use Figma components as hints**: Figma component structure often maps to Atomic Design
