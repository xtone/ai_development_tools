import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../core/network/dio_provider.dart';
import '../../data/api/users_api_service.dart';
import '../../data/repositories/users_repository_impl.dart';
import '../../domain/models/user.dart';
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
