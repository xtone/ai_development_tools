# OpenAPI to Dart Type Mapping

このドキュメントは、OpenAPI仕様の型をDart型にマッピングするルールを定義します。

## Basic Type Mapping

| OpenAPI Type | OpenAPI Format | Dart Type | Notes |
|-------------|----------------|-----------|-------|
| `string` | - | `String` | 基本文字列型 |
| `string` | `date` | `DateTime` | 日付のみ |
| `string` | `date-time` | `DateTime` | 日時 |
| `string` | `email` | `String` | メールアドレス |
| `string` | `uri` | `String` | URI |
| `string` | `uuid` | `String` | UUID |
| `string` | `binary` | `List<int>` | バイナリデータ |
| `integer` | - | `int` | 整数 |
| `integer` | `int32` | `int` | 32ビット整数 |
| `integer` | `int64` | `int` | 64ビット整数 |
| `number` | - | `double` | 浮動小数点数 |
| `number` | `float` | `double` | 単精度浮動小数点数 |
| `number` | `double` | `double` | 倍精度浮動小数点数 |
| `boolean` | - | `bool` | 真偽値 |
| `array` | - | `List<T>` | 配列（Tは要素型） |
| `object` | - | `Map<String, dynamic>` or Custom Class | オブジェクト |

## Nullable Types

OpenAPIの`nullable: true`またはrequired配列に含まれないプロパティは、Dartでは`?`を付けてnullable型として表現します。

### Example

```yaml
# OpenAPI
properties:
  name:
    type: string
  nickname:
    type: string
    nullable: true
required:
  - name
```

```dart
// Dart
@freezed
class User with _$User {
  const factory User({
    required String name,
    String? nickname,
  }) = _User;
}
```

## Array Types

配列は`List<T>`として表現し、要素型は`items`から決定します。

### Example

```yaml
# OpenAPI
properties:
  tags:
    type: array
    items:
      type: string
  users:
    type: array
    items:
      $ref: '#/components/schemas/User'
```

```dart
// Dart
@freezed
class Response with _$Response {
  const factory Response({
    required List<String> tags,
    required List<User> users,
  }) = _Response;
}
```

## Object Types (Nested)

ネストされたオブジェクトは、別のFreezedクラスとして定義します。

### Example

```yaml
# OpenAPI
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        profile:
          $ref: '#/components/schemas/Profile'
    Profile:
      type: object
      properties:
        bio:
          type: string
```

```dart
// Dart - user.dart
@freezed
class User with _$User {
  const factory User({
    required int id,
    Profile? profile,
  }) = _User;
}

// Dart - profile.dart
@freezed
class Profile with _$Profile {
  const factory Profile({
    String? bio,
  }) = _Profile;
}
```

## Enum Types

`enum`プロパティはDartのenumとして定義し、`@JsonEnum`アノテーションを使用します。

### Example

```yaml
# OpenAPI
components:
  schemas:
    User:
      type: object
      properties:
        status:
          type: string
          enum: [active, inactive, pending]
```

```dart
// Dart
@JsonEnum(alwaysCreate: true)
enum UserStatus {
  @JsonValue('active')
  active,
  @JsonValue('inactive')
  inactive,
  @JsonValue('pending')
  pending,
}

@freezed
class User with _$User {
  const factory User({
    UserStatus? status,
  }) = _User;
}
```

## Reference Types ($ref)

`$ref`は参照先のスキーマに解決し、対応するDartクラス名を使用します。

### Example

```yaml
# OpenAPI
properties:
  author:
    $ref: '#/components/schemas/User'
```

```dart
// Dart
@freezed
class Post with _$Post {
  const factory Post({
    User? author,
  }) = _Post;
}
```

## AllOf / OneOf / AnyOf

### allOf (Composition)

`allOf`は全てのスキーマを結合した単一クラスとして生成します。

```yaml
# OpenAPI
schemas:
  Employee:
    allOf:
      - $ref: '#/components/schemas/Person'
      - type: object
        properties:
          employeeId:
            type: string
```

```dart
// Dart - すべてのプロパティを含むクラス
@freezed
class Employee with _$Employee {
  const factory Employee({
    // Personのプロパティ
    required String name,
    int? age,
    // 追加プロパティ
    String? employeeId,
  }) = _Employee;
}
```

### oneOf / anyOf (Union Types)

`oneOf`または`anyOf`はFreezedのunion typeとして生成します。

```yaml
# OpenAPI
schemas:
  Pet:
    oneOf:
      - $ref: '#/components/schemas/Cat'
      - $ref: '#/components/schemas/Dog'
```

```dart
// Dart
@freezed
sealed class Pet with _$Pet {
  const factory Pet.cat({
    required String name,
    required String meowSound,
  }) = Cat;

  const factory Pet.dog({
    required String name,
    required String barkSound,
  }) = Dog;
}
```

## Additional Properties

`additionalProperties`を持つオブジェクトは`Map<String, T>`として表現します。

```yaml
# OpenAPI
schemas:
  Metadata:
    type: object
    additionalProperties:
      type: string
```

```dart
// Dart
typedef Metadata = Map<String, String>;
```

## Property Name Conversion

OpenAPIのプロパティ名（snake_case）はDartの命名規則（camelCase）に変換し、`@JsonKey`で元の名前を指定します。

### Example

```yaml
# OpenAPI
properties:
  created_at:
    type: string
    format: date-time
  user_name:
    type: string
```

```dart
// Dart
@freezed
class User with _$User {
  const factory User({
    @JsonKey(name: 'created_at') DateTime? createdAt,
    @JsonKey(name: 'user_name') String? userName,
  }) = _User;
}
```

## Default Values

`default`値はFreezedのデフォルトパラメータとして設定します。

```yaml
# OpenAPI
properties:
  status:
    type: string
    default: 'active'
  count:
    type: integer
    default: 0
```

```dart
// Dart
@freezed
class Item with _$Item {
  const factory Item({
    @Default('active') String status,
    @Default(0) int count,
  }) = _Item;
}
```
