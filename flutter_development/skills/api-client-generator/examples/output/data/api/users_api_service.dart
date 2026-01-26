import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../domain/models/user.dart';

part 'users_api_service.g.dart';

/// ユーザー関連のAPIサービス
@RestApi()
abstract class UsersApiService {
  factory UsersApiService(Dio dio, {String baseUrl}) = _UsersApiService;

  /// ユーザー一覧を取得
  @GET('/users')
  Future<List<User>> getUsers();

  /// 指定IDのユーザーを取得
  @GET('/users/{id}')
  Future<User> getUser({
    @Path('id') required int id,
  });
}
