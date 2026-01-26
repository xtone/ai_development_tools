# Step 3: Generate API Service

このステップでは、OpenAPIのpathsからRetrofitベースのAPIサービスを生成します。

## Input

Step 1で抽出したエンドポイント情報

## Tasks

### 3.1 ディレクトリ構造の作成

```bash
mkdir -p lib/data/api
```

### 3.2 Tag別にAPIサービスを生成

各tagごとに1つのAPIサービスクラスを生成します。

### 3.3 Retrofitアノテーションの適用

#### 基本構造

```dart
// lib/data/api/users_api_service.dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../domain/models/user.dart';
import '../../domain/models/create_user_dto.dart';
import '../../domain/models/update_user_dto.dart';

part 'users_api_service.g.dart';

@RestApi()
abstract class UsersApiService {
  factory UsersApiService(Dio dio, {String baseUrl}) = _UsersApiService;

  // エンドポイントメソッド
}
```

### 3.4 HTTPメソッド別のテンプレート

#### GET - 一覧取得

```dart
  /// ユーザー一覧を取得
  @GET('/users')
  Future<List<User>> getUsers({
    @Query('page') int? page,
    @Query('per_page') int? perPage,
    @Query('sort') String? sort,
  });
```

#### GET - 単体取得

```dart
  /// 指定IDのユーザーを取得
  @GET('/users/{id}')
  Future<User> getUser({
    @Path('id') required int id,
  });
```

#### POST - 作成

```dart
  /// 新規ユーザーを作成
  @POST('/users')
  Future<User> createUser({
    @Body() required CreateUserDto body,
  });
```

#### PUT - 全体更新

```dart
  /// ユーザー情報を更新
  @PUT('/users/{id}')
  Future<User> updateUser({
    @Path('id') required int id,
    @Body() required UpdateUserDto body,
  });
```

#### PATCH - 部分更新

```dart
  /// ユーザー情報を部分更新
  @PATCH('/users/{id}')
  Future<User> patchUser({
    @Path('id') required int id,
    @Body() required UpdateUserDto body,
  });
```

#### DELETE - 削除

```dart
  /// ユーザーを削除
  @DELETE('/users/{id}')
  Future<void> deleteUser({
    @Path('id') required int id,
  });
```

### 3.5 パラメータの処理

#### Path Parameters

```yaml
# OpenAPI
/users/{id}:
  get:
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: integer
```

```dart
// Dart
@GET('/users/{id}')
Future<User> getUser({
  @Path('id') required int id,
});
```

#### Query Parameters

```yaml
# OpenAPI
/users:
  get:
    parameters:
      - name: page
        in: query
        schema:
          type: integer
      - name: status
        in: query
        required: true
        schema:
          type: string
```

```dart
// Dart
@GET('/users')
Future<List<User>> getUsers({
  @Query('page') int? page,
  @Query('status') required String status,
});
```

#### Header Parameters

```yaml
# OpenAPI
/users:
  get:
    parameters:
      - name: X-Custom-Header
        in: header
        required: true
        schema:
          type: string
```

```dart
// Dart
@GET('/users')
Future<List<User>> getUsers({
  @Header('X-Custom-Header') required String customHeader,
});
```

### 3.6 Request Body の処理

#### JSON Body

```yaml
# OpenAPI
/users:
  post:
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/CreateUserDto'
```

```dart
// Dart
@POST('/users')
Future<User> createUser({
  @Body() required CreateUserDto body,
});
```

#### Form Data

```yaml
# OpenAPI
/users/avatar:
  post:
    requestBody:
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              file:
                type: string
                format: binary
```

```dart
// Dart
@POST('/users/avatar')
@MultiPart()
Future<void> uploadAvatar({
  @Part() required File file,
});
```

### 3.7 Response の処理

#### 単一オブジェクト

```yaml
# OpenAPI
responses:
  '200':
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/User'
```

```dart
// Dart
Future<User> getUser(...);
```

#### 配列

```yaml
# OpenAPI
responses:
  '200':
    content:
      application/json:
        schema:
          type: array
          items:
            $ref: '#/components/schemas/User'
```

```dart
// Dart
Future<List<User>> getUsers(...);
```

#### void (204 No Content)

```yaml
# OpenAPI
responses:
  '204':
    description: No Content
```

```dart
// Dart
Future<void> deleteUser(...);
```

#### ページネーション

```yaml
# OpenAPI
responses:
  '200':
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/PaginatedUserResponse'
```

```dart
// Dart
Future<PaginatedResponse<User>> getUsers(...);
```

### 3.8 完成例

```dart
// lib/data/api/users_api_service.dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../domain/models/user.dart';
import '../../domain/models/create_user_dto.dart';
import '../../domain/models/update_user_dto.dart';

part 'users_api_service.g.dart';

/// ユーザー関連のAPIサービス
@RestApi()
abstract class UsersApiService {
  factory UsersApiService(Dio dio, {String baseUrl}) = _UsersApiService;

  /// ユーザー一覧を取得
  @GET('/users')
  Future<List<User>> getUsers({
    @Query('page') int? page,
    @Query('per_page') int? perPage,
  });

  /// 指定IDのユーザーを取得
  @GET('/users/{id}')
  Future<User> getUser({
    @Path('id') required int id,
  });

  /// 新規ユーザーを作成
  @POST('/users')
  Future<User> createUser({
    @Body() required CreateUserDto body,
  });

  /// ユーザー情報を更新
  @PUT('/users/{id}')
  Future<User> updateUser({
    @Path('id') required int id,
    @Body() required UpdateUserDto body,
  });

  /// ユーザーを削除
  @DELETE('/users/{id}')
  Future<void> deleteUser({
    @Path('id') required int id,
  });
}
```

## Output

生成されるファイル一覧：

```
lib/data/api/
├── users_api_service.dart
├── posts_api_service.dart
└── comments_api_service.dart
```

## Checklist

- [ ] すべてのtagに対応するAPIサービスを作成した
- [ ] HTTPメソッド（GET/POST/PUT/PATCH/DELETE）を正しく設定した
- [ ] パスパラメータに@Pathを適用した
- [ ] クエリパラメータに@Queryを適用した
- [ ] リクエストボディに@Bodyを適用した
- [ ] 戻り値の型を正しく設定した
- [ ] 必要なモデルをimportした
- [ ] part文を正しく設定した

## Next Step

APIサービス生成完了後、Step 4（リポジトリ生成）に進みます。
