# API Client Generator Examples

このディレクトリには、スキルの入出力例が含まれています。few-shot promptingの参考として使用してください。

## ディレクトリ構成

```
examples/
├── sample_api.yaml      # 入力: OpenAPI仕様
└── output/              # 出力: 生成されたDartコード
    ├── core/
    ├── data/
    ├── domain/
    └── presentation/
```

## 入力例: sample_api.yaml

タスク管理APIの仕様（OpenAPI 3.0）

### 含まれるスキーマ
- `Task` - タスクモデル（id, title, status, assignee等）
- `TaskStatus` - enum型（pending, in_progress, completed）
- `CreateTaskDto` - 作成リクエスト
- `UpdateTaskDto` - 更新リクエスト
- `User` - ユーザーモデル

### 含まれるエンドポイント
| Tag | Method | Path | OperationId |
|-----|--------|------|-------------|
| tasks | GET | /tasks | getTasks |
| tasks | POST | /tasks | createTask |
| tasks | GET | /tasks/{id} | getTask |
| tasks | PUT | /tasks/{id} | updateTask |
| tasks | DELETE | /tasks/{id} | deleteTask |
| users | GET | /users | getUsers |
| users | GET | /users/{id} | getUser |

## 出力例: output/

### 生成されたファイル

#### Models (5 files)
- `domain/models/task.dart` - Freezedモデル
- `domain/models/task_status.dart` - Enum型
- `domain/models/create_task_dto.dart` - 作成DTO
- `domain/models/update_task_dto.dart` - 更新DTO
- `domain/models/user.dart` - Freezedモデル

#### API Services (2 files)
- `data/api/tasks_api_service.dart` - Retrofitサービス
- `data/api/users_api_service.dart` - Retrofitサービス

#### Repositories (4 files)
- `domain/repositories/tasks_repository.dart` - インターフェース
- `domain/repositories/users_repository.dart` - インターフェース
- `data/repositories/tasks_repository_impl.dart` - Either型実装
- `data/repositories/users_repository_impl.dart` - Either型実装

#### Providers (2 files)
- `presentation/providers/tasks_providers.dart` - Query + Mutation
- `presentation/providers/users_providers.dart` - Query

#### Core (3 files)
- `core/error/failures.dart` - Failure型定義
- `core/network/dio_client.dart` - Dioクライアント
- `core/network/dio_provider.dart` - Dioプロバイダ

## 使用方法

このサンプルを参考に、実際のOpenAPI仕様から同様のコードを生成してください。

### 型マッピングの例

```yaml
# OpenAPI
due_date:
  type: string
  format: date-time
```

```dart
// Dart
@JsonKey(name: 'due_date') DateTime? dueDate,
```

### Enumの例

```yaml
# OpenAPI
TaskStatus:
  type: string
  enum: [pending, in_progress, completed]
```

```dart
// Dart
@JsonEnum(alwaysCreate: true)
enum TaskStatus {
  @JsonValue('pending')
  pending,
  @JsonValue('in_progress')
  inProgress,
  @JsonValue('completed')
  completed,
}
```

### 参照型の例

```yaml
# OpenAPI
assignee:
  $ref: '#/components/schemas/User'
```

```dart
// Dart
User? assignee,
```
