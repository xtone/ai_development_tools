# Riverpod Patterns Guide

Common state management patterns using Riverpod in Flutter.

## Provider Types

### Provider (Read-Only)

For computed values or simple read-only data:

```dart
final greetingProvider = Provider<String>((ref) {
  final user = ref.watch(userProvider);
  return 'Hello, ${user.name}!';
});
```

### StateProvider (Simple State)

For simple state that can be modified:

```dart
final counterProvider = StateProvider<int>((ref) => 0);

// Usage in widget
final count = ref.watch(counterProvider);
ref.read(counterProvider.notifier).state++;
```

### StateNotifierProvider (Complex State)

For complex state with multiple actions:

```dart
// State class (using freezed)
@freezed
class CartState with _$CartState {
  const factory CartState({
    @Default([]) List<CartItem> items,
    @Default(false) bool isLoading,
    String? error,
  }) = _CartState;
}

// StateNotifier
class CartNotifier extends StateNotifier<CartState> {
  CartNotifier(this._repository) : super(const CartState());

  final CartRepository _repository;

  Future<void> addItem(Product product) async {
    state = state.copyWith(isLoading: true);
    try {
      await _repository.addToCart(product);
      state = state.copyWith(
        items: [...state.items, CartItem(product: product, quantity: 1)],
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(error: e.toString(), isLoading: false);
    }
  }

  void removeItem(String productId) {
    state = state.copyWith(
      items: state.items.where((item) => item.product.id != productId).toList(),
    );
  }

  void clearCart() {
    state = const CartState();
  }
}

// Provider
final cartProvider = StateNotifierProvider<CartNotifier, CartState>((ref) {
  return CartNotifier(ref.read(cartRepositoryProvider));
});
```

### FutureProvider (Async Data)

For async data that doesn't change:

```dart
final userProfileProvider = FutureProvider<User>((ref) async {
  final userId = ref.watch(currentUserIdProvider);
  final repository = ref.read(userRepositoryProvider);
  return repository.getUser(userId);
});

// Usage
final userAsync = ref.watch(userProfileProvider);
return userAsync.when(
  data: (user) => Text(user.name),
  loading: () => CircularProgressIndicator(),
  error: (e, _) => Text('Error: $e'),
);
```

### FutureProvider.family (Parameterized)

For async data with parameters:

```dart
final productProvider = FutureProvider.family<Product, String>((ref, id) async {
  final repository = ref.read(productRepositoryProvider);
  return repository.getProduct(id);
});

// Usage
final productAsync = ref.watch(productProvider(productId));
```

### StreamProvider (Real-time Data)

For streams of data:

```dart
final messagesProvider = StreamProvider<List<Message>>((ref) {
  final chatId = ref.watch(currentChatIdProvider);
  return ref.read(chatRepositoryProvider).getMessages(chatId);
});
```

### NotifierProvider (Riverpod 2.0)

Modern approach for complex state:

```dart
@riverpod
class Counter extends _$Counter {
  @override
  int build() => 0;

  void increment() => state++;
  void decrement() => state--;
}

// Generated provider: counterProvider
```

### AsyncNotifierProvider (Riverpod 2.0)

For async state management:

```dart
@riverpod
class Products extends _$Products {
  @override
  Future<List<Product>> build() async {
    return ref.read(productRepositoryProvider).getProducts();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      return ref.read(productRepositoryProvider).getProducts();
    });
  }

  Future<void> addProduct(Product product) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      await ref.read(productRepositoryProvider).addProduct(product);
      return ref.read(productRepositoryProvider).getProducts();
    });
  }
}
```

## Common Patterns

### Repository Pattern

```dart
// Abstract repository
abstract class ProductRepository {
  Future<List<Product>> getProducts();
  Future<Product> getProduct(String id);
  Future<void> addProduct(Product product);
  Future<void> deleteProduct(String id);
}

// Implementation
class ProductRepositoryImpl implements ProductRepository {
  ProductRepositoryImpl(this._client);

  final ApiClient _client;

  @override
  Future<List<Product>> getProducts() async {
    final response = await _client.get('/products');
    return (response.data as List)
        .map((json) => Product.fromJson(json))
        .toList();
  }

  // ... other methods
}

// Provider
final productRepositoryProvider = Provider<ProductRepository>((ref) {
  return ProductRepositoryImpl(ref.read(apiClientProvider));
});
```

### ViewModel Pattern (MVVM)

```dart
// UIState
@freezed
class ProductListUIState with _$ProductListUIState {
  const factory ProductListUIState({
    @Default([]) List<Product> products,
    @Default([]) List<Product> filteredProducts,
    @Default(false) bool isLoading,
    String? error,
    @Default('') String searchQuery,
    @Default(SortOrder.newest) SortOrder sortOrder,
  }) = _ProductListUIState;
}

enum SortOrder { newest, oldest, priceHigh, priceLow }

// ViewModel
class ProductListViewModel extends StateNotifier<ProductListUIState> {
  ProductListViewModel(this._repository) : super(const ProductListUIState());

  final ProductRepository _repository;

  Future<void> loadProducts() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final products = await _repository.getProducts();
      state = state.copyWith(
        products: products,
        filteredProducts: _applyFilters(products),
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(error: e.toString(), isLoading: false);
    }
  }

  void search(String query) {
    state = state.copyWith(
      searchQuery: query,
      filteredProducts: _applyFilters(state.products),
    );
  }

  void setSortOrder(SortOrder order) {
    state = state.copyWith(
      sortOrder: order,
      filteredProducts: _applyFilters(state.products),
    );
  }

  List<Product> _applyFilters(List<Product> products) {
    var filtered = products;

    // Apply search
    if (state.searchQuery.isNotEmpty) {
      filtered = filtered
          .where((p) =>
              p.name.toLowerCase().contains(state.searchQuery.toLowerCase()))
          .toList();
    }

    // Apply sort
    switch (state.sortOrder) {
      case SortOrder.newest:
        filtered.sort((a, b) => b.createdAt.compareTo(a.createdAt));
        break;
      case SortOrder.oldest:
        filtered.sort((a, b) => a.createdAt.compareTo(b.createdAt));
        break;
      case SortOrder.priceHigh:
        filtered.sort((a, b) => b.price.compareTo(a.price));
        break;
      case SortOrder.priceLow:
        filtered.sort((a, b) => a.price.compareTo(b.price));
        break;
    }

    return filtered;
  }
}

// Provider
final productListViewModelProvider =
    StateNotifierProvider<ProductListViewModel, ProductListUIState>((ref) {
  return ProductListViewModel(ref.read(productRepositoryProvider));
});
```

### Combining Providers

```dart
// Combine multiple providers
final dashboardProvider = Provider<DashboardData>((ref) {
  final user = ref.watch(userProvider);
  final orders = ref.watch(ordersProvider);
  final notifications = ref.watch(notificationsProvider);

  return DashboardData(
    user: user,
    recentOrders: orders.take(5).toList(),
    unreadCount: notifications.where((n) => !n.isRead).length,
  );
});
```

### Scoped Providers

```dart
// Define provider
final selectedProductProvider = Provider<Product>((ref) {
  throw UnimplementedError();
});

// Override in widget tree
ProviderScope(
  overrides: [
    selectedProductProvider.overrideWithValue(product),
  ],
  child: ProductDetailView(),
)

// Use in child widget
final product = ref.watch(selectedProductProvider);
```

## Widget Integration

### ConsumerWidget

```dart
class ProductListScreen extends ConsumerWidget {
  const ProductListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(productListViewModelProvider);
    final viewModel = ref.read(productListViewModelProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: Text('Products'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: viewModel.loadProducts,
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

    return ListView.builder(
      itemCount: state.filteredProducts.length,
      itemBuilder: (context, index) {
        return ProductListItem(product: state.filteredProducts[index]);
      },
    );
  }
}
```

### HookConsumerWidget

```dart
class ProductSearchScreen extends HookConsumerWidget {
  const ProductSearchScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final searchController = useTextEditingController();
    final debouncer = useMemoized(() => Debouncer(milliseconds: 500));
    final state = ref.watch(productListViewModelProvider);
    final viewModel = ref.read(productListViewModelProvider.notifier);

    useEffect(() {
      viewModel.loadProducts();
      return null;
    }, []);

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          controller: searchController,
          decoration: InputDecoration(
            hintText: 'Search products...',
            border: InputBorder.none,
          ),
          onChanged: (value) {
            debouncer.run(() => viewModel.search(value));
          },
        ),
      ),
      body: state.isLoading
          ? Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: state.filteredProducts.length,
              itemBuilder: (context, index) {
                return ProductListItem(product: state.filteredProducts[index]);
              },
            ),
    );
  }
}
```

### Consumer (For Partial Rebuilds)

```dart
class ProductCard extends StatelessWidget {
  const ProductCard({super.key, required this.product});

  final Product product;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          Image.network(product.imageUrl),
          Text(product.name),
          // Only this part rebuilds when cart changes
          Consumer(
            builder: (context, ref, child) {
              final isInCart = ref.watch(
                cartProvider.select(
                  (state) => state.items.any((i) => i.product.id == product.id),
                ),
              );
              return IconButton(
                icon: Icon(
                  isInCart ? Icons.shopping_cart : Icons.add_shopping_cart,
                ),
                onPressed: () {
                  if (isInCart) {
                    ref.read(cartProvider.notifier).removeItem(product.id);
                  } else {
                    ref.read(cartProvider.notifier).addItem(product);
                  }
                },
              );
            },
          ),
        ],
      ),
    );
  }
}
```

## Best Practices

### 1. Use select() for Granular Rebuilds

```dart
// Bad: Rebuilds on any cart change
final cart = ref.watch(cartProvider);

// Good: Only rebuilds when item count changes
final itemCount = ref.watch(cartProvider.select((s) => s.items.length));
```

### 2. Keep Providers Small and Focused

```dart
// Bad: One massive provider
final appStateProvider = StateNotifierProvider<AppStateNotifier, AppState>(...);

// Good: Separate providers by domain
final userProvider = StateNotifierProvider<UserNotifier, UserState>(...);
final cartProvider = StateNotifierProvider<CartNotifier, CartState>(...);
final settingsProvider = StateNotifierProvider<SettingsNotifier, Settings>(...);
```

### 3. Use AutoDispose When Appropriate

```dart
// Auto dispose when no longer listened to
final searchResultsProvider = FutureProvider.autoDispose
    .family<List<Product>, String>((ref, query) async {
  return ref.read(productRepositoryProvider).search(query);
});
```

### 4. Handle Loading and Error States

```dart
final productsAsync = ref.watch(productsProvider);

return productsAsync.when(
  data: (products) => ProductList(products: products),
  loading: () => Center(child: CircularProgressIndicator()),
  error: (error, stack) => ErrorView(
    message: error.toString(),
    onRetry: () => ref.refresh(productsProvider),
  ),
);
```

### 5. Use ref.listen for Side Effects

```dart
@override
Widget build(BuildContext context, WidgetRef ref) {
  // Listen for auth changes to navigate
  ref.listen<AuthState>(authProvider, (previous, next) {
    if (next.isLoggedOut) {
      context.router.replace(LoginRoute());
    }
  });

  // ...
}
```

## Testing

### Testing Providers

```dart
void main() {
  test('CartNotifier adds item correctly', () {
    final container = ProviderContainer(
      overrides: [
        cartRepositoryProvider.overrideWithValue(MockCartRepository()),
      ],
    );

    final notifier = container.read(cartProvider.notifier);
    final product = Product(id: '1', name: 'Test', price: 10);

    notifier.addItem(product);

    expect(container.read(cartProvider).items.length, 1);
    expect(container.read(cartProvider).items.first.product, product);
  });
}
```

### Testing Widgets with Providers

```dart
void main() {
  testWidgets('ProductListScreen shows products', (tester) async {
    final products = [
      Product(id: '1', name: 'Product 1', price: 10),
      Product(id: '2', name: 'Product 2', price: 20),
    ];

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          productListViewModelProvider.overrideWith(
            (ref) => ProductListViewModel(MockProductRepository())
              ..state = ProductListUIState(
                products: products,
                filteredProducts: products,
              ),
          ),
        ],
        child: MaterialApp(home: ProductListScreen()),
      ),
    );

    expect(find.text('Product 1'), findsOneWidget);
    expect(find.text('Product 2'), findsOneWidget);
  });
}
```
