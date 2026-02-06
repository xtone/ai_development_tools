import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../core/network/dio_provider.dart';
import '../../data/api/tasks_api_service.dart';
import '../../data/repositories/tasks_repository_impl.dart';
import '../../domain/models/task.dart';
import '../../domain/models/task_status.dart';
import '../../domain/models/create_task_dto.dart';
import '../../domain/models/update_task_dto.dart';
import '../../domain/repositories/tasks_repository.dart';

part 'tasks_providers.g.dart';

// =============================================================================
// Infrastructure Providers
// =============================================================================

/// TasksApiServiceのプロバイダ
@riverpod
TasksApiService tasksApiService(TasksApiServiceRef ref) {
  final dioClient = ref.watch(dioClientProvider);
  return TasksApiService(dioClient.dio);
}

/// TasksRepositoryのプロバイダ
@riverpod
TasksRepository tasksRepository(TasksRepositoryRef ref) {
  final apiService = ref.watch(tasksApiServiceProvider);
  return TasksRepositoryImpl(apiService);
}

// =============================================================================
// Query Providers
// =============================================================================

/// タスク一覧を取得するプロバイダ
@riverpod
Future<List<Task>> tasks(
  TasksRef ref, {
  TaskStatus? status,
  int? page,
  int? perPage,
}) async {
  final repository = ref.watch(tasksRepositoryProvider);
  final result = await repository.getTasks(
    status: status,
    page: page,
    perPage: perPage,
  );
  return result.fold(
    (failure) => throw failure,
    (tasks) => tasks,
  );
}

/// 指定IDのタスクを取得するプロバイダ
@riverpod
Future<Task> task(TaskRef ref, int id) async {
  final repository = ref.watch(tasksRepositoryProvider);
  final result = await repository.getTask(id: id);
  return result.fold(
    (failure) => throw failure,
    (task) => task,
  );
}

// =============================================================================
// Mutation Providers
// =============================================================================

/// タスク作成のNotifierプロバイダ
@riverpod
class CreateTask extends _$CreateTask {
  @override
  AsyncValue<Task?> build() => const AsyncData(null);

  Future<void> execute(CreateTaskDto data) async {
    state = const AsyncLoading();
    final repository = ref.read(tasksRepositoryProvider);
    final result = await repository.createTask(data: data);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (task) {
        // 一覧を再取得
        ref.invalidate(tasksProvider);
        return AsyncData(task);
      },
    );
  }
}

/// タスク更新のNotifierプロバイダ
@riverpod
class UpdateTask extends _$UpdateTask {
  @override
  AsyncValue<Task?> build() => const AsyncData(null);

  Future<void> execute({
    required int id,
    required UpdateTaskDto data,
  }) async {
    state = const AsyncLoading();
    final repository = ref.read(tasksRepositoryProvider);
    final result = await repository.updateTask(id: id, data: data);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (task) {
        // 関連プロバイダを再取得
        ref.invalidate(tasksProvider);
        ref.invalidate(taskProvider(id));
        return AsyncData(task);
      },
    );
  }
}

/// タスク削除のNotifierプロバイダ
@riverpod
class DeleteTask extends _$DeleteTask {
  @override
  AsyncValue<void> build() => const AsyncData(null);

  Future<void> execute(int id) async {
    state = const AsyncLoading();
    final repository = ref.read(tasksRepositoryProvider);
    final result = await repository.deleteTask(id: id);
    state = result.fold(
      (failure) => AsyncError(failure, StackTrace.current),
      (_) {
        // 一覧を再取得
        ref.invalidate(tasksProvider);
        return const AsyncData(null);
      },
    );
  }
}
