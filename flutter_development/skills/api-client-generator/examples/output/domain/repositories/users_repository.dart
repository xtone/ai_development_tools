import 'package:dartz/dartz.dart';

import '../models/user.dart';
import '../../core/error/failures.dart';

/// ユーザーリポジトリのインターフェース
abstract interface class UsersRepository {
  /// ユーザー一覧を取得
  Future<Either<Failure, List<User>>> getUsers();

  /// 指定IDのユーザーを取得
  Future<Either<Failure, User>> getUser({
    required int id,
  });
}
