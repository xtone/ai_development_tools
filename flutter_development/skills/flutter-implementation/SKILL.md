---
name: flutter-implementation
description: Generate production-ready Flutter widgets from design specifications. Use this skill when you have a design specification document and need to create Flutter/Dart widgets with proper state management, Riverpod integration, widget tests, and native platform integration when required.
---

# Flutter Implementation Skill

## Overview

Generate production-ready Flutter widgets from design specifications created by the `figma-to-flutter` skill. This skill focuses on creating well-structured, testable, and maintainable Flutter code that follows best practices.

**Use this skill when:**
- You have a design specification document from `figma-to-flutter`
- Need to implement Flutter widgets with proper architecture
- Require Riverpod state management integration
- Need widget tests for the implementation
- Require native platform integration (iOS/Android)

## Prerequisites

Before using this skill, ensure you have:
1. A design specification document (from `figma-to-flutter` or manually created)
2. Understanding of the project's existing architecture
3. Knowledge of the project's design system/theme (if exists)

## Core Workflow

### Step 1: Analyze the Design Specification

Read and understand the design specification:

1. **Extract widget information:**
   - Widget name
   - Atomic category (Atom/Molecule/Organism)
   - Widget type (StatelessWidget/StatefulWidget/ConsumerWidget)

2. **Identify dependencies:**
   - Required packages
   - Theme dependencies
   - State management needs
   - Native platform requirements

3. **Understand the widget structure:**
   - Constructor parameters
   - Layout hierarchy
   - Child widgets

### Step 2: Set Up File Structure

Create files based on atomic category:

```
lib/presentation/widgets/
├── atoms/
│   └── [widget_name]/
│       ├── [widget_name].dart
│       └── [widget_name]_test.dart
├── molecules/
│   └── [widget_name]/
│       ├── [widget_name].dart
│       └── [widget_name]_test.dart
└── organisms/
    └── [widget_name]/
        ├── [widget_name].dart
        └── [widget_name]_test.dart
```

For screens:
```
lib/presentation/screens/
└── [feature]/
    ├── [screen_name]_screen.dart
    ├── [screen_name]_view_model.dart
    └── [screen_name]_ui_state.dart
```

### Step 3: Generate Widget Code

#### For StatelessWidget (No State)

```dart
import 'package:flutter/material.dart';

/// {@template widget_name}
/// A brief description of what this widget does.
/// {@endtemplate}
class WidgetName extends StatelessWidget {
  /// {@macro widget_name}
  const WidgetName({
    super.key,
    required this.label,
    this.onPressed,
    this.variant = WidgetVariant.primary,
  });

  /// The text displayed on the widget.
  final String label;

  /// Called when the widget is pressed.
  final VoidCallback? onPressed;

  /// The visual variant of the widget.
  final WidgetVariant variant;

  @override
  Widget build(BuildContext context) {
    return Container(
      // Implementation based on design spec
    );
  }
}

/// Variants for [WidgetName].
enum WidgetVariant {
  /// Primary variant with filled background.
  primary,

  /// Secondary variant with outlined style.
  secondary,

  /// Tertiary variant with text-only style.
  tertiary,
}
```

#### For StatefulWidget (With Local State)

```dart
import 'package:flutter/material.dart';

/// {@template widget_name}
/// A brief description of what this widget does.
/// {@endtemplate}
class WidgetName extends StatefulWidget {
  /// {@macro widget_name}
  const WidgetName({
    super.key,
    required this.initialValue,
    this.onChanged,
  });

  /// The initial value for the widget.
  final String initialValue;

  /// Called when the value changes.
  final ValueChanged<String>? onChanged;

  @override
  State<WidgetName> createState() => _WidgetNameState();
}

class _WidgetNameState extends State<WidgetName> {
  late String _value;

  @override
  void initState() {
    super.initState();
    _value = widget.initialValue;
  }

  void _handleChange(String newValue) {
    setState(() {
      _value = newValue;
    });
    widget.onChanged?.call(newValue);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      // Implementation based on design spec
    );
  }
}
```

#### For ConsumerWidget (With Riverpod)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// {@template widget_name}
/// A brief description of what this widget does.
/// {@endtemplate}
class WidgetName extends ConsumerWidget {
  /// {@macro widget_name}
  const WidgetName({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(widgetStateProvider);

    return Container(
      // Implementation based on design spec
    );
  }
}
```

#### For HooksConsumerWidget (With Riverpod + Hooks)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

/// {@template widget_name}
/// A brief description of what this widget does.
/// {@endtemplate}
class WidgetName extends HookConsumerWidget {
  /// {@macro widget_name}
  const WidgetName({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final controller = useTextEditingController();
    final state = ref.watch(widgetStateProvider);

    return Container(
      // Implementation based on design spec
    );
  }
}
```

### Step 4: Implement Layout

Based on the design specification's layout section:

1. **Read layout mapping guide:**
   ```
   Read references/widget-patterns.md
   ```

2. **Apply layout widgets:**

```dart
// For vertical arrangement
Column(
  mainAxisAlignment: MainAxisAlignment.start,
  crossAxisAlignment: CrossAxisAlignment.stretch,
  children: [
    // Children with SizedBox for spacing
  ],
)

// For horizontal arrangement
Row(
  mainAxisAlignment: MainAxisAlignment.spaceBetween,
  crossAxisAlignment: CrossAxisAlignment.center,
  children: [
    // Children
  ],
)

// For overlapping elements
Stack(
  children: [
    // Background
    Positioned(
      top: 16,
      right: 16,
      child: // Overlay widget
    ),
  ],
)
```

### Step 5: Apply Styling

Based on the design specification's styling sections:

```dart
Container(
  padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
  decoration: BoxDecoration(
    color: Color(0xFF2196F3),
    borderRadius: BorderRadius.circular(12),
    boxShadow: [
      BoxShadow(
        color: Color(0x1A000000),
        blurRadius: 8,
        offset: Offset(0, 4),
      ),
    ],
  ),
  child: Text(
    label,
    style: TextStyle(
      fontFamily: 'Roboto',
      fontSize: 16,
      fontWeight: FontWeight.w600,
      color: Colors.white,
    ),
  ),
)
```

### Step 6: Handle States and Variants

Implement all states from the design specification:

```dart
class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    this.onPressed,
    this.variant = ButtonVariant.primary,
    this.size = ButtonSize.medium,
    this.isLoading = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final ButtonVariant variant;
  final ButtonSize size;
  final bool isLoading;

  bool get _isDisabled => onPressed == null || isLoading;

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: _isDisabled ? 0.5 : 1.0,
      child: InkWell(
        onTap: _isDisabled ? null : onPressed,
        borderRadius: BorderRadius.circular(_borderRadius),
        child: Container(
          padding: _padding,
          decoration: BoxDecoration(
            color: _backgroundColor,
            borderRadius: BorderRadius.circular(_borderRadius),
            border: _border,
          ),
          child: isLoading
              ? SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: _textColor,
                  ),
                )
              : Text(
                  label,
                  style: TextStyle(
                    fontSize: _fontSize,
                    fontWeight: FontWeight.w600,
                    color: _textColor,
                  ),
                ),
        ),
      ),
    );
  }

  EdgeInsets get _padding {
    switch (size) {
      case ButtonSize.small:
        return EdgeInsets.symmetric(horizontal: 16, vertical: 8);
      case ButtonSize.medium:
        return EdgeInsets.symmetric(horizontal: 24, vertical: 12);
      case ButtonSize.large:
        return EdgeInsets.symmetric(horizontal: 32, vertical: 16);
    }
  }

  double get _fontSize {
    switch (size) {
      case ButtonSize.small:
        return 14;
      case ButtonSize.medium:
        return 16;
      case ButtonSize.large:
        return 18;
    }
  }

  double get _borderRadius => 8;

  Color get _backgroundColor {
    switch (variant) {
      case ButtonVariant.primary:
        return Color(0xFF2196F3);
      case ButtonVariant.secondary:
        return Colors.white;
      case ButtonVariant.tertiary:
        return Colors.transparent;
    }
  }

  Color get _textColor {
    switch (variant) {
      case ButtonVariant.primary:
        return Colors.white;
      case ButtonVariant.secondary:
      case ButtonVariant.tertiary:
        return Color(0xFF2196F3);
    }
  }

  Border? get _border {
    switch (variant) {
      case ButtonVariant.secondary:
        return Border.all(color: Color(0xFF2196F3), width: 1);
      default:
        return null;
    }
  }
}

enum ButtonVariant { primary, secondary, tertiary }
enum ButtonSize { small, medium, large }
```

### Step 7: Add Accessibility

Implement accessibility features:

```dart
Semantics(
  label: 'Submit button',
  button: true,
  enabled: !_isDisabled,
  child: InkWell(
    onTap: onPressed,
    child: // Widget content
  ),
)
```

For custom widgets:
```dart
class AppButton extends StatelessWidget {
  // ...

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: semanticLabel ?? label,
      button: true,
      enabled: !_isDisabled,
      child: ExcludeSemantics(
        child: // Visual widget
      ),
    );
  }
}
```

### Step 8: Generate Widget Tests

Create comprehensive widget tests:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/presentation/widgets/atoms/app_button/app_button.dart';

void main() {
  group('AppButton', () {
    testWidgets('renders label correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              label: 'Test Button',
              onPressed: () {},
            ),
          ),
        ),
      );

      expect(find.text('Test Button'), findsOneWidget);
    });

    testWidgets('calls onPressed when tapped', (tester) async {
      var pressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              label: 'Test',
              onPressed: () => pressed = true,
            ),
          ),
        ),
      );

      await tester.tap(find.byType(AppButton));
      expect(pressed, isTrue);
    });

    testWidgets('shows loading indicator when isLoading is true', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              label: 'Test',
              onPressed: () {},
              isLoading: true,
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Test'), findsNothing);
    });

    testWidgets('is disabled when onPressed is null', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              label: 'Test',
              onPressed: null,
            ),
          ),
        ),
      );

      final opacity = tester.widget<Opacity>(find.byType(Opacity));
      expect(opacity.opacity, 0.5);
    });

    group('variants', () {
      testWidgets('primary variant has correct background color', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: AppButton(
                label: 'Test',
                onPressed: () {},
                variant: ButtonVariant.primary,
              ),
            ),
          ),
        );

        final container = tester.widget<Container>(
          find.descendant(
            of: find.byType(AppButton),
            matching: find.byType(Container),
          ),
        );
        final decoration = container.decoration as BoxDecoration;
        expect(decoration.color, Color(0xFF2196F3));
      });

      testWidgets('secondary variant has border', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: AppButton(
                label: 'Test',
                onPressed: () {},
                variant: ButtonVariant.secondary,
              ),
            ),
          ),
        );

        final container = tester.widget<Container>(
          find.descendant(
            of: find.byType(AppButton),
            matching: find.byType(Container),
          ),
        );
        final decoration = container.decoration as BoxDecoration;
        expect(decoration.border, isNotNull);
      });
    });

    group('sizes', () {
      testWidgets('small size has correct padding', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: AppButton(
                label: 'Test',
                onPressed: () {},
                size: ButtonSize.small,
              ),
            ),
          ),
        );

        final container = tester.widget<Container>(
          find.descendant(
            of: find.byType(AppButton),
            matching: find.byType(Container),
          ),
        );
        expect(
          container.padding,
          EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        );
      });
    });
  });
}
```

### Step 9: Handle Native Platform Integration

When the design specification indicates native platform requirements:

1. **Read native integration guide:**
   ```
   Read references/native-integration-guide.md
   ```

2. **Identify the integration pattern:**
   - **MethodChannel**: For calling native code
   - **EventChannel**: For streaming data from native
   - **Platform Views**: For embedding native UI

3. **Create platform interface:**

```dart
// lib/services/camera_service.dart
import 'package:flutter/services.dart';

class CameraService {
  static const _channel = MethodChannel('app.example/camera');

  Future<String?> takePicture() async {
    try {
      final result = await _channel.invokeMethod<String>('takePicture');
      return result;
    } on PlatformException catch (e) {
      throw CameraException(e.message ?? 'Unknown error');
    }
  }
}

class CameraException implements Exception {
  final String message;
  CameraException(this.message);
}
```

4. **Document native implementation requirements:**

```markdown
## Native Implementation Required

### iOS (Swift)
Use the `ios-development` skills for implementation:
- `/swiftui-components` for camera UI
- Reference: AVFoundation for camera access

### Android (Kotlin)
Create MethodChannel handler:
- Use Camera2 API
- Handle permissions
```

5. **Recommend related skills:**
   - For iOS: `ios-development/swiftui-components`
   - For Android: Reference Android development patterns

### Step 10: Create Screen Implementation (For Pages)

For screen-level widgets with MVVM pattern:

**UIState (Immutable State Class):**
```dart
// lib/presentation/screens/product/product_list_ui_state.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'product_list_ui_state.freezed.dart';

@freezed
class ProductListUIState with _$ProductListUIState {
  const factory ProductListUIState({
    @Default([]) List<Product> products,
    @Default(false) bool isLoading,
    String? error,
    @Default('') String searchQuery,
  }) = _ProductListUIState;
}
```

**ViewModel (StateNotifier):**
```dart
// lib/presentation/screens/product/product_list_view_model.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

final productListViewModelProvider =
    StateNotifierProvider<ProductListViewModel, ProductListUIState>((ref) {
  return ProductListViewModel(ref.read(productRepositoryProvider));
});

class ProductListViewModel extends StateNotifier<ProductListUIState> {
  ProductListViewModel(this._repository) : super(const ProductListUIState());

  final ProductRepository _repository;

  Future<void> loadProducts() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final products = await _repository.getProducts();
      state = state.copyWith(products: products, isLoading: false);
    } catch (e) {
      state = state.copyWith(error: e.toString(), isLoading: false);
    }
  }

  void search(String query) {
    state = state.copyWith(searchQuery: query);
    // Implement search logic
  }
}
```

**Screen Widget:**
```dart
// lib/presentation/screens/product/product_list_screen.dart
import 'package:auto_route/auto_route.dart';
import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

@RoutePage()
class ProductListScreen extends HookConsumerWidget {
  const ProductListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(productListViewModelProvider);
    final viewModel = ref.read(productListViewModelProvider.notifier);

    useEffect(() {
      viewModel.loadProducts();
      return null;
    }, []);

    return Scaffold(
      appBar: AppBar(
        title: Text('Products'),
        actions: [
          IconButton(
            icon: Icon(Icons.search),
            onPressed: () => _showSearch(context),
          ),
        ],
      ),
      body: _buildBody(state),
    );
  }

  Widget _buildBody(ProductListUIState state) {
    if (state.isLoading) {
      return Center(child: CircularProgressIndicator());
    }

    if (state.error != null) {
      return Center(child: Text('Error: ${state.error}'));
    }

    if (state.products.isEmpty) {
      return Center(child: Text('No products found'));
    }

    return GridView.builder(
      padding: EdgeInsets.all(16),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 16,
        crossAxisSpacing: 16,
        childAspectRatio: 0.75,
      ),
      itemCount: state.products.length,
      itemBuilder: (context, index) => ProductCard(
        product: state.products[index],
      ),
    );
  }

  void _showSearch(BuildContext context) {
    // Implement search modal
  }
}
```

## Best Practices

1. **Use const constructors:**
   ```dart
   const AppButton({super.key, required this.label});
   ```

2. **Document public APIs:**
   ```dart
   /// {@template app_button}
   /// A customizable button widget.
   /// {@endtemplate}
   ```

3. **Follow Flutter naming conventions:**
   - Classes: PascalCase
   - Variables/methods: camelCase
   - Files: snake_case

4. **Keep widgets focused:**
   - Single responsibility
   - Extract complex logic

5. **Use theme when possible:**
   ```dart
   Theme.of(context).textTheme.bodyLarge
   ```

6. **Handle edge cases:**
   - Empty states
   - Loading states
   - Error states

## Resources

This skill includes comprehensive guides:

### references/

- **widget-patterns.md**: Common widget implementation patterns
- **riverpod-patterns.md**: State management with Riverpod
- **testing-guide.md**: Widget testing best practices
- **native-integration-guide.md**: Platform-specific integration (optional)

## Common Pitfalls

1. **Not using const:**
   - Always use const for static widgets

2. **Forgetting to dispose resources:**
   - Dispose controllers, streams in StatefulWidget

3. **Hardcoding values:**
   - Use theme and design tokens

4. **Missing null safety:**
   - Handle nullable values properly

5. **Not testing edge cases:**
   - Test disabled, loading, error states

6. **Ignoring accessibility:**
   - Add semantic labels

## Output Format

The implementation should include:

1. **Widget file** with proper documentation
2. **Test file** with comprehensive tests
3. **Supporting files** (enums, models if needed)
4. **Integration notes** for native features (if applicable)

## Related Skills

- **figma-to-flutter**: Design specification extraction
- **flutter-widget-assistant**: Architecture decision support
- **ios-development/swiftui-components**: iOS native implementation
- **android-test-runner**: Android test execution
