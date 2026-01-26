import 'package:freezed_annotation/freezed_annotation.dart';

part 'create_task_dto.freezed.dart';
part 'create_task_dto.g.dart';

/// タスク作成リクエスト
@freezed
class CreateTaskDto with _$CreateTaskDto {
  const factory CreateTaskDto({
    required String title,
    String? description,
    int? priority,
    @JsonKey(name: 'assignee_id') int? assigneeId,
    @JsonKey(name: 'due_date') DateTime? dueDate,
  }) = _CreateTaskDto;

  factory CreateTaskDto.fromJson(Map<String, dynamic> json) =>
      _$CreateTaskDtoFromJson(json);
}
