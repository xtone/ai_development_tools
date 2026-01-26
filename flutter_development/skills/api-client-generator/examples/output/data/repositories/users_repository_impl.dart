import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';

import '../../core/error/failures.dart';
import '../../domain/models/user.dart';
import '../../domain/repositories/users_repository.dart';
import '../api/users_api_service.dart';

/// ユーザーリポジトリの実装
class UsersRepositoryImpl implements UsersRepository {
  final UsersApiService _apiService;

  UsersRepositoryImpl(this._apiService);

  @override
  Future<Either<Failure, List<User>>> getUsers() async {
    try {
      final result = await _apiService.getUsers();
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
