# Step 5: Generate Riverpod Providers

このステップでは、Riverpodプロバイダを生成します。

## Input

- Step 3で生成したAPIサービス
- Step 4で生成したリポジトリ

## Tasks

### 5.1 ディレクトリ構造の作成

```bash
mkdir -p lib/presentation/providers
mkdir -p lib/core/network
```

### 5.2 Dio Provider の生成

```dart
// lib/core/network/dio_provider.dart
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'dio_client.dart';

part 'dio_provider.g.dart';

/// Dioクライアントのプロバイダ
///
/// アプリ全体で単一インスタンスを共有（keepAlive: true）
@Riverpod(keepAlive: true)
DioClient dioClient(DioClientRef ref) {
  return DioClient(
    baseUrl: const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://localhost:3000/api',
    ),
  );
}
```

### 5.3 API Service Provider の生成

```dart
// lib/presentation/providers/users_providers.dart
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../core/network/dio_provider.dart';
import '../../data/api/users_api_service.dart';
import '../../data/repositories/users_repository_impl.dart';
import '../../domain/models/user.dart';
import '../../domain/repositories/users_repository.dart';

part 'users_providers.g.dart';

/// UsersApiServiceのプロバイダ
@riverpod
UsersApiService usersApiService(UsersApiServiceRef ref) {
  final dioClient = ref.watch(dioClientProvider);
  return UsersApiService(dioClient.dio);
}

/// UsersRepositoryのプロバイダ
@riverpod
UsersRepository usersRepository(UsersRepositoryRef ref) {
  final apiService = ref.watch(usersApiServiceProvider);
  return UsersRepositoryImpl(apiService);
}
```

### 5.4 Data Provider の生成

#### 一覧取得プロバイダ

```dart
/// ユーザー一覧を取得するプロバイダ
@riverpod
Future<List<User>> users(UsersRef ref) async {
  final repository = ref.watch(usersRepositoryProvider);
  final result = await repository.getUsers();
  return result.fold(
    (failure) => throw failure,
    (users) => users,
  );
}
```

#### ページネーション対応一覧プロバイダ

```dart
/// ページネーション対応のユーザー一覧プロバイダ
@riverpod
Future<List<User>> usersPaginated(
  UsersPaginatedRef ref, {
  int page = 1,
  int perPage = 20,
}) async {
  final repository = ref.watch(usersRepositoryProvider);
  final result = await repository.getUsers(
    page: page,
    perPage: perPage,
  );
  return result.fold(
    (failure) => throw failure,
    (users) => users,
  );
}
```

#### 単体取得プロバイダ（Family）

```dart
/// 指定IDのユーザーを取得するプロバイダ
@riverpod
Future<User> user(UserRef ref, int id) async {
  final repository = ref.watch(usersRepositoryProvider);
  final result = await repository.getUser(id: id);
  return result.fold(
    (failure) => throw failure,
    (user) => user,
  );
}
```

### 5.5 Mutation Provider の生成

CRUDの作成・更新・削除操作用のプロバイダを生成します。

```dart
/// ユーザー作成のNotifierプロバイダ
@riverpod
class CreateUser extends _$CreateUser {
  @override
  AsyncValue<User?> build() => const AsyncData(null);

  Future<void> execute(CreateUserDto data) async {
    state = const AsyncLoading();
    final repository = ref.read(usersRepositoryProvider);
    final result = await repository.createUser(data: data);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (user) => AsyncData(user),
    );
  }
}

/// ユーザー更新のNotifierプロバイダ
@riverpod
class UpdateUser extends _$UpdateUser {
  @override
  AsyncValue<User?> build() => const AsyncData(null);

  Future<void> execute({
    required int id,
    required UpdateUserDto data,
  }) async {
    state = const AsyncLoading();
    final repository = ref.read(usersRepositoryProvider);
    final result = await repository.updateUser(id: id, data: data);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (user) => AsyncData(user),
    );
  }
}

/// ユーザー削除のNotifierプロバイダ
@riverpod
class DeleteUser extends _$DeleteUser {
  @override
  AsyncValue<void> build() => const AsyncData(null);

  Future<void> execute(int id) async {
    state = const AsyncLoading();
    final repository = ref.read(usersRepositoryProvider);
    final result = await repository.deleteUser(id: id);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (_) => const AsyncData(null),
    );
  }
}
```

### 5.6 完成例

```dart
// lib/presentation/providers/users_providers.dart
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../core/network/dio_provider.dart';
import '../../data/api/users_api_service.dart';
import '../../data/repositories/users_repository_impl.dart';
import '../../domain/models/user.dart';
import '../../domain/models/create_user_dto.dart';
import '../../domain/models/update_user_dto.dart';
import '../../domain/repositories/users_repository.dart';

part 'users_providers.g.dart';

// =============================================================================
// Infrastructure Providers
// =============================================================================

/// UsersApiServiceのプロバイダ
@riverpod
UsersApiService usersApiService(UsersApiServiceRef ref) {
  final dioClient = ref.watch(dioClientProvider);
  return UsersApiService(dioClient.dio);
}

/// UsersRepositoryのプロバイダ
@riverpod
UsersRepository usersRepository(UsersRepositoryRef ref) {
  final apiService = ref.watch(usersApiServiceProvider);
  return UsersRepositoryImpl(apiService);
}

// =============================================================================
// Query Providers
// =============================================================================

/// ユーザー一覧を取得するプロバイダ
@riverpod
Future<List<User>> users(UsersRef ref) async {
  final repository = ref.watch(usersRepositoryProvider);
  final result = await repository.getUsers();
  return result.fold(
    (failure) => throw failure,
    (users) => users,
  );
}

/// 指定IDのユーザーを取得するプロバイダ
@riverpod
Future<User> user(UserRef ref, int id) async {
  final repository = ref.watch(usersRepositoryProvider);
  final result = await repository.getUser(id: id);
  return result.fold(
    (failure) => throw failure,
    (user) => user,
  );
}

// =============================================================================
// Mutation Providers
// =============================================================================

/// ユーザー作成のNotifierプロバイダ
@riverpod
class CreateUser extends _$CreateUser {
  @override
  AsyncValue<User?> build() => const AsyncData(null);

  Future<void> execute(CreateUserDto data) async {
    state = const AsyncLoading();
    final repository = ref.read(usersRepositoryProvider);
    final result = await repository.createUser(data: data);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (user) {
        // 一覧を再取得
        ref.invalidate(usersProvider);
        return AsyncData(user);
      },
    );
  }
}

/// ユーザー更新のNotifierプロバイダ
@riverpod
class UpdateUser extends _$UpdateUser {
  @override
  AsyncValue<User?> build() => const AsyncData(null);

  Future<void> execute({
    required int id,
    required UpdateUserDto data,
  }) async {
    state = const AsyncLoading();
    final repository = ref.read(usersRepositoryProvider);
    final result = await repository.updateUser(id: id, data: data);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (user) {
        // 関連プロバイダを再取得
        ref.invalidate(usersProvider);
        ref.invalidate(userProvider(id));
        return AsyncData(user);
      },
    );
  }
}

/// ユーザー削除のNotifierプロバイダ
@riverpod
class DeleteUser extends _$DeleteUser {
  @override
  AsyncValue<void> build() => const AsyncData(null);

  Future<void> execute(int id) async {
    state = const AsyncLoading();
    final repository = ref.read(usersRepositoryProvider);
    final result = await repository.deleteUser(id: id);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (_) {
        // 一覧を再取得
        ref.invalidate(usersProvider);
        return const AsyncData(null);
      },
    );
  }
}
```

### 5.7 例外版のプロバイダ

例外ベースのエラーハンドリングを選択した場合：

```dart
/// ユーザー一覧を取得するプロバイダ（例外版）
@riverpod
Future<List<User>> users(UsersRef ref) async {
  final repository = ref.watch(usersRepositoryProvider);
  return repository.getUsers();
}

/// ユーザー作成のNotifierプロバイダ（例外版）
@riverpod
class CreateUser extends _$CreateUser {
  @override
  AsyncValue<User?> build() => const AsyncData(null);

  Future<void> execute(CreateUserDto data) async {
    state = const AsyncLoading();
    try {
      final repository = ref.read(usersRepositoryProvider);
      final user = await repository.createUser(data: data);
      ref.invalidate(usersProvider);
      state = AsyncData(user);
    } catch (e, st) {
      state = AsyncError(e, st);
    }
  }
}
```

### 5.8 Widget での使用例

```dart
// 一覧表示
class UserListScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final usersAsync = ref.watch(usersProvider);

    return usersAsync.when(
      data: (users) => ListView.builder(
        itemCount: users.length,
        itemBuilder: (context, index) => UserCard(user: users[index]),
      ),
      loading: () => const CircularProgressIndicator(),
      error: (error, _) => ErrorWidget(error),
    );
  }
}

// 詳細表示
class UserDetailScreen extends ConsumerWidget {
  final int userId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(userProvider(userId));

    return userAsync.when(
      data: (user) => UserDetail(user: user),
      loading: () => const CircularProgressIndicator(),
      error: (error, _) => ErrorWidget(error),
    );
  }
}

// 作成操作
class CreateUserButton extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final createState = ref.watch(createUserProvider);

    return ElevatedButton(
      onPressed: createState.isLoading
          ? null
          : () => ref.read(createUserProvider.notifier).execute(
                CreateUserDto(name: 'John', email: 'john@example.com'),
              ),
      child: createState.isLoading
          ? const CircularProgressIndicator()
          : const Text('Create User'),
    );
  }
}
```

## Output

生成されるファイル一覧：

```
lib/
├── core/
│   └── network/
│       └── dio_provider.dart
└── presentation/
    └── providers/
        ├── users_providers.dart
        ├── posts_providers.dart
        └── comments_providers.dart
```

## Checklist

- [ ] Dio Providerを生成した
- [ ] すべてのAPIサービスに対応するプロバイダを作成した
- [ ] すべてのリポジトリに対応するプロバイダを作成した
- [ ] 一覧取得プロバイダを作成した
- [ ] 単体取得プロバイダ（Family）を作成した
- [ ] 作成・更新・削除のNotifierプロバイダを作成した
- [ ] Mutationプロバイダで関連データの再取得（invalidate）を実装した
- [ ] part文とimportを正しく設定した

## Next Step

プロバイダ生成完了後、Step 6（実装検証）に進みます。
