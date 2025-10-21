# Semantic HTML Guide

This guide provides recommendations for choosing appropriate HTML tags when converting Figma designs to React components, ensuring accessibility and semantic correctness.

## Why Semantic HTML Matters

1. **Accessibility**: Screen readers and assistive technologies rely on semantic HTML
2. **SEO**: Search engines understand content structure better
3. **Maintainability**: Code is more readable and self-documenting
4. **Styling**: Easier to style with CSS selectors
5. **Future-proofing**: Standards-compliant code ages better

## Semantic HTML Elements

### Document Structure

#### `<header>`

**Use for:**
- Site header
- Page header
- Section header
- Article header

**Don't use for:**
- Every heading (use h1-h6 instead)
- Random containers

**Figma Indicators:**
- Top section of a page or component
- Contains logo, navigation, or title
- Labeled "Header" in Figma

**Example:**
```tsx
<header className="flex items-center justify-between p-4">
  <img src="logo.png" alt="Company Logo" />
  <nav>...</nav>
</header>
```

#### `<nav>`

**Use for:**
- Primary navigation
- Breadcrumb navigation
- Table of contents
- Pagination

**Don't use for:**
- Social media links (use `<ul>` instead)
- Footer links (unless it's primary navigation)

**Figma Indicators:**
- Navigation menu
- Labeled "Navigation" or "Nav" in Figma
- Contains multiple links to different sections

**Example:**
```tsx
<nav className="flex gap-4">
  <a href="/">Home</a>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
</nav>
```

#### `<main>`

**Use for:**
- Main content of the page
- The primary content area

**Don't use for:**
- Sidebars
- Headers or footers
- Navigation

**Rules:**
- Only one `<main>` per page
- Should not be inside `<article>`, `<aside>`, `<footer>`, `<header>`, or `<nav>`

**Figma Indicators:**
- Central content area of a page
- Labeled "Main Content" or "Content" in Figma

**Example:**
```tsx
<main className="container mx-auto p-8">
  {/* Primary page content */}
</main>
```

#### `<aside>`

**Use for:**
- Sidebars
- Related content
- Callout boxes
- Pull quotes
- Advertising

**Don't use for:**
- Main content

**Figma Indicators:**
- Sidebar sections
- "Related articles" sections
- Callout boxes
- Labeled "Sidebar" or "Aside" in Figma

**Example:**
```tsx
<aside className="w-64 bg-gray-100 p-4">
  <h3>Related Articles</h3>
  <ul>...</ul>
</aside>
```

#### `<footer>`

**Use for:**
- Site footer
- Page footer
- Section footer
- Article footer

**Don't use for:**
- Every bottom section (assess if it's truly footer content)

**Figma Indicators:**
- Bottom section of a page or component
- Contains copyright, links, contact info
- Labeled "Footer" in Figma

**Example:**
```tsx
<footer className="bg-gray-900 text-white p-8">
  <p>&copy; 2024 Company Name</p>
</footer>
```

#### `<section>`

**Use for:**
- Thematic groupings of content
- Chapters or sections of a page
- Tabbed content areas

**Don't use for:**
- Generic containers (use `<div>` instead)

**Rule:** Each `<section>` should have a heading (h1-h6)

**Figma Indicators:**
- Distinct content sections on a page
- Sections with headings
- Labeled "Section" in Figma

**Example:**
```tsx
<section className="py-16">
  <h2>Our Services</h2>
  <p>...</p>
</section>
```

#### `<article>`

**Use for:**
- Blog posts
- News articles
- Forum posts
- Comments
- Product cards (in some contexts)
- Independent, self-contained content

**Don't use for:**
- Generic content containers

**Rule:** Content inside `<article>` should make sense independently

**Figma Indicators:**
- Blog post layouts
- News article cards
- Comment sections
- Product cards

**Example:**
```tsx
<article className="border rounded p-6">
  <h2>Article Title</h2>
  <p className="text-gray-600">Published on ...</p>
  <p>Article content...</p>
</article>
```

### Content

#### Headings: `<h1>` to `<h6>`

**Use for:**
- Section titles
- Content hierarchy

**Don't use for:**
- Styling purposes (use CSS instead)

**Rules:**
- Only one `<h1>` per page (page title)
- Don't skip levels (h1 → h2 → h3, not h1 → h3)
- Use in descending order

**Figma Indicators:**
- Text labeled "Heading", "Title", "H1", "H2", etc.
- Large, bold text at the start of sections
- Text styles named "Heading 1", "Heading 2", etc.

**Example:**
```tsx
<h1 className="text-4xl font-bold">Page Title</h1>
<section>
  <h2 className="text-3xl font-semibold">Section Title</h2>
  <h3 className="text-2xl font-medium">Subsection Title</h3>
</section>
```

#### `<p>`

**Use for:**
- Paragraphs of text
- Body content

**Don't use for:**
- Headings
- Lists
- Single words or short phrases (use `<span>` instead)

**Example:**
```tsx
<p className="text-base leading-relaxed">
  This is a paragraph of text...
</p>
```

#### `<a>`

**Use for:**
- Hyperlinks
- Navigation links

**Don't use for:**
- Buttons (use `<button>` instead)

**Rule:** Always include `href` attribute

**Accessibility:**
- Use descriptive link text (not "click here")
- Add `rel="noopener noreferrer"` for external links with `target="_blank"`

**Example:**
```tsx
<a href="/about" className="text-blue-600 hover:underline">
  Learn more about our company
</a>

{/* External link */}
<a
  href="https://example.com"
  target="_blank"
  rel="noopener noreferrer"
  className="text-blue-600"
>
  Visit example.com
</a>
```

#### `<button>`

**Use for:**
- Interactive buttons
- Form submissions
- Actions that don't navigate

**Don't use for:**
- Links (use `<a>` instead)

**Rule:** Always include `type` attribute (`button`, `submit`, or `reset`)

**Example:**
```tsx
<button
  type="button"
  onClick={handleClick}
  className="px-4 py-2 bg-blue-500 text-white rounded"
>
  Click Me
</button>
```

### Lists

#### `<ul>` (Unordered List)

**Use for:**
- Lists without order
- Navigation menus (within `<nav>`)
- Feature lists

**Example:**
```tsx
<ul className="list-disc list-inside">
  <li>First item</li>
  <li>Second item</li>
  <li>Third item</li>
</ul>
```

#### `<ol>` (Ordered List)

**Use for:**
- Lists with order/sequence
- Step-by-step instructions
- Rankings

**Example:**
```tsx
<ol className="list-decimal list-inside">
  <li>First step</li>
  <li>Second step</li>
  <li>Third step</li>
</ol>
```

#### `<dl>`, `<dt>`, `<dd>` (Definition List)

**Use for:**
- Term-definition pairs
- Metadata
- Key-value pairs

**Example:**
```tsx
<dl>
  <dt className="font-semibold">Name</dt>
  <dd className="ml-4">John Doe</dd>

  <dt className="font-semibold">Email</dt>
  <dd className="ml-4">john@example.com</dd>
</dl>
```

### Forms

#### `<form>`

**Use for:**
- All form inputs
- Search bars
- Login forms

**Rule:** Always include `action` or handle submit with JavaScript

**Example:**
```tsx
<form onSubmit={handleSubmit} className="flex flex-col gap-4">
  {/* form fields */}
</form>
```

#### `<label>`

**Use for:**
- Input labels

**Rule:** Always associate with an input using `htmlFor` or by wrapping

**Example:**
```tsx
{/* Using htmlFor */}
<label htmlFor="email" className="font-medium">
  Email
</label>
<input id="email" type="email" />

{/* Wrapping */}
<label className="flex flex-col gap-1">
  <span className="font-medium">Email</span>
  <input type="email" />
</label>
```

#### `<input>`

**Use for:**
- Text input
- Checkboxes
- Radio buttons
- File uploads
- Dates
- Many other input types

**Rule:** Always include `type` attribute

**Example:**
```tsx
<input
  type="text"
  placeholder="Enter your name"
  className="border rounded px-3 py-2"
/>
```

#### `<textarea>`

**Use for:**
- Multi-line text input

**Example:**
```tsx
<textarea
  rows={4}
  placeholder="Enter your message"
  className="border rounded px-3 py-2"
/>
```

#### `<select>`

**Use for:**
- Dropdown menus

**Example:**
```tsx
<select className="border rounded px-3 py-2">
  <option value="">Choose an option</option>
  <option value="1">Option 1</option>
  <option value="2">Option 2</option>
</select>
```

#### `<fieldset>` and `<legend>`

**Use for:**
- Grouping related form fields
- Radio button groups
- Checkbox groups

**Example:**
```tsx
<fieldset className="border rounded p-4">
  <legend className="font-semibold px-2">Choose a size</legend>
  <label>
    <input type="radio" name="size" value="small" /> Small
  </label>
  <label>
    <input type="radio" name="size" value="large" /> Large
  </label>
</fieldset>
```

### Media

#### `<img>`

**Use for:**
- Images

**Rules:**
- Always include `alt` attribute (describe the image or use empty string for decorative)
- Always include `src` attribute

**Example:**
```tsx
{/* Content image */}
<img
  src="/photo.jpg"
  alt="A scenic mountain landscape"
  className="w-full rounded"
/>

{/* Decorative image */}
<img
  src="/decoration.png"
  alt=""
  className="w-8 h-8"
/>
```

#### `<figure>` and `<figcaption>`

**Use for:**
- Images with captions
- Code snippets with descriptions
- Diagrams

**Example:**
```tsx
<figure>
  <img src="/chart.png" alt="Sales data chart" />
  <figcaption className="text-sm text-gray-600">
    Figure 1: Sales data for Q4 2024
  </figcaption>
</figure>
```

#### `<video>` and `<audio>`

**Use for:**
- Video and audio content

**Example:**
```tsx
<video controls className="w-full">
  <source src="/video.mp4" type="video/mp4" />
  Your browser does not support video.
</video>
```

### Text-level Semantics

#### `<strong>` vs `<b>`

- `<strong>`: Use for **important** text (semantic)
- `<b>`: Use for **stylistic** bold text (rare, prefer CSS)

**Prefer `<strong>`** in most cases.

#### `<em>` vs `<i>`

- `<em>`: Use for **emphasized** text (semantic)
- `<i>`: Use for **stylistic** italic text (rare, prefer CSS)

**Prefer `<em>`** in most cases.

#### `<span>`

**Use for:**
- Inline text that needs styling
- Wrapping text for JavaScript manipulation

**Don't use for:**
- Semantic meaning (use `<strong>`, `<em>`, etc.)

**Example:**
```tsx
<p>
  This is <span className="text-blue-600">highlighted</span> text.
</p>
```

#### `<div>`

**Use for:**
- Generic containers
- Layout purposes

**Don't use for:**
- Semantic meaning (use `<section>`, `<article>`, etc. instead)

**Example:**
```tsx
<div className="flex gap-4">
  {/* content */}
</div>
```

## Decision Tree: Choosing the Right Tag

### For Content Sections

```
Is it the main content of the page?
├─ YES → <main>
└─ NO
   ├─ Is it a navigation menu?
   │  └─ YES → <nav>
   └─ NO
      ├─ Is it a sidebar or related content?
      │  └─ YES → <aside>
      └─ NO
         ├─ Is it a header section?
         │  └─ YES → <header>
         └─ NO
            ├─ Is it a footer section?
            │  └─ YES → <footer>
            └─ NO
               ├─ Is it a self-contained article or post?
               │  └─ YES → <article>
               └─ NO
                  ├─ Is it a thematic section with a heading?
                  │  └─ YES → <section>
                  └─ NO → <div>
```

### For Interactive Elements

```
Is it a link that navigates somewhere?
├─ YES → <a href="...">
└─ NO
   └─ Is it a button that performs an action?
      └─ YES → <button type="button">
```

### For Text

```
Is it a heading?
├─ YES → <h1> to <h6> (based on hierarchy)
└─ NO
   ├─ Is it a paragraph?
   │  └─ YES → <p>
   └─ NO
      ├─ Is it emphasized/important?
      │  ├─ Important → <strong>
      │  └─ Emphasized → <em>
      └─ NO → <span>
```

## Common Figma → HTML Mappings

| Figma Element | Semantic HTML | Notes |
|--------------|---------------|-------|
| Frame labeled "Header" | `<header>` | Site/page header |
| Frame labeled "Nav" | `<nav>` | Navigation menu |
| Frame labeled "Main" | `<main>` | Primary content |
| Frame labeled "Sidebar" | `<aside>` | Sidebar content |
| Frame labeled "Footer" | `<footer>` | Site/page footer |
| Frame labeled "Section" | `<section>` | Content section |
| Frame labeled "Card" | `<article>` or `<div>` | Depends on content |
| Text layer "Heading" | `<h1>` to `<h6>` | Based on hierarchy |
| Text layer "Body" | `<p>` | Paragraph text |
| Button component | `<button>` | Interactive button |
| Link component | `<a>` | Hyperlink |
| Image layer | `<img>` | Image element |
| Auto Layout (vertical) | `<div className="flex flex-col">` | Layout container |
| Form | `<form>` | Form container |
| Input field | `<input>` | Form input |

## Accessibility Considerations

### ARIA Attributes

When semantic HTML is not enough, use ARIA attributes:

```tsx
{/* Button that controls a menu */}
<button
  type="button"
  aria-haspopup="true"
  aria-expanded={isOpen}
>
  Menu
</button>

{/* Navigation landmark */}
<nav aria-label="Primary navigation">
  {/* links */}
</nav>

{/* Region landmark */}
<section aria-labelledby="section-title">
  <h2 id="section-title">Section Title</h2>
</section>
```

### Focus Management

Ensure interactive elements are keyboard accessible:

```tsx
{/* Custom clickable div (avoid if possible) */}
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyPress={handleKeyPress}
>
  Click me
</div>

{/* Better: use semantic button */}
<button type="button" onClick={handleClick}>
  Click me
</button>
```

## Common Mistakes

1. **Using `<div>` for everything**
   - ❌ `<div className="header">...</div>`
   - ✅ `<header>...</header>`

2. **Using `<a>` for buttons**
   - ❌ `<a onClick={handleClick}>Submit</a>`
   - ✅ `<button type="button" onClick={handleClick}>Submit</button>`

3. **Using `<button>` for links**
   - ❌ `<button onClick={() => navigate('/about')}>About</button>`
   - ✅ `<a href="/about">About</a>`

4. **Skipping heading levels**
   - ❌ `<h1>Title</h1><h3>Subtitle</h3>`
   - ✅ `<h1>Title</h1><h2>Subtitle</h2>`

5. **Multiple `<main>` elements**
   - ❌ Two `<main>` on the same page
   - ✅ Only one `<main>` per page

6. **Empty `alt` attributes on content images**
   - ❌ `<img src="chart.jpg" alt="" />`
   - ✅ `<img src="chart.jpg" alt="Sales chart showing growth" />`

7. **Using `<br>` for spacing**
   - ❌ `<p>Text<br><br><br>More text</p>`
   - ✅ Use CSS margin/padding instead

## Tips

- **Use semantic HTML first**: Before adding ARIA, check if semantic HTML solves the problem
- **Test with screen readers**: Use tools like VoiceOver (Mac) or NVDA (Windows)
- **Validate HTML**: Use W3C validator to check for errors
- **Think about structure**: How would this content be read aloud?
- **Consult ARIA authoring practices**: https://www.w3.org/WAI/ARIA/apg/
- **When in doubt, use `<div>` or `<span>`**: Don't force semantic meaning where it doesn't exist
