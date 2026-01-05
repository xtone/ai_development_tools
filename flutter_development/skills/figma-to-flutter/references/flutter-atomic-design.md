# Flutter Atomic Design Classification Guide

This guide provides criteria for classifying Flutter widgets according to Atomic Design principles.

## Atomic Design Overview

Atomic Design is a methodology for creating design systems with five distinct levels:

1. **Atoms** - Basic building blocks
2. **Molecules** - Simple combinations of atoms
3. **Organisms** - Complex combinations of molecules and atoms
4. **Templates** - Page-level layouts (Scaffolds in Flutter)
5. **Pages** - Specific instances of templates with real content

For Flutter widget libraries, focus primarily on Atoms, Molecules, and Organisms.

## Classification Criteria

### Atoms

**Definition:** The smallest, indivisible UI widgets that cannot be broken down further without losing meaning.

**Characteristics:**
- Single responsibility
- Highly reusable
- Self-contained
- Cannot be broken down further
- Typically StatelessWidget

**Flutter Examples:**
- `ElevatedButton`, `TextButton`, `IconButton`
- `TextField`, `TextFormField`
- `Text`, `Icon`
- `Image`, `CircleAvatar`
- `Checkbox`, `Radio`, `Switch`
- `Badge`, `Chip`
- `CircularProgressIndicator`, `LinearProgressIndicator`
- `Divider`

**Custom Atom Example:**
```dart
class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    this.onPressed,
    this.variant = ButtonVariant.primary,
  });

  final String label;
  final VoidCallback? onPressed;
  final ButtonVariant variant;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: _getButtonStyle(variant),
      child: Text(label),
    );
  }
}
```

**Directory:** `lib/presentation/widgets/atoms/`

### Molecules

**Definition:** Simple combinations of atoms that work together as a unit.

**Characteristics:**
- Composed of 2-5 atoms
- Has a single, clear purpose
- Still relatively simple
- Reusable across contexts
- May have simple internal logic

**Flutter Examples:**
- Search bar (TextField + IconButton)
- Form field (Text label + TextField + Text error)
- List tile with icon (Icon + Text + Icon)
- Input with label
- Rating display (Row of Icon atoms)
- Social share button group
- Breadcrumb navigation

**Custom Molecule Example:**
```dart
class SearchBar extends StatelessWidget {
  const SearchBar({
    super.key,
    required this.controller,
    this.onSearch,
    this.hint = 'Search...',
  });

  final TextEditingController controller;
  final VoidCallback? onSearch;
  final String hint;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            decoration: InputDecoration(
              hintText: hint,
              prefixIcon: Icon(Icons.search),
            ),
          ),
        ),
        SizedBox(width: 8),
        IconButton(
          icon: Icon(Icons.search),
          onPressed: onSearch,
        ),
      ],
    );
  }
}
```

**Directory:** `lib/presentation/widgets/molecules/`

### Organisms

**Definition:** Complex UI widgets composed of molecules and atoms, forming distinct sections of an interface.

**Characteristics:**
- Composed of multiple molecules and/or atoms
- Complex structure
- May have significant internal logic and state
- Represents a distinct section of the UI
- Often context-specific

**Flutter Examples:**
- AppBar (with logo, title, actions)
- Navigation drawer
- Product card
- Comment section
- Form (multiple form fields + submit button)
- Modal/Dialog content
- Bottom sheet content
- User profile card
- Settings section

**Custom Organism Example:**
```dart
class ProductCard extends StatelessWidget {
  const ProductCard({
    super.key,
    required this.product,
    this.onAddToCart,
    this.onFavorite,
  });

  final Product product;
  final VoidCallback? onAddToCart;
  final VoidCallback? onFavorite;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image (Atom)
          AspectRatio(
            aspectRatio: 16 / 9,
            child: Image.network(product.imageUrl, fit: BoxFit.cover),
          ),
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Title (Atom)
                Text(
                  product.name,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                SizedBox(height: 8),
                // Price badge (Atom)
                PriceBadge(price: product.price),
                SizedBox(height: 16),
                // Action buttons (Molecule)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    AppButton(
                      label: 'Add to Cart',
                      onPressed: onAddToCart,
                    ),
                    IconButton(
                      icon: Icon(Icons.favorite_border),
                      onPressed: onFavorite,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

**Directory:** `lib/presentation/widgets/organisms/`

### Templates (Scaffolds)

**Definition:** Page-level layouts that define content structure without actual content.

**Characteristics:**
- Arranges organisms into page layouts
- Uses placeholder/slot pattern
- Defines overall structure
- Reusable across multiple pages

**Flutter Example:**
```dart
class MainScaffold extends StatelessWidget {
  const MainScaffold({
    super.key,
    required this.body,
    this.appBar,
    this.bottomNavigationBar,
    this.floatingActionButton,
  });

  final Widget body;
  final PreferredSizeWidget? appBar;
  final Widget? bottomNavigationBar;
  final Widget? floatingActionButton;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar,
      body: SafeArea(child: body),
      bottomNavigationBar: bottomNavigationBar,
      floatingActionButton: floatingActionButton,
    );
  }
}
```

**Directory:** `lib/presentation/templates/`

### Pages (Screens)

**Definition:** Specific instances of templates with real content and state management.

**Characteristics:**
- Uses actual data
- Represents a specific screen in the application
- May include page-specific logic (data fetching, etc.)
- Often uses Riverpod for state management

**Flutter Example:**
```dart
@RoutePage()
class ProductListScreen extends ConsumerWidget {
  const ProductListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final products = ref.watch(productsProvider);

    return MainScaffold(
      appBar: AppBar(title: Text('Products')),
      body: products.when(
        data: (items) => GridView.builder(
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
          ),
          itemCount: items.length,
          itemBuilder: (context, index) => ProductCard(
            product: items[index],
            onAddToCart: () => ref.read(cartProvider.notifier).add(items[index]),
          ),
        ),
        loading: () => Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
```

**Directory:** `lib/presentation/screens/[feature]/`

## Classification Decision Tree

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

## Flutter Directory Structure

```
lib/
  presentation/
    widgets/
      atoms/
        app_button.dart
        app_text_field.dart
        app_icon.dart
        price_badge.dart
      molecules/
        search_bar.dart
        form_field.dart
        rating_display.dart
      organisms/
        product_card.dart
        app_header.dart
        navigation_drawer.dart
        comment_section.dart
    templates/
      main_scaffold.dart
      auth_scaffold.dart
    screens/
      home/
        home_screen.dart
        home_view_model.dart
      product/
        product_list_screen.dart
        product_detail_screen.dart
```

## Widget Composition Patterns

### Atoms → Molecules
```dart
// Atoms: Icon, Text
// Molecule: IconLabel
class IconLabel extends StatelessWidget {
  const IconLabel({
    super.key,
    required this.icon,
    required this.label,
    this.spacing = 8,
  });

  final IconData icon;
  final String label;
  final double spacing;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon),
        SizedBox(width: spacing),
        Text(label),
      ],
    );
  }
}
```

### Molecules → Organisms
```dart
// Molecules: IconLabel, AppButton
// Organism: ActionCard
class ActionCard extends StatelessWidget {
  const ActionCard({
    super.key,
    required this.icon,
    required this.title,
    required this.description,
    this.onAction,
  });

  final IconData icon;
  final String title;
  final String description;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            IconLabel(icon: icon, label: title),
            SizedBox(height: 8),
            Text(description),
            SizedBox(height: 16),
            AppButton(
              label: 'Learn More',
              onPressed: onAction,
            ),
          ],
        ),
      ),
    );
  }
}
```

## Common Flutter Patterns by Category

### Forms

- **Atoms**: TextField, Checkbox, Radio, Switch
- **Molecules**: FormField (Label + TextField + Error)
- **Organisms**: LoginForm (Multiple FormFields + Button)

### Navigation

- **Atoms**: Icon, Text
- **Molecules**: NavItem (Icon + Text)
- **Organisms**: BottomNavigationBar, NavigationDrawer

### Cards

- **Atoms**: Image, Text, Icon, Button
- **Molecules**: CardHeader, CardFooter
- **Organisms**: ProductCard, UserCard, ArticleCard

### Lists

- **Atoms**: Text, Icon, Avatar
- **Molecules**: ListTile (Avatar + Text + Action)
- **Organisms**: UserList (Header + Multiple ListTiles + Pagination)

## Naming Conventions

### Atoms
```
AppButton
AppTextField
AppIcon
AppImage
PriceBadge
StatusChip
```

### Molecules
```
SearchBar
FormField
IconLabel
RatingDisplay
SocialShareButtons
```

### Organisms
```
ProductCard
UserProfileCard
CommentSection
NavigationHeader
SettingsSection
```

## Tips

1. **Start small**: Begin with Atoms, then build up
2. **Be consistent**: Once you classify a pattern, stick with it
3. **Keep atoms pure**: No business logic in atoms
4. **Molecules are simple**: If it's getting complex, it's probably an Organism
5. **Organisms can use atoms directly**: Skip molecules if simpler
6. **Use const constructors**: For static widgets
7. **Consider reusability**: Atoms and Molecules should be highly reusable
8. **Document decisions**: If classification is ambiguous, document why

## Edge Cases

### When a widget feels too simple for Molecule

If a "Molecule" only combines 2 atoms without adding meaningful functionality:
- Consider if it should be an Atom
- Or accept it as a simple Molecule for consistency

### When a widget feels too complex for Organism

If an "Organism" is extremely complex:
- Consider breaking it down into smaller Organisms
- Or accept it as a complex Organism if it represents a single, cohesive UI section

### Reusing across categories

It's normal for:
- Organisms to use Molecules
- Molecules to use Atoms
- Organisms to use Atoms directly (skip Molecules if simpler)

**Don't force categorization** - the goal is organization and reusability.
