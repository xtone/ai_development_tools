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
