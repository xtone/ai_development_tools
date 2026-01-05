# Flutter Widget Testing Guide

Best practices and patterns for testing Flutter widgets.

## Test Setup

### Basic Test Structure

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/widgets/app_button.dart';

void main() {
  group('AppButton', () {
    testWidgets('renders label correctly', (tester) async {
      // Arrange
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

      // Assert
      expect(find.text('Test Button'), findsOneWidget);
    });
  });
}
```

### Test Helper Function

```dart
Widget createTestWidget(Widget child) {
  return MaterialApp(
    home: Scaffold(
      body: child,
    ),
  );
}

// Usage
await tester.pumpWidget(createTestWidget(AppButton(...)));
```

### Test with Theme

```dart
Widget createThemedTestWidget(Widget child) {
  return MaterialApp(
    theme: ThemeData(
      primarySwatch: Colors.blue,
      textTheme: TextTheme(
        bodyLarge: TextStyle(fontSize: 16),
      ),
    ),
    home: Scaffold(body: child),
  );
}
```

## Finding Widgets

### Common Finders

```dart
// By text
find.text('Hello')

// By widget type
find.byType(ElevatedButton)

// By key
find.byKey(Key('submit_button'))

// By icon
find.byIcon(Icons.search)

// By widget predicate
find.byWidgetPredicate(
  (widget) => widget is Text && widget.data?.contains('Error') == true,
)

// Descendant finder
find.descendant(
  of: find.byType(Card),
  matching: find.text('Title'),
)

// Ancestor finder
find.ancestor(
  of: find.text('Title'),
  matching: find.byType(Card),
)
```

### Finder Matchers

```dart
// Finds exactly one widget
expect(find.text('Title'), findsOneWidget);

// Finds nothing
expect(find.text('Error'), findsNothing);

// Finds multiple widgets
expect(find.byType(ListTile), findsNWidgets(3));

// Finds at least one
expect(find.byType(Text), findsWidgets);
```

## Interactions

### Tap

```dart
testWidgets('button tap calls onPressed', (tester) async {
  var tapped = false;

  await tester.pumpWidget(createTestWidget(
    AppButton(
      label: 'Tap Me',
      onPressed: () => tapped = true,
    ),
  ));

  await tester.tap(find.text('Tap Me'));
  await tester.pump(); // Trigger rebuild

  expect(tapped, isTrue);
});
```

### Long Press

```dart
testWidgets('long press shows context menu', (tester) async {
  await tester.pumpWidget(createTestWidget(
    LongPressWidget(onLongPress: () {}),
  ));

  await tester.longPress(find.byType(LongPressWidget));
  await tester.pump();

  expect(find.text('Context Menu'), findsOneWidget);
});
```

### Text Entry

```dart
testWidgets('text field accepts input', (tester) async {
  await tester.pumpWidget(createTestWidget(
    TextField(key: Key('email_field')),
  ));

  await tester.enterText(find.byKey(Key('email_field')), 'test@example.com');
  await tester.pump();

  expect(find.text('test@example.com'), findsOneWidget);
});
```

### Scrolling

```dart
testWidgets('scrolls to show item', (tester) async {
  await tester.pumpWidget(createTestWidget(
    ListView.builder(
      itemCount: 100,
      itemBuilder: (_, i) => ListTile(title: Text('Item $i')),
    ),
  ));

  // Scroll down
  await tester.scrollUntilVisible(
    find.text('Item 50'),
    500.0, // scroll amount
    scrollable: find.byType(Scrollable),
  );

  expect(find.text('Item 50'), findsOneWidget);
});

// Or use drag
testWidgets('drags to scroll', (tester) async {
  await tester.pumpWidget(createTestWidget(listView));

  await tester.drag(find.byType(ListView), Offset(0, -300));
  await tester.pump();
});
```

### Form Submission

```dart
testWidgets('form submits with valid data', (tester) async {
  var submittedEmail = '';

  await tester.pumpWidget(createTestWidget(
    LoginForm(onSubmit: (email, _) => submittedEmail = email),
  ));

  await tester.enterText(find.byKey(Key('email')), 'test@example.com');
  await tester.enterText(find.byKey(Key('password')), 'password123');
  await tester.tap(find.text('Submit'));
  await tester.pump();

  expect(submittedEmail, 'test@example.com');
});
```

## Async Testing

### Using pump() vs pumpAndSettle()

```dart
// pump() - advances one frame
await tester.tap(find.text('Button'));
await tester.pump(); // One frame

// pump(duration) - advances by duration
await tester.pump(Duration(milliseconds: 100));

// pumpAndSettle() - pumps until no more frames scheduled
// Good for animations
await tester.tap(find.text('Button'));
await tester.pumpAndSettle();

// pumpAndSettle with timeout
await tester.pumpAndSettle(Duration(seconds: 5));
```

### Testing Async Operations

```dart
testWidgets('shows loading then data', (tester) async {
  final completer = Completer<List<Product>>();

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        productsProvider.overrideWith((ref) => completer.future),
      ],
      child: MaterialApp(home: ProductListScreen()),
    ),
  );

  // Initially shows loading
  expect(find.byType(CircularProgressIndicator), findsOneWidget);

  // Complete the future
  completer.complete([Product(name: 'Test Product')]);
  await tester.pumpAndSettle();

  // Now shows data
  expect(find.byType(CircularProgressIndicator), findsNothing);
  expect(find.text('Test Product'), findsOneWidget);
});
```

### Using FakeAsync

```dart
testWidgets('debounces search input', (tester) async {
  await tester.runAsync(() async {
    var searchCount = 0;

    await tester.pumpWidget(createTestWidget(
      SearchField(onSearch: (_) => searchCount++),
    ));

    await tester.enterText(find.byType(TextField), 'a');
    await tester.enterText(find.byType(TextField), 'ab');
    await tester.enterText(find.byType(TextField), 'abc');

    // Wait for debounce (500ms)
    await tester.pump(Duration(milliseconds: 600));

    // Should only search once due to debounce
    expect(searchCount, 1);
  });
});
```

## Testing with Riverpod

### Basic Provider Override

```dart
testWidgets('displays user name from provider', (tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        userProvider.overrideWithValue(
          User(name: 'John Doe'),
        ),
      ],
      child: MaterialApp(home: UserProfile()),
    ),
  );

  expect(find.text('John Doe'), findsOneWidget);
});
```

### Testing StateNotifier

```dart
testWidgets('cart updates when item added', (tester) async {
  final container = ProviderContainer();

  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: MaterialApp(home: CartScreen()),
    ),
  );

  // Initial state
  expect(find.text('Cart (0)'), findsOneWidget);

  // Add item
  container.read(cartProvider.notifier).addItem(
    Product(id: '1', name: 'Test', price: 10),
  );
  await tester.pump();

  // Updated state
  expect(find.text('Cart (1)'), findsOneWidget);
});
```

### Mocking Repository

```dart
class MockProductRepository extends Mock implements ProductRepository {}

testWidgets('shows products from repository', (tester) async {
  final mockRepo = MockProductRepository();
  when(mockRepo.getProducts()).thenAnswer(
    (_) async => [Product(name: 'Test Product')],
  );

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        productRepositoryProvider.overrideWithValue(mockRepo),
      ],
      child: MaterialApp(home: ProductListScreen()),
    ),
  );

  await tester.pumpAndSettle();

  expect(find.text('Test Product'), findsOneWidget);
  verify(mockRepo.getProducts()).called(1);
});
```

## Testing States

### Loading State

```dart
testWidgets('shows loading indicator while loading', (tester) async {
  await tester.pumpWidget(createTestWidget(
    DataWidget(isLoading: true),
  ));

  expect(find.byType(CircularProgressIndicator), findsOneWidget);
  expect(find.byType(DataContent), findsNothing);
});
```

### Error State

```dart
testWidgets('shows error message on error', (tester) async {
  await tester.pumpWidget(createTestWidget(
    DataWidget(error: 'Something went wrong'),
  ));

  expect(find.text('Something went wrong'), findsOneWidget);
  expect(find.byType(DataContent), findsNothing);
});
```

### Empty State

```dart
testWidgets('shows empty state when no data', (tester) async {
  await tester.pumpWidget(createTestWidget(
    DataWidget(items: []),
  ));

  expect(find.text('No items found'), findsOneWidget);
  expect(find.byType(ListView), findsNothing);
});
```

### Disabled State

```dart
testWidgets('button is disabled when onPressed is null', (tester) async {
  await tester.pumpWidget(createTestWidget(
    AppButton(label: 'Disabled', onPressed: null),
  ));

  // Check visual indicator
  final opacity = tester.widget<Opacity>(find.byType(Opacity));
  expect(opacity.opacity, 0.5);

  // Verify tap does nothing
  var tapped = false;
  await tester.tap(find.text('Disabled'));
  expect(tapped, isFalse);
});
```

## Testing Accessibility

### Semantic Labels

```dart
testWidgets('has correct semantic label', (tester) async {
  await tester.pumpWidget(createTestWidget(
    AppButton(label: 'Submit', onPressed: () {}),
  ));

  final semantics = tester.getSemantics(find.byType(AppButton));
  expect(semantics.label, 'Submit');
  expect(semantics.hasFlag(SemanticsFlag.isButton), isTrue);
});
```

### Testing with Semantics

```dart
testWidgets('meets accessibility guidelines', (tester) async {
  final handle = tester.ensureSemantics();

  await tester.pumpWidget(createTestWidget(
    AppButton(label: 'Submit', onPressed: () {}),
  ));

  await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  await expectLater(tester, meetsGuideline(textContrastGuideline));

  handle.dispose();
});
```

## Golden Tests

### Basic Golden Test

```dart
testWidgets('matches golden file', (tester) async {
  await tester.pumpWidget(createTestWidget(
    AppButton(label: 'Test', onPressed: () {}),
  ));

  await expectLater(
    find.byType(AppButton),
    matchesGoldenFile('goldens/app_button.png'),
  );
});
```

### Golden Test with Variants

```dart
testWidgets('button variants match golden', (tester) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: Column(
          children: [
            AppButton(label: 'Primary', variant: ButtonVariant.primary),
            AppButton(label: 'Secondary', variant: ButtonVariant.secondary),
            AppButton(label: 'Tertiary', variant: ButtonVariant.tertiary),
          ],
        ),
      ),
    ),
  );

  await expectLater(
    find.byType(Column),
    matchesGoldenFile('goldens/button_variants.png'),
  );
});
```

## Tips and Best Practices

### 1. Use Keys for Finding Widgets

```dart
// In widget
TextField(key: Key('email_input'))

// In test
find.byKey(Key('email_input'))
```

### 2. Group Related Tests

```dart
group('AppButton', () {
  group('rendering', () {
    testWidgets('renders label', ...);
    testWidgets('renders icon when provided', ...);
  });

  group('interactions', () {
    testWidgets('calls onPressed when tapped', ...);
    testWidgets('does not call onPressed when disabled', ...);
  });

  group('variants', () {
    testWidgets('primary has blue background', ...);
    testWidgets('secondary has border', ...);
  });
});
```

### 3. Test Edge Cases

```dart
testWidgets('handles empty text', (tester) async {
  await tester.pumpWidget(createTestWidget(
    AppButton(label: '', onPressed: () {}),
  ));
  // Verify widget handles empty text gracefully
});

testWidgets('handles very long text', (tester) async {
  await tester.pumpWidget(createTestWidget(
    AppButton(
      label: 'A' * 100, // Very long text
      onPressed: () {},
    ),
  ));
  // Verify widget handles overflow
});
```

### 4. Clean Up Resources

```dart
late ProviderContainer container;

setUp(() {
  container = ProviderContainer();
});

tearDown(() {
  container.dispose();
});
```

### 5. Use testWidgets Over test

Always use `testWidgets` for widget tests - it provides the `WidgetTester` and handles the widget lifecycle properly.

```dart
// Good
testWidgets('widget test', (tester) async {
  await tester.pumpWidget(...);
});

// Bad - don't use test() for widget tests
test('widget test', () {
  // Missing WidgetTester
});
```
