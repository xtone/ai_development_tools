# Code Templates

このドキュメントは、APIクライアント生成で使用するコードテンプレートを定義します。

## 1. Freezed Model Template

### Basic Model

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part '{model_name}.freezed.dart';
part '{model_name}.g.dart';

/// {description}
@freezed
class {ClassName} with _${ClassName} {
  const factory {ClassName}({
    {fields}
  }) = _{ClassName};

  factory {ClassName}.fromJson(Map<String, dynamic> json) =>
      _${ClassName}FromJson(json);
}
```

### Field Formats

```dart
// Required field
required {Type} {fieldName},

// Optional field
{Type}? {fieldName},

// Required field with JsonKey
@JsonKey(name: '{original_name}') required {Type} {fieldName},

// Optional field with JsonKey
@JsonKey(name: '{original_name}') {Type}? {fieldName},

// Field with default value
@Default({defaultValue}) {Type} {fieldName},
```

### Enum Template

```dart
import 'package:json_annotation/json_annotation.dart';

@JsonEnum(alwaysCreate: true)
enum {EnumName} {
  @JsonValue('{value1}')
  {dartValue1},
  @JsonValue('{value2}')
  {dartValue2},
  // ...
}
```

## 2. Retrofit API Service Template

```dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

part '{tag}_api_service.g.dart';

@RestApi()
abstract class {Tag}ApiService {
  factory {Tag}ApiService(Dio dio, {String baseUrl}) = _{Tag}ApiService;

  {methods}
}
```

### Method Templates

#### GET Request (List)

```dart
  @GET('{path}')
  Future<List<{Model}>> {operationId}({
    {queryParameters}
  });
```

#### GET Request (Single)

```dart
  @GET('{path}')
  Future<{Model}> {operationId}({
    {pathParameters}
    {queryParameters}
  });
```

#### POST Request

```dart
  @POST('{path}')
  Future<{ResponseModel}> {operationId}({
    @Body() required {RequestModel} body,
  });
```

#### PUT Request

```dart
  @PUT('{path}')
  Future<{ResponseModel}> {operationId}({
    {pathParameters}
    @Body() required {RequestModel} body,
  });
```

#### PATCH Request

```dart
  @PATCH('{path}')
  Future<{ResponseModel}> {operationId}({
    {pathParameters}
    @Body() required {RequestModel} body,
  });
```

#### DELETE Request

```dart
  @DELETE('{path}')
  Future<void> {operationId}({
    {pathParameters}
  });
```

### Parameter Templates

```dart
// Path parameter
@Path('{paramName}') required {Type} {paramName},

// Query parameter (required)
@Query('{paramName}') required {Type} {paramName},

// Query parameter (optional)
@Query('{paramName}') {Type}? {paramName},

// Header parameter
@Header('{headerName}') required String {headerName},
```

## 3. Failure Classes Template

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'failures.freezed.dart';

@freezed
sealed class Failure with _$Failure {
  const factory Failure.server({
    required String message,
    int? statusCode,
  }) = ServerFailure;

  const factory Failure.network({
    required String message,
  }) = NetworkFailure;

  const factory Failure.cache({
    required String message,
  }) = CacheFailure;

  const factory Failure.validation({
    required String message,
    Map<String, List<String>>? errors,
  }) = ValidationFailure;

  const factory Failure.unauthorized({
    String? message,
  }) = UnauthorizedFailure;

  const factory Failure.notFound({
    String? message,
  }) = NotFoundFailure;

  const factory Failure.unknown({
    String? message,
    Object? error,
  }) = UnknownFailure;
}
```

## 4. Dio Client Template

```dart
import 'package:dio/dio.dart';

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
      ),
    ]);
  }

  Dio get dio => _dio;

  void addInterceptor(Interceptor interceptor) {
    _dio.interceptors.add(interceptor);
  }

  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  void clearAuthToken() {
    _dio.options.headers.remove('Authorization');
  }
}
```

## 5. Repository Interface Template

```dart
import 'package:dartz/dartz.dart';

import '../models/{model}.dart';
import '../../core/error/failures.dart';

abstract interface class {Tag}Repository {
  {methods}
}
```

### Method Templates (Either)

```dart
  // List
  Future<Either<Failure, List<{Model}>>> get{Models}({parameters});

  // Single
  Future<Either<Failure, {Model}>> get{Model}({parameters});

  // Create
  Future<Either<Failure, {Model}>> create{Model}({required {CreateModel} data});

  // Update
  Future<Either<Failure, {Model}>> update{Model}({
    required {idType} id,
    required {UpdateModel} data,
  });

  // Delete
  Future<Either<Failure, void>> delete{Model}({required {idType} id});
```

## 6. Repository Implementation Template (Either版)

```dart
import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';

import '../../core/error/failures.dart';
import '../../domain/models/{model}.dart';
import '../../domain/repositories/{tag}_repository.dart';
import '../api/{tag}_api_service.dart';

class {Tag}RepositoryImpl implements {Tag}Repository {
  final {Tag}ApiService _apiService;

  {Tag}RepositoryImpl(this._apiService);

  {methods}
}
```

### Implementation Method Templates (Either)

```dart
  @override
  Future<Either<Failure, List<{Model}>>> get{Models}({parameters}) async {
    try {
      final result = await _apiService.{operationId}({arguments});
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, {Model}>> get{Model}({parameters}) async {
    try {
      final result = await _apiService.{operationId}({arguments});
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, {Model}>> create{Model}({required {CreateModel} data}) async {
    try {
      final result = await _apiService.{operationId}(body: data);
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, void>> delete{Model}({required {idType} id}) async {
    try {
      await _apiService.{operationId}(id: id);
      return const Right(null);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  Failure _handleDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const Failure.network(message: 'Connection timeout');
      case DioExceptionType.connectionError:
        return const Failure.network(message: 'No internet connection');
      case DioExceptionType.badResponse:
        return _handleStatusCode(e.response?.statusCode, e.response?.data);
      default:
        return Failure.unknown(message: e.message, error: e);
    }
  }

  Failure _handleStatusCode(int? statusCode, dynamic data) {
    final message = data is Map ? data['message'] as String? : null;
    switch (statusCode) {
      case 400:
        return Failure.validation(
          message: message ?? 'Bad request',
          errors: data is Map ? data['errors'] as Map<String, List<String>>? : null,
        );
      case 401:
        return Failure.unauthorized(message: message);
      case 404:
        return Failure.notFound(message: message);
      case 500:
      default:
        return Failure.server(
          message: message ?? 'Server error',
          statusCode: statusCode,
        );
    }
  }
```

## 7. Repository Implementation Template (例外版)

```dart
import 'package:dio/dio.dart';

import '../../core/error/failures.dart';
import '../../domain/models/{model}.dart';
import '../../domain/repositories/{tag}_repository.dart';
import '../api/{tag}_api_service.dart';

class {Tag}RepositoryImpl implements {Tag}Repository {
  final {Tag}ApiService _apiService;

  {Tag}RepositoryImpl(this._apiService);

  {methods}
}
```

### Implementation Method Templates (例外版)

```dart
  @override
  Future<List<{Model}>> get{Models}({parameters}) async {
    try {
      return await _apiService.{operationId}({arguments});
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Failure _handleDioError(DioException e) {
    // Same as Either version
  }
```

## 8. Riverpod Provider Template

```dart
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../core/network/dio_client.dart';
import '../../data/api/{tag}_api_service.dart';
import '../../data/repositories/{tag}_repository_impl.dart';
import '../../domain/models/{model}.dart';
import '../../domain/repositories/{tag}_repository.dart';

part '{tag}_providers.g.dart';

// API Service Provider
@riverpod
{Tag}ApiService {tag}ApiService({Tag}ApiServiceRef ref) {
  final dioClient = ref.watch(dioClientProvider);
  return {Tag}ApiService(dioClient.dio);
}

// Repository Provider
@riverpod
{Tag}Repository {tag}Repository({Tag}RepositoryRef ref) {
  final apiService = ref.watch({tag}ApiServiceProvider);
  return {Tag}RepositoryImpl(apiService);
}

// List Provider
@riverpod
Future<List<{Model}>> {models}({Models}Ref ref) async {
  final repository = ref.watch({tag}RepositoryProvider);
  final result = await repository.get{Models}();
  return result.fold(
    (failure) => throw failure,
    (data) => data,
  );
}

// Single Item Provider (with Family)
@riverpod
Future<{Model}> {model}({Model}Ref ref, {idType} id) async {
  final repository = ref.watch({tag}RepositoryProvider);
  final result = await repository.get{Model}(id: id);
  return result.fold(
    (failure) => throw failure,
    (data) => data,
  );
}
```

## 9. Dio Client Provider Template

```dart
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'dio_client.dart';

part 'dio_provider.g.dart';

@Riverpod(keepAlive: true)
DioClient dioClient(DioClientRef ref) {
  return DioClient(
    baseUrl: const String.fromEnvironment('API_BASE_URL'),
  );
}
```
