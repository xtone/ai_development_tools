# Step 2: Generate Models

このステップでは、OpenAPIのスキーマからFreezedベースのDartモデルを生成します。

## Input

Step 1で抽出したスキーマ情報

## Tasks

### 2.1 ディレクトリ構造の作成

```bash
mkdir -p lib/domain/models
```

### 2.2 型マッピングの適用

`references/01_openapi_mapping.md`に従って、OpenAPI型をDart型に変換します。

```yaml
# OpenAPI
properties:
  id:
    type: integer
  name:
    type: string
  email:
    type: string
    format: email
  created_at:
    type: string
    format: date-time
```

↓

```dart
// Dart
required int id,
required String name,
required String email,
@JsonKey(name: 'created_at') DateTime? createdAt,
```

### 2.3 Freezed モデルの生成

#### 基本モデル

```dart
// lib/domain/models/user.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

/// ユーザー情報
@freezed
class User with _$User {
  const factory User({
    required int id,
    required String name,
    required String email,
    @JsonKey(name: 'created_at') DateTime? createdAt,
    @JsonKey(name: 'updated_at') DateTime? updatedAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
```

#### Enum型

```dart
// lib/domain/models/user_status.dart
import 'package:json_annotation/json_annotation.dart';

@JsonEnum(alwaysCreate: true)
enum UserStatus {
  @JsonValue('active')
  active,
  @JsonValue('inactive')
  inactive,
  @JsonValue('pending')
  pending,
}
```

#### Enum型をモデル内で使用

```dart
// lib/domain/models/user.dart
import 'package:freezed_annotation/freezed_annotation.dart';

import 'user_status.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const factory User({
    required int id,
    required String name,
    @Default(UserStatus.active) UserStatus status,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
```

### 2.4 Request/Response モデル

API操作用の専用モデルを生成します。

#### Create DTO

```dart
// lib/domain/models/create_user_dto.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'create_user_dto.freezed.dart';
part 'create_user_dto.g.dart';

/// ユーザー作成リクエスト
@freezed
class CreateUserDto with _$CreateUserDto {
  const factory CreateUserDto({
    required String name,
    required String email,
    String? password,
  }) = _CreateUserDto;

  factory CreateUserDto.fromJson(Map<String, dynamic> json) =>
      _$CreateUserDtoFromJson(json);
}
```

#### Update DTO

```dart
// lib/domain/models/update_user_dto.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'update_user_dto.freezed.dart';
part 'update_user_dto.g.dart';

/// ユーザー更新リクエスト
@freezed
class UpdateUserDto with _$UpdateUserDto {
  const factory UpdateUserDto({
    String? name,
    String? email,
  }) = _UpdateUserDto;

  factory UpdateUserDto.fromJson(Map<String, dynamic> json) =>
      _$UpdateUserDtoFromJson(json);
}
```

#### Paginated Response

```dart
// lib/domain/models/paginated_response.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'paginated_response.freezed.dart';
part 'paginated_response.g.dart';

@Freezed(genericArgumentFactories: true)
class PaginatedResponse<T> with _$PaginatedResponse<T> {
  const factory PaginatedResponse({
    required List<T> data,
    required int total,
    required int page,
    @JsonKey(name: 'per_page') required int perPage,
    @JsonKey(name: 'last_page') required int lastPage,
  }) = _PaginatedResponse<T>;

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object?) fromJsonT,
  ) =>
      _$PaginatedResponseFromJson(json, fromJsonT);
}
```

### 2.5 ネストしたオブジェクトの処理

#### 参照型（$ref）

参照先のモデルをimportして使用します。

```dart
// lib/domain/models/post.dart
import 'package:freezed_annotation/freezed_annotation.dart';

import 'user.dart';

part 'post.freezed.dart';
part 'post.g.dart';

@freezed
class Post with _$Post {
  const factory Post({
    required int id,
    required String title,
    required String content,
    User? author,  // $ref: '#/components/schemas/User'
  }) = _Post;

  factory Post.fromJson(Map<String, dynamic> json) => _$PostFromJson(json);
}
```

#### インラインオブジェクト

インラインで定義されたオブジェクトは別クラスとして抽出します。

```yaml
# OpenAPI
Post:
  properties:
    metadata:
      type: object
      properties:
        views:
          type: integer
        likes:
          type: integer
```

```dart
// lib/domain/models/post_metadata.dart
@freezed
class PostMetadata with _$PostMetadata {
  const factory PostMetadata({
    int? views,
    int? likes,
  }) = _PostMetadata;

  factory PostMetadata.fromJson(Map<String, dynamic> json) =>
      _$PostMetadataFromJson(json);
}

// lib/domain/models/post.dart
@freezed
class Post with _$Post {
  const factory Post({
    required int id,
    PostMetadata? metadata,
  }) = _Post;
  // ...
}
```

### 2.6 Union Types (oneOf/anyOf)

```dart
// lib/domain/models/notification.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'notification.freezed.dart';
part 'notification.g.dart';

@freezed
sealed class Notification with _$Notification {
  const factory Notification.email({
    required String subject,
    required String body,
  }) = EmailNotification;

  const factory Notification.push({
    required String title,
    required String message,
  }) = PushNotification;

  const factory Notification.sms({
    required String phoneNumber,
    required String text,
  }) = SmsNotification;

  factory Notification.fromJson(Map<String, dynamic> json) =>
      _$NotificationFromJson(json);
}
```

### 2.7 バレルファイルの作成（オプション）

```dart
// lib/domain/models/models.dart
export 'user.dart';
export 'user_status.dart';
export 'create_user_dto.dart';
export 'update_user_dto.dart';
export 'post.dart';
export 'post_metadata.dart';
```

## Output

生成されるファイル一覧：

```
lib/domain/models/
├── user.dart
├── user_status.dart
├── create_user_dto.dart
├── update_user_dto.dart
├── post.dart
├── post_metadata.dart
└── models.dart (バレルファイル)
```

## Checklist

- [ ] すべてのスキーマに対応するモデルファイルを作成した
- [ ] 型マッピングを正しく適用した
- [ ] snake_case → camelCase変換と@JsonKeyを適用した
- [ ] required/nullable を正しく設定した
- [ ] enum型を@JsonEnumで定義した
- [ ] 参照型（$ref）を正しく解決した
- [ ] インラインオブジェクトを別クラスとして抽出した
- [ ] part文とimport文を正しく設定した

## Next Step

モデル生成完了後、Step 3（APIサービス生成）に進みます。
