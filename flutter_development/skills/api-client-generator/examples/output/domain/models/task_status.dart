import 'package:json_annotation/json_annotation.dart';

/// タスクのステータス
@JsonEnum(alwaysCreate: true)
enum TaskStatus {
  @JsonValue('pending')
  pending,
  @JsonValue('in_progress')
  inProgress,
  @JsonValue('completed')
  completed,
}
