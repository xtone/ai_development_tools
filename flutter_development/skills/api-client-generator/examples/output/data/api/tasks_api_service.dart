import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../domain/models/task.dart';
import '../../domain/models/task_status.dart';
import '../../domain/models/create_task_dto.dart';
import '../../domain/models/update_task_dto.dart';

part 'tasks_api_service.g.dart';

/// タスク関連のAPIサービス
@RestApi()
abstract class TasksApiService {
  factory TasksApiService(Dio dio, {String baseUrl}) = _TasksApiService;

  /// タスク一覧を取得
  @GET('/tasks')
  Future<List<Task>> getTasks({
    @Query('status') TaskStatus? status,
    @Query('page') int? page,
    @Query('per_page') int? perPage,
  });

  /// 新規タスクを作成
  @POST('/tasks')
  Future<Task> createTask({
    @Body() required CreateTaskDto body,
  });

  /// 指定IDのタスクを取得
  @GET('/tasks/{id}')
  Future<Task> getTask({
    @Path('id') required int id,
  });

  /// タスクを更新
  @PUT('/tasks/{id}')
  Future<Task> updateTask({
    @Path('id') required int id,
    @Body() required UpdateTaskDto body,
  });

  /// タスクを削除
  @DELETE('/tasks/{id}')
  Future<void> deleteTask({
    @Path('id') required int id,
  });
}
