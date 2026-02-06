import 'package:freezed_annotation/freezed_annotation.dart';

import 'task_status.dart';
import 'user.dart';

part 'task.freezed.dart';
part 'task.g.dart';

/// タスク情報
@freezed
class Task with _$Task {
  const factory Task({
    required int id,
    required String title,
    String? description,
    required TaskStatus status,
    @Default(0) int priority,
    User? assignee,
    @JsonKey(name: 'due_date') DateTime? dueDate,
    @JsonKey(name: 'created_at') DateTime? createdAt,
    @JsonKey(name: 'updated_at') DateTime? updatedAt,
  }) = _Task;

  factory Task.fromJson(Map<String, dynamic> json) => _$TaskFromJson(json);
}
