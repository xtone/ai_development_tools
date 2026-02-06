# Step 6: Verify Implementation

このステップでは、生成されたコードをビルド・検証します。

## Tasks

### 6.1 pubspec.yaml の確認

必要な依存関係がすべて追加されていることを確認します。

```yaml
# pubspec.yaml
name: your_app
description: Your Flutter application

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter

  # HTTP Client
  dio: ^5.4.0

  # API Definition (Retrofit)
  retrofit: ^4.1.0

  # Serialization
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1

  # State Management
  flutter_riverpod: ^2.4.9
  riverpod_annotation: ^2.3.3

  # Functional Programming
  dartz: ^0.10.1

dev_dependencies:
  flutter_test:
    sdk: flutter

  # Code Generation
  build_runner: ^2.4.8
  retrofit_generator: ^8.1.0
  freezed: ^2.4.6
  json_serializable: ^6.7.1
  riverpod_generator: ^2.3.9

  # Linting
  flutter_lints: ^3.0.1
```

### 6.2 依存関係のインストール

```bash
flutter pub get
```

### 6.3 コード生成の実行

```bash
# 通常のビルド
flutter pub run build_runner build --delete-conflicting-outputs

# または、継続的なビルド（開発中）
flutter pub run build_runner watch --delete-conflicting-outputs
```

### 6.4 生成されるファイルの確認

build_runner実行後、以下のファイルが生成されることを確認します。

```
lib/
├── core/
│   ├── error/
│   │   ├── failures.dart
│   │   └── failures.freezed.dart        # ← 生成
│   └── network/
│       ├── dio_client.dart
│       ├── dio_provider.dart
│       └── dio_provider.g.dart          # ← 生成
├── data/
│   ├── api/
│   │   ├── users_api_service.dart
│   │   └── users_api_service.g.dart     # ← 生成
│   └── repositories/
│       └── users_repository_impl.dart
├── domain/
│   ├── models/
│   │   ├── user.dart
│   │   ├── user.freezed.dart            # ← 生成
│   │   └── user.g.dart                  # ← 生成
│   └── repositories/
│       └── users_repository.dart
└── presentation/
    └── providers/
        ├── users_providers.dart
        └── users_providers.g.dart       # ← 生成
```

### 6.5 型エラーのチェック

```bash
flutter analyze
```

#### よくあるエラーと対処法

| エラー | 原因 | 対処 |
|-------|------|------|
| `The name '...' is already defined` | part文の重複 | part文を確認し重複を削除 |
| `Target of URI hasn't been generated` | .g.dartファイル未生成 | build_runnerを再実行 |
| `The class '...' doesn't have a default constructor` | Freezedの設定ミス | @freezedアノテーションを確認 |
| `Couldn't find a factory constructor` | fromJsonの定義漏れ | factory fromJsonを追加 |
| `The argument type 'Xxx' can't be assigned` | 型不一致 | 型マッピングを確認 |

### 6.6 ビルドの確認

```bash
flutter build apk --debug
# または
flutter build ios --debug --no-codesign
```

### 6.7 基本的な動作テスト

#### Provider のテスト

```dart
// test/providers/users_providers_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';
import 'package:dartz/dartz.dart';

import 'package:your_app/domain/models/user.dart';
import 'package:your_app/domain/repositories/users_repository.dart';
import 'package:your_app/presentation/providers/users_providers.dart';

class MockUsersRepository extends Mock implements UsersRepository {}

void main() {
  late MockUsersRepository mockRepository;
  late ProviderContainer container;

  setUp(() {
    mockRepository = MockUsersRepository();
    container = ProviderContainer(
      overrides: [
        usersRepositoryProvider.overrideWithValue(mockRepository),
      ],
    );
  });

  tearDown(() {
    container.dispose();
  });

  group('usersProvider', () {
    test('returns list of users on success', () async {
      // Arrange
      final users = [
        User(id: 1, name: 'John', email: 'john@example.com'),
        User(id: 2, name: 'Jane', email: 'jane@example.com'),
      ];
      when(() => mockRepository.getUsers())
          .thenAnswer((_) async => Right(users));

      // Act
      final result = await container.read(usersProvider.future);

      // Assert
      expect(result, users);
    });

    test('throws failure on error', () async {
      // Arrange
      when(() => mockRepository.getUsers())
          .thenAnswer((_) async => const Left(Failure.network(message: 'Error')));

      // Act & Assert
      expect(
        () => container.read(usersProvider.future),
        throwsA(isA<Failure>()),
      );
    });
  });
}
```

#### Repository のテスト

```dart
// test/repositories/users_repository_impl_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:dio/dio.dart';

import 'package:your_app/data/api/users_api_service.dart';
import 'package:your_app/data/repositories/users_repository_impl.dart';
import 'package:your_app/domain/models/user.dart';

class MockUsersApiService extends Mock implements UsersApiService {}

void main() {
  late MockUsersApiService mockApiService;
  late UsersRepositoryImpl repository;

  setUp(() {
    mockApiService = MockUsersApiService();
    repository = UsersRepositoryImpl(mockApiService);
  });

  group('getUsers', () {
    test('returns Right with users on success', () async {
      // Arrange
      final users = [
        User(id: 1, name: 'John', email: 'john@example.com'),
      ];
      when(() => mockApiService.getUsers())
          .thenAnswer((_) async => users);

      // Act
      final result = await repository.getUsers();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (l) => fail('Should be Right'),
        (r) => expect(r, users),
      );
    });

    test('returns Left with NetworkFailure on DioException', () async {
      // Arrange
      when(() => mockApiService.getUsers()).thenThrow(
        DioException(
          type: DioExceptionType.connectionError,
          requestOptions: RequestOptions(),
        ),
      );

      // Act
      final result = await repository.getUsers();

      // Assert
      expect(result.isLeft(), true);
      result.fold(
        (l) => expect(l, isA<NetworkFailure>()),
        (r) => fail('Should be Left'),
      );
    });
  });
}
```

### 6.8 環境変数の設定

API のベースURLを環境変数で設定します。

```bash
# 開発環境
flutter run --dart-define=API_BASE_URL=http://localhost:3000/api

# 本番環境
flutter run --dart-define=API_BASE_URL=https://api.example.com
```

#### launch.json（VS Code）

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Development",
      "request": "launch",
      "type": "dart",
      "args": [
        "--dart-define=API_BASE_URL=http://localhost:3000/api"
      ]
    },
    {
      "name": "Production",
      "request": "launch",
      "type": "dart",
      "args": [
        "--dart-define=API_BASE_URL=https://api.example.com"
      ]
    }
  ]
}
```

### 6.9 ProviderScope の設定

main.dart でProviderScopeを設定します。

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Your App',
      home: const HomeScreen(),
    );
  }
}
```

## Verification Checklist

### 依存関係
- [ ] pubspec.yaml に必要な依存関係がすべて追加されている
- [ ] `flutter pub get` が成功する

### コード生成
- [ ] `flutter pub run build_runner build` が成功する
- [ ] すべての .g.dart ファイルが生成されている
- [ ] すべての .freezed.dart ファイルが生成されている

### 型チェック
- [ ] `flutter analyze` でエラーがない
- [ ] すべての型が正しくマッピングされている

### ビルド
- [ ] `flutter build` が成功する

### テスト
- [ ] Provider のテストが通る
- [ ] Repository のテストが通る

### 設定
- [ ] 環境変数（API_BASE_URL）が設定されている
- [ ] ProviderScope が設定されている

## Troubleshooting

### build_runner が失敗する場合

```bash
# キャッシュをクリア
flutter pub run build_runner clean
flutter pub run build_runner build --delete-conflicting-outputs
```

### 依存関係の競合

```bash
# 依存関係を更新
flutter pub upgrade --major-versions
```

### 型エラーが解消しない場合

1. IDE を再起動
2. `.dart_tool` フォルダを削除
3. `flutter pub get` を再実行
4. `flutter pub run build_runner build --delete-conflicting-outputs` を再実行

## Next Steps

検証完了後：

1. **実際のAPIとの接続テスト** - 開発サーバーに接続してE2Eテスト
2. **エラーハンドリングのカスタマイズ** - プロジェクト固有のエラー型を追加
3. **認証インターセプターの追加** - トークン管理の実装
4. **キャッシュ層の追加** - オフライン対応の実装
5. **リトライ機構の追加** - ネットワークエラー時の再試行

## Generated Code Summary

スキル実行により生成されたコードの概要をユーザーに提示してください。

```markdown
## 生成完了

### 生成されたファイル

#### Models (X files)
- lib/domain/models/user.dart
- lib/domain/models/create_user_dto.dart
- ...

#### API Services (X files)
- lib/data/api/users_api_service.dart
- ...

#### Repositories (X files)
- lib/domain/repositories/users_repository.dart
- lib/data/repositories/users_repository_impl.dart
- ...

#### Providers (X files)
- lib/presentation/providers/users_providers.dart
- ...

#### Core (X files)
- lib/core/error/failures.dart
- lib/core/network/dio_client.dart
- lib/core/network/dio_provider.dart

### 次のステップ

1. `flutter pub get` を実行
2. `flutter pub run build_runner build --delete-conflicting-outputs` を実行
3. `flutter analyze` で型エラーがないことを確認
4. APIサーバーに接続して動作確認
```
