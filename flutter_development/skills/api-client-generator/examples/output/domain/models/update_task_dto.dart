import 'package:freezed_annotation/freezed_annotation.dart';

import 'task_status.dart';

part 'update_task_dto.freezed.dart';
part 'update_task_dto.g.dart';

/// タスク更新リクエスト
@freezed
class UpdateTaskDto with _$UpdateTaskDto {
  const factory UpdateTaskDto({
    String? title,
    String? description,
    TaskStatus? status,
    int? priority,
    @JsonKey(name: 'assignee_id') int? assigneeId,
    @JsonKey(name: 'due_date') DateTime? dueDate,
  }) = _UpdateTaskDto;

  factory UpdateTaskDto.fromJson(Map<String, dynamic> json) =>
      _$UpdateTaskDtoFromJson(json);
}
