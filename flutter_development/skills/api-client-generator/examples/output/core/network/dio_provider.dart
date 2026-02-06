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
      defaultValue: 'https://api.example.com/v1',
    ),
  );
}
