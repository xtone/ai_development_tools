import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';

import '../../core/error/failures.dart';
import '../../domain/models/task.dart';
import '../../domain/models/task_status.dart';
import '../../domain/models/create_task_dto.dart';
import '../../domain/models/update_task_dto.dart';
import '../../domain/repositories/tasks_repository.dart';
import '../api/tasks_api_service.dart';

/// タスクリポジトリの実装
class TasksRepositoryImpl implements TasksRepository {
  final TasksApiService _apiService;

  TasksRepositoryImpl(this._apiService);

  @override
  Future<Either<Failure, List<Task>>> getTasks({
    TaskStatus? status,
    int? page,
    int? perPage,
  }) async {
    try {
      final result = await _apiService.getTasks(
        status: status,
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
  Future<Either<Failure, Task>> getTask({
    required int id,
  }) async {
    try {
      final result = await _apiService.getTask(id: id);
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, Task>> createTask({
    required CreateTaskDto data,
  }) async {
    try {
      final result = await _apiService.createTask(body: data);
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, Task>> updateTask({
    required int id,
    required UpdateTaskDto data,
  }) async {
    try {
      final result = await _apiService.updateTask(id: id, body: data);
      return Right(result);
    } on DioException catch (e) {
      return Left(_handleDioError(e));
    } catch (e) {
      return Left(Failure.unknown(error: e));
    }
  }

  @override
  Future<Either<Failure, void>> deleteTask({
    required int id,
  }) async {
    try {
      await _apiService.deleteTask(id: id);
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
        return _validationError(message ?? 'リクエストが不正です', data);
      case 401:
        return Failure.unauthorized(message: message);
      case 403:
        return Failure.unauthorized(message: message ?? 'アクセス権限がありません');
      case 404:
        return Failure.notFound(message: message);
      case 422:
        return _validationError(message ?? 'バリデーションエラー', data);
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

  /// バリデーションエラーを生成（型安全な変換）
  Failure _validationError(String message, dynamic data) {
    return Failure.validation(
      message: message,
      errors: data is Map && data['errors'] is Map<String, dynamic>
          ? (data['errors'] as Map<String, dynamic>).map(
              (k, v) => MapEntry(
                k,
                v is List ? v.map((e) => e.toString()).toList() : <String>[],
              ),
            )
          : null,
    );
  }
}
