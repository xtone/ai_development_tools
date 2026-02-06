import 'package:dartz/dartz.dart';

import '../models/task.dart';
import '../models/task_status.dart';
import '../models/create_task_dto.dart';
import '../models/update_task_dto.dart';
import '../../core/error/failures.dart';

/// タスクリポジトリのインターフェース
abstract interface class TasksRepository {
  /// タスク一覧を取得
  Future<Either<Failure, List<Task>>> getTasks({
    TaskStatus? status,
    int? page,
    int? perPage,
  });

  /// 指定IDのタスクを取得
  Future<Either<Failure, Task>> getTask({
    required int id,
  });

  /// 新規タスクを作成
  Future<Either<Failure, Task>> createTask({
    required CreateTaskDto data,
  });

  /// タスクを更新
  Future<Either<Failure, Task>> updateTask({
    required int id,
    required UpdateTaskDto data,
  });

  /// タスクを削除
  Future<Either<Failure, void>> deleteTask({
    required int id,
  });
}
