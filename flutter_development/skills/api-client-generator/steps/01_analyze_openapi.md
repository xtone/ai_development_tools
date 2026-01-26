# Step 1: OpenAPI Specification Analysis

このステップでは、OpenAPI仕様ファイルを解析し、生成対象を特定します。

## Input

ユーザーから提供されるOpenAPI仕様ファイル（YAML/JSON）

## Tasks

### 1.1 ファイルの読み込みと検証

```
1. OpenAPIファイルを読み込む
2. OpenAPI 3.x形式であることを確認
3. 必須セクション（info, paths, components）の存在を確認
```

### 1.2 Schemas の抽出

`components.schemas`からモデル定義を抽出します。

```yaml
# 抽出対象
components:
  schemas:
    User:           # → User モデル
    Post:           # → Post モデル
    CreateUserDto:  # → CreateUserDto モデル（リクエスト用）
    UserResponse:   # → UserResponse モデル（レスポンス用）
```

#### 各スキーマから抽出する情報

| 項目 | 説明 |
|-----|------|
| スキーマ名 | クラス名として使用 |
| type | object / enum / その他 |
| properties | フィールド定義 |
| required | 必須フィールド一覧 |
| enum | 列挙値（enum型の場合） |
| allOf / oneOf / anyOf | 複合型定義 |
| $ref | 参照先 |

### 1.3 Paths の抽出

`paths`からエンドポイント定義を抽出します。

```yaml
# 抽出対象
paths:
  /users:
    get:            # → GET /users
    post:           # → POST /users
  /users/{id}:
    get:            # → GET /users/{id}
    put:            # → PUT /users/{id}
    delete:         # → DELETE /users/{id}
```

#### 各エンドポイントから抽出する情報

| 項目 | 説明 |
|-----|------|
| path | エンドポイントURL |
| method | HTTP メソッド |
| operationId | メソッド名として使用 |
| tags | APIサービスのグルーピング |
| parameters | パス/クエリパラメータ |
| requestBody | リクエストボディのスキーマ |
| responses | レスポンスのスキーマ |

### 1.4 Tags によるグルーピング

`tags`を使用してエンドポイントをグルーピングし、APIサービス単位を決定します。

```yaml
# 例
paths:
  /users:
    get:
      tags: [users]       # → UsersApiService
  /posts:
    get:
      tags: [posts]       # → PostsApiService
  /posts/{id}/comments:
    get:
      tags: [comments]    # → CommentsApiService
```

**グルーピングルール：**
- 同じtagを持つエンドポイントは同一APIサービスにまとめる
- tagが未指定の場合は`default`として扱う
- tagは`PascalCase`に変換してクラス名に使用

### 1.5 依存関係の解析

`$ref`参照を解決し、モデル間の依存関係を特定します。

```yaml
# 例
User:
  properties:
    profile:
      $ref: '#/components/schemas/Profile'  # UserはProfileに依存
```

### 1.6 生成ファイル一覧の決定

解析結果から生成するファイル一覧を決定します。

## Output

解析結果を以下の形式で整理します。

### Models

```markdown
## 生成対象モデル

| モデル名 | 種別 | フィールド数 | 依存先 | 生成ファイル |
|---------|------|-------------|--------|-------------|
| User | object | 5 | Profile | lib/domain/models/user.dart |
| Profile | object | 3 | - | lib/domain/models/profile.dart |
| UserStatus | enum | 3 | - | lib/domain/models/user_status.dart |
| CreateUserDto | object | 3 | - | lib/domain/models/create_user_dto.dart |
```

### Endpoints

```markdown
## 生成対象エンドポイント

### users (UsersApiService)

| Method | Path | OperationId | Request | Response |
|--------|------|-------------|---------|----------|
| GET | /users | getUsers | - | List<User> |
| GET | /users/{id} | getUser | - | User |
| POST | /users | createUser | CreateUserDto | User |
| PUT | /users/{id} | updateUser | UpdateUserDto | User |
| DELETE | /users/{id} | deleteUser | - | void |
```

### Generated Files

```markdown
## 生成ファイル一覧

### Models
- lib/domain/models/user.dart
- lib/domain/models/profile.dart
- lib/domain/models/user_status.dart
- lib/domain/models/create_user_dto.dart

### API Services
- lib/data/api/users_api_service.dart

### Repositories
- lib/domain/repositories/users_repository.dart
- lib/data/repositories/users_repository_impl.dart

### Providers
- lib/presentation/providers/users_providers.dart

### Core
- lib/core/error/failures.dart
- lib/core/network/dio_client.dart
- lib/core/network/dio_provider.dart
```

## Checklist

- [ ] OpenAPIファイルを読み込んだ
- [ ] components.schemasからモデル一覧を抽出した
- [ ] pathsからエンドポイント一覧を抽出した
- [ ] tagsによるグルーピングを行った
- [ ] $ref参照を解決した
- [ ] 生成ファイル一覧を決定した
- [ ] 解析結果をユーザーに提示し確認を得た

## Next Step

解析結果の確認後、Step 2（モデル生成）に進みます。
