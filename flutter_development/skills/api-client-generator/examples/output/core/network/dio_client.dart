import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Dioクライアントの設定
class DioClient {
  late final Dio _dio;

  DioClient({
    required String baseUrl,
    Map<String, dynamic>? headers,
    Duration? connectTimeout,
    Duration? receiveTimeout,
    bool enableLogging = true,
  }) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        headers: headers ?? {'Content-Type': 'application/json'},
        connectTimeout: connectTimeout ?? const Duration(seconds: 30),
        receiveTimeout: receiveTimeout ?? const Duration(seconds: 30),
      ),
    );

    // デバッグモードでのみログを出力
    if (kDebugMode && enableLogging) {
      _dio.interceptors.add(
        LogInterceptor(
          requestBody: true,
          responseBody: true,
          logPrint: (obj) => debugPrint('[DIO] $obj'),
        ),
      );
    }
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
