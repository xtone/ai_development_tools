# Step 4: Generate Repository

このステップでは、リポジトリインターフェースと実装クラスを生成します。

## Input

- Step 3で生成したAPIサービス
- エラーハンドリング方式の選択（Either型 or 例外）

## Tasks

### 4.1 ディレクトリ構造の作成

```bash
mkdir -p lib/domain/repositories
mkdir -p lib/data/repositories
mkdir -p lib/core/error
mkdir -p lib/core/network
```

### 4.2 Failure クラスの生成

```dart
// lib/core/error/failures.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'failures.freezed.dart';

/// アプリケーションのエラー型
@freezed
sealed class Failure with _$Failure {
  /// サーバーエラー
  const factory Failure.server({
    required String message,
    int? statusCode,
  }) = ServerFailure;

  /// ネットワークエラー
  const factory Failure.network({
    required String message,
  }) = NetworkFailure;

  /// キャッシュエラー
  const factory Failure.cache({
    required String message,
  }) = CacheFailure;

  /// バリデーションエラー
  const factory Failure.validation({
    required String message,
    Map<String, List<String>>? errors,
  }) = ValidationFailure;

  /// 認証エラー
  const factory Failure.unauthorized({
    String? message,
  }) = UnauthorizedFailure;

  /// NotFoundエラー
  const factory Failure.notFound({
    String? message,
  }) = NotFoundFailure;

  /// 不明なエラー
  const factory Failure.unknown({
    String? message,
    Object? error,
  }) = UnknownFailure;
}

/// Failure の拡張メソッド
extension FailureX on Failure {
  /// エラーメッセージを取得
  String get displayMessage => when(
        server: (message, _) => message,
        network: (message) => message,
        cache: (message) => message,
        validation: (message, _) => message,
        unauthorized: (message) => message ?? '認証が必要です',
        notFound: (message) => message ?? 'リソースが見つかりません',
        unknown: (message, _) => message ?? '予期せぬエラーが発生しました',
      );
}
```

### 4.3 Dio Client の生成

```dart
// lib/core/network/dio_client.dart
import 'package:dio/dio.dart';

/// Dioクライアントの設定
class DioClient {
  late final Dio _dio;

  DioClient({
    required String baseUrl,
    Map<String, dynamic>? headers,
    Duration? connectTimeout,
    Duration? receiveTimeout,
  }) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        headers: headers ?? {'Content-Type': 'application/json'},
        connectTimeout: connectTimeout ?? const Duration(seconds: 30),
        receiveTimeout: receiveTimeout ?? const Duration(seconds: 30),
      ),
    );

    _dio.interceptors.addAll([
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (obj) => print('[DIO] $obj'),
      ),
    ]);
  }

  Dio get dio => _dio;

  /// インターセプターを追加
  void addInterceptor(Interceptor interceptor) {
    _dio.interceptors.add(interceptor);
  }

  /// 認証トークンを設定
  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  /// 認証トークンをクリア
  void clearAuthToken() {
    _dio.options.headers.remove('Authorization');
  }
}
```

### 4.4 Repository Interface の生成

```dart
// lib/domain/repositories/users_repository.dart
import 'package:dartz/dartz.dart';

import '../models/user.dart';
import '../models/create_user_dto.dart';
import '../models/update_user_dto.dart';
import '../../core/error/failures.dart';

/// ユーザーリポジトリのインターフェース
abstract interface class UsersRepository {
  /// ユーザー一覧を取得
  Future<Either<Failure, List<User>>> getUsers({
    int? page,
    int? perPage,
  });

  /// 指定IDのユーザーを取得
  Future<Either<Failure, User>> getUser({
    required int id,
  });

  /// 新規ユーザーを作成
  Future<Either<Failure, User>> createUser({
    required CreateUserDto data,
  });

  /// ユーザー情報を更新
  Future<Either<Failure, User>> updateUser({
    required int id,
    required UpdateUserDto data,
  });

  /// ユーザーを削除
  Future<Either<Failure, void>> deleteUser({
    required int id,
  });
}
```

### 4.5 Repository Implementation の生成（Either版 - 推奨）

```dart
// lib/data/repositories/users_repository_impl.dart
import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';

import '../../core/error/failures.dart';
import '../../domain/models/user.dart';
import '../../domain/models/create_user_dto.dart';
import '../../domain/models/update_user_dto.dart';
import '../../domain/repositories/users_repository.dart';
import '../api/users_api_service.dart';

/// ユーザーリポジトリの実装
class UsersRepositoryImpl implements UsersRepository {
  final UsersApiService _apiService;

  UsersRepositoryImpl(this._apiService);

  @override
  Future<Either<Failure, List<User>>> getUsers({
    int? page,
    int? perPage,
  }) async {
    try {
      final result = await _apiService.getUsers(
        page: page,
        perPage: perPage,
      );
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, User>> getUser({
    required int id,
  }) async {
    try {
      final result = await _apiService.getUser(id: id);
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, User>> createUser({
    required CreateUserDto data,
  }) async {
    try {
      final result = await _apiService.createUser(body: data);
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, User>> updateUser({
    required int id,
    required UpdateUserDto data,
  }) async {
    try {
      final result = await _apiService.updateUser(id: id, body: data);
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, void>> deleteUser({
    required int id,
  }) async {
    try {
      await _apiService.deleteUser(id: id);
      return const Right(null);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  /// DioExceptionをFailureに変換
  Failure _handleDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const Failure.network(message: '接続がタイムアウトしました');
      case DioExceptionType.connectionError:
        return const Failure.network(message: 'インターネット接続を確認してください');
      case DioExceptionType.badResponse:
        return _handleStatusCode(e.response?.statusCode, e.response?.data);
      case DioExceptionType.cancel:
        return const Failure.network(message: 'リクエストがキャンセルされました');
      default:
        return Failure.unknown(message: e.message, error: e);
    }
  }

  /// HTTPステータスコードをFailureに変換
  Failure _handleStatusCode(int? statusCode, dynamic data) {
    final message = data is Map ? data['message'] as String? : null;
    switch (statusCode) {
      case 400:
        return Failure.validation(
          message: message ?? 'リクエストが不正です',
          errors: data is Map
              ? (data['errors'] as Map<String, dynamic>?)?.map(
                  (k, v) => MapEntry(k, (v as List).cast<String>()),
                )
              : null,
        );
      case 401:
        return Failure.unauthorized(message: message);
      case 403:
        return Failure.unauthorized(message: message ?? 'アクセス権限がありません');
      case 404:
        return Failure.notFound(message: message);
      case 422:
        return Failure.validation(
          message: message ?? 'バリデーションエラー',
          errors: data is Map
              ? (data['errors'] as Map<String, dynamic>?)?.map(
                  (k, v) => MapEntry(k, (v as List).cast<String>()),
                )
              : null,
        );
      case 500:
      case 502:
      case 503:
      default:
        return Failure.server(
          message: message ?? 'サーバーエラーが発生しました',
          statusCode: statusCode,
        );
    }
  }
}
```

### 4.6 Repository Implementation の生成（例外版 - オプション）

例外版を選択した場合は以下のように生成します。

```dart
// lib/data/repositories/users_repository_impl.dart
import 'package:dio/dio.dart';

import '../../core/error/failures.dart';
import '../../domain/models/user.dart';
import '../../domain/models/create_user_dto.dart';
import '../../domain/models/update_user_dto.dart';
import '../../domain/repositories/users_repository.dart';
import '../api/users_api_service.dart';

/// ユーザーリポジトリの実装（例外版）
class UsersRepositoryImpl implements UsersRepository {
  final UsersApiService _apiService;

  UsersRepositoryImpl(this._apiService);

  @override
  Future<List<User>> getUsers({
    int? page,
    int? perPage,
  }) async {
    try {
      return await _apiService.getUsers(
        page: page,
        perPage: perPage,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  @override
  Future<User> getUser({
    required int id,
  }) async {
    try {
      return await _apiService.getUser(id: id);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // ... 他のメソッドも同様

  Failure _handleDioError(DioException e) {
    // Either版と同じ実装
  }
}
```

### 4.7 例外版の Repository Interface

例外版を選択した場合、インターフェースも変更します。

```dart
// lib/domain/repositories/users_repository.dart
import '../models/user.dart';
import '../models/create_user_dto.dart';
import '../models/update_user_dto.dart';

/// ユーザーリポジトリのインターフェース（例外版）
abstract interface class UsersRepository {
  Future<List<User>> getUsers({int? page, int? perPage});
  Future<User> getUser({required int id});
  Future<User> createUser({required CreateUserDto data});
  Future<User> updateUser({required int id, required UpdateUserDto data});
  Future<void> deleteUser({required int id});
}
```

## Output

生成されるファイル一覧：

```
lib/
├── core/
│   ├── error/
│   │   └── failures.dart
│   └── network/
│       └── dio_client.dart
├── domain/
│   └── repositories/
│       └── users_repository.dart
└── data/
    └── repositories/
        └── users_repository_impl.dart
```

## Checklist

- [ ] Failure クラスを生成した
- [ ] Dio Client を生成した
- [ ] すべてのAPIサービスに対応するリポジトリインターフェースを作成した
- [ ] すべてのリポジトリ実装を作成した
- [ ] エラーハンドリング（Either or 例外）を実装した
- [ ] DioExceptionの変換処理を実装した
- [ ] HTTPステータスコードの変換処理を実装した
- [ ] 必要なimportを設定した

## Next Step

リポジトリ生成完了後、Step 5（プロバイダ生成）に進みます。
