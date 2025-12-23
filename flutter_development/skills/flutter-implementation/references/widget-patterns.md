# Flutter Widget Patterns Guide

Common widget implementation patterns for Flutter development.

## Basic Widget Patterns

### Stateless Widget with Parameters

```dart
class AppCard extends StatelessWidget {
  const AppCard({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.onTap,
    this.padding = const EdgeInsets.all(16),
  });

  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final VoidCallback? onTap;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: padding,
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
        child: Row(
          children: [
            if (leading != null) ...[
              leading!,
              SizedBox(width: 12),
            ],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  if (subtitle != null)
                    Text(
                      subtitle!,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                ],
              ),
            ),
            if (trailing != null) ...[
              SizedBox(width: 12),
              trailing!,
            ],
          ],
        ),
      ),
    );
  }
}
```

### Stateful Widget with Controller

```dart
class AppTextField extends StatefulWidget {
  const AppTextField({
    super.key,
    this.controller,
    this.label,
    this.hint,
    this.errorText,
    this.onChanged,
    this.obscureText = false,
    this.keyboardType,
  });

  final TextEditingController? controller;
  final String? label;
  final String? hint;
  final String? errorText;
  final ValueChanged<String>? onChanged;
  final bool obscureText;
  final TextInputType? keyboardType;

  @override
  State<AppTextField> createState() => _AppTextFieldState();
}

class _AppTextFieldState extends State<AppTextField> {
  late TextEditingController _controller;
  bool _isObscured = true;

  @override
  void initState() {
    super.initState();
    _controller = widget.controller ?? TextEditingController();
    _isObscured = widget.obscureText;
  }

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    }
    super.dispose();
  }

  void _toggleObscure() {
    setState(() {
      _isObscured = !_isObscured;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.label != null) ...[
          Text(
            widget.label!,
            style: Theme.of(context).textTheme.labelMedium,
          ),
          SizedBox(height: 8),
        ],
        TextField(
          controller: _controller,
          obscureText: widget.obscureText && _isObscured,
          keyboardType: widget.keyboardType,
          onChanged: widget.onChanged,
          decoration: InputDecoration(
            hintText: widget.hint,
            errorText: widget.errorText,
            suffixIcon: widget.obscureText
                ? IconButton(
                    icon: Icon(
                      _isObscured ? Icons.visibility : Icons.visibility_off,
                    ),
                    onPressed: _toggleObscure,
                  )
                : null,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
      ],
    );
  }
}
```

## Layout Patterns

### Responsive Layout

```dart
class ResponsiveLayout extends StatelessWidget {
  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    this.desktop,
  });

  final Widget mobile;
  final Widget? tablet;
  final Widget? desktop;

  static const mobileBreakpoint = 600.0;
  static const tabletBreakpoint = 1200.0;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= tabletBreakpoint && desktop != null) {
          return desktop!;
        }
        if (constraints.maxWidth >= mobileBreakpoint && tablet != null) {
          return tablet!;
        }
        return mobile;
      },
    );
  }
}

// Usage
ResponsiveLayout(
  mobile: MobileProductList(),
  tablet: TabletProductGrid(columns: 2),
  desktop: DesktopProductGrid(columns: 4),
)
```

### Sliver Layout

```dart
class ProductListScreen extends StatelessWidget {
  const ProductListScreen({super.key, required this.products});

  final List<Product> products;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 200,
          pinned: true,
          flexibleSpace: FlexibleSpaceBar(
            title: Text('Products'),
            background: Image.asset(
              'assets/header.png',
              fit: BoxFit.cover,
            ),
          ),
        ),
        SliverPadding(
          padding: EdgeInsets.all(16),
          sliver: SliverGrid(
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 16,
              crossAxisSpacing: 16,
              childAspectRatio: 0.75,
            ),
            delegate: SliverChildBuilderDelegate(
              (context, index) => ProductCard(product: products[index]),
              childCount: products.length,
            ),
          ),
        ),
      ],
    );
  }
}
```

## Animation Patterns

### Implicit Animation

```dart
class AnimatedCard extends StatelessWidget {
  const AnimatedCard({
    super.key,
    required this.child,
    this.isSelected = false,
  });

  final Widget child;
  final bool isSelected;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: Duration(milliseconds: 200),
      curve: Curves.easeInOut,
      transform: Matrix4.identity()..scale(isSelected ? 1.05 : 1.0),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(isSelected ? 0.2 : 0.1),
            blurRadius: isSelected ? 16 : 8,
            offset: Offset(0, isSelected ? 8 : 4),
          ),
        ],
      ),
      child: child,
    );
  }
}
```

### Explicit Animation with AnimationController

```dart
class PulseAnimation extends StatefulWidget {
  const PulseAnimation({super.key, required this.child});

  final Widget child;

  @override
  State<PulseAnimation> createState() => _PulseAnimationState();
}

class _PulseAnimationState extends State<PulseAnimation>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: 1000),
      vsync: this,
    );
    _animation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _controller.repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _animation,
      child: widget.child,
    );
  }
}
```

## Form Patterns

### Form with Validation

```dart
class LoginForm extends StatefulWidget {
  const LoginForm({super.key, required this.onSubmit});

  final void Function(String email, String password) onSubmit;

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      widget.onSubmit(
        _emailController.text,
        _passwordController.text,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _emailController,
            decoration: InputDecoration(
              labelText: 'Email',
              border: OutlineInputBorder(),
            ),
            keyboardType: TextInputType.emailAddress,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter your email';
              }
              if (!value.contains('@')) {
                return 'Please enter a valid email';
              }
              return null;
            },
          ),
          SizedBox(height: 16),
          TextFormField(
            controller: _passwordController,
            decoration: InputDecoration(
              labelText: 'Password',
              border: OutlineInputBorder(),
            ),
            obscureText: true,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter your password';
              }
              if (value.length < 8) {
                return 'Password must be at least 8 characters';
              }
              return null;
            },
          ),
          SizedBox(height: 24),
          ElevatedButton(
            onPressed: _submit,
            child: Text('Login'),
          ),
        ],
      ),
    );
  }
}
```

## List Patterns

### Infinite Scroll List

```dart
class InfiniteScrollList extends StatefulWidget {
  const InfiniteScrollList({
    super.key,
    required this.itemBuilder,
    required this.onLoadMore,
    required this.itemCount,
    this.hasMore = true,
  });

  final Widget Function(BuildContext, int) itemBuilder;
  final Future<void> Function() onLoadMore;
  final int itemCount;
  final bool hasMore;

  @override
  State<InfiniteScrollList> createState() => _InfiniteScrollListState();
}

class _InfiniteScrollListState extends State<InfiniteScrollList> {
  final _scrollController = ScrollController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      _loadMore();
    }
  }

  Future<void> _loadMore() async {
    if (_isLoading || !widget.hasMore) return;
    setState(() => _isLoading = true);
    await widget.onLoadMore();
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: _scrollController,
      itemCount: widget.itemCount + (widget.hasMore ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == widget.itemCount) {
          return Center(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            ),
          );
        }
        return widget.itemBuilder(context, index);
      },
    );
  }
}
```

### Grouped List

```dart
class GroupedList<T, G> extends StatelessWidget {
  const GroupedList({
    super.key,
    required this.items,
    required this.groupBy,
    required this.groupBuilder,
    required this.itemBuilder,
    this.separator,
  });

  final List<T> items;
  final G Function(T) groupBy;
  final Widget Function(G group) groupBuilder;
  final Widget Function(T item) itemBuilder;
  final Widget? separator;

  @override
  Widget build(BuildContext context) {
    final groups = <G, List<T>>{};
    for (final item in items) {
      final group = groupBy(item);
      groups.putIfAbsent(group, () => []).add(item);
    }

    return ListView.builder(
      itemCount: groups.length,
      itemBuilder: (context, groupIndex) {
        final group = groups.keys.elementAt(groupIndex);
        final groupItems = groups[group]!;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            groupBuilder(group),
            ...groupItems.map(itemBuilder),
            if (separator != null && groupIndex < groups.length - 1)
              separator!,
          ],
        );
      },
    );
  }
}
```

## Dialog Patterns

### Confirmation Dialog

```dart
class ConfirmationDialog extends StatelessWidget {
  const ConfirmationDialog({
    super.key,
    required this.title,
    required this.content,
    this.confirmText = 'Confirm',
    this.cancelText = 'Cancel',
    this.isDestructive = false,
  });

  final String title;
  final String content;
  final String confirmText;
  final String cancelText;
  final bool isDestructive;

  static Future<bool?> show(
    BuildContext context, {
    required String title,
    required String content,
    String confirmText = 'Confirm',
    String cancelText = 'Cancel',
    bool isDestructive = false,
  }) {
    return showDialog<bool>(
      context: context,
      builder: (context) => ConfirmationDialog(
        title: title,
        content: content,
        confirmText: confirmText,
        cancelText: cancelText,
        isDestructive: isDestructive,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(title),
      content: Text(content),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: Text(cancelText),
        ),
        TextButton(
          onPressed: () => Navigator.of(context).pop(true),
          style: TextButton.styleFrom(
            foregroundColor: isDestructive ? Colors.red : null,
          ),
          child: Text(confirmText),
        ),
      ],
    );
  }
}

// Usage
final confirmed = await ConfirmationDialog.show(
  context,
  title: 'Delete Item',
  content: 'Are you sure you want to delete this item?',
  confirmText: 'Delete',
  isDestructive: true,
);
```

## Error Handling Patterns

### Error Widget with Retry

```dart
class ErrorView extends StatelessWidget {
  const ErrorView({
    super.key,
    required this.message,
    this.onRetry,
    this.icon = Icons.error_outline,
  });

  final String message;
  final VoidCallback? onRetry;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            if (onRetry != null) ...[
              SizedBox(height: 24),
              ElevatedButton(
                onPressed: onRetry,
                child: Text('Retry'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

### Empty State Widget

```dart
class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.title,
    this.subtitle,
    this.icon = Icons.inbox,
    this.action,
    this.actionLabel,
  });

  final String title;
  final String? subtitle;
  final IconData icon;
  final VoidCallback? action;
  final String? actionLabel;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: Colors.grey[400]),
            SizedBox(height: 16),
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            if (subtitle != null) ...[
              SizedBox(height: 8),
              Text(
                subtitle!,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey[600],
                    ),
                textAlign: TextAlign.center,
              ),
            ],
            if (action != null && actionLabel != null) ...[
              SizedBox(height: 24),
              ElevatedButton(
                onPressed: action,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

## Tips

1. **Extract reusable widgets**: If a pattern is used more than twice, create a widget
2. **Use const constructors**: Improves performance
3. **Keep widgets small**: Break complex widgets into smaller pieces
4. **Document public APIs**: Use doc comments for public widgets
5. **Consider accessibility**: Add semantic labels
6. **Handle edge cases**: Empty states, loading, errors
