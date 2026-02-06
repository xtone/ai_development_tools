---
name: api-client-generator
description: Generate Flutter API client code from OpenAPI/Swagger specifications. Creates type-safe models, Retrofit API services, repositories with Either-based error handling, and Riverpod providers.
---

# Flutter API Client Generator

## Overview

このスキルは、OpenAPI/Swagger仕様からFlutter用のAPIクライアントコードを自動生成します。型安全なモデル、APIサービス、リポジトリ、Riverpodプロバイダを含むフルスタックの実装を生成します。

**Use this skill when:**
- OpenAPI/Swagger仕様からFlutter APIクライアントを生成したい
- Retrofit + freezed + Riverpodを使った型安全なAPI層を構築したい
- Either型によるエラーハンドリングを実装したい
- 既存のバックエンドAPIに対するFlutterクライアントを作成したい

## Input Requirements

### 必須入力
- **OpenAPI仕様ファイル**: OpenAPI 3.x形式のYAMLまたはJSONファイル

### オプション設定
- **エラーハンドリング方式**: Either型（デフォルト・推奨）または例外ベース
- **出力ディレクトリ**: 生成コードの出力先（デフォルト: `lib/`）

## Technology Stack

| カテゴリ | ライブラリ | 用途 |
|---------|-----------|------|
| HTTP Client | dio | HTTP通信 |
| API定義 | retrofit | 型安全なAPI定義 |
| シリアライズ | json_serializable | JSON変換 |
| イミュータブルモデル | freezed | モデル・Failure定義 |
| 状態管理 | riverpod | 依存注入・状態管理 |
| コード生成 | riverpod_annotation | Provider自動生成 |
| 関数型 | dartz | Either型（エラーハンドリング） |

## Generated Code Structure

```
lib/
├── core/
│   ├── error/
│   │   ├── failures.dart              # エラー型定義
│   │   └── failures.freezed.dart      # 生成ファイル
│   └── network/
│       └── dio_client.dart            # Dioクライアント設定
├── data/
│   ├── api/
│   │   ├── {tag}_api_service.dart     # Retrofit APIサービス
│   │   └── {tag}_api_service.g.dart   # 生成ファイル
│   └── repositories/
│       └── {tag}_repository_impl.dart # リポジトリ実装
├── domain/
│   ├── models/
│   │   ├── {model}.dart               # Freezedモデル
│   │   ├── {model}.freezed.dart       # 生成ファイル
│   │   └── {model}.g.dart             # 生成ファイル
│   └── repositories/
│       └── {tag}_repository.dart      # リポジトリインターフェース
└── presentation/
    └── providers/
        ├── {tag}_providers.dart       # Riverpodプロバイダ
        └── {tag}_providers.g.dart     # 生成ファイル
```

## Dependencies (pubspec.yaml)

> **Note**: 以下のバージョンは参考値です。プロジェクトの要件に合わせて最新の安定版を使用してください。

```yaml
dependencies:
  dio: ^5.4.0
  retrofit: ^4.1.0
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1
  riverpod_annotation: ^2.3.3
  flutter_riverpod: ^2.4.9
  dartz: ^0.10.1

dev_dependencies:
  build_runner: ^2.4.8
  retrofit_generator: ^8.1.0
  freezed: ^2.4.6
  json_serializable: ^6.7.1
  riverpod_generator: ^2.3.9
```

## Workflow Steps

このスキルは以下のステップで実行されます：

### Step 1: OpenAPI解析
@import steps/01_analyze_openapi.md

OpenAPI仕様ファイルを解析し、生成対象のモデルとエンドポイントを特定します。

### Step 2: モデル生成
@import steps/02_generate_models.md

FreezedベースのDartモデルクラスを生成します。

### Step 3: APIサービス生成
@import steps/03_generate_api_service.md

Retrofitアノテーション付きのAPIサービスを生成します。

### Step 4: リポジトリ生成
@import steps/04_generate_repository.md

Either型エラーハンドリングを含むリポジトリを生成します。

### Step 5: プロバイダ生成
@import steps/05_generate_providers.md

Riverpodプロバイダを生成します。

### Step 6: 実装検証
@import steps/06_verify_implementation.md

生成コードをビルド・検証します。

## Reference Documents

### OpenAPI型マッピング
@import references/01_openapi_mapping.md

### コードテンプレート
@import references/02_code_templates.md

## Usage Example

### 1. OpenAPI仕様の準備

```yaml
# api_spec.yaml
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
paths:
  /users:
    get:
      tags: [users]
      operationId: getUsers
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
  /users/{id}:
    get:
      tags: [users]
      operationId: getUser
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      required: [id, name, email]
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
          format: email
        createdAt:
          type: string
          format: date-time
```

### 2. スキル実行

```
/api-client-generator api_spec.yaml
```

### 3. コード生成実行

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

## Error Handling Strategy

### Either型（推奨）

```dart
// 使用例
final result = await userRepository.getUser(userId);
result.fold(
  (failure) => showError(failure.message),
  (user) => showUser(user),
);
```

### 例外ベース（オプション）

```dart
// 使用例
try {
  final user = await userRepository.getUser(userId);
  showUser(user);
} on NetworkFailure catch (e) {
  showError(e.message);
}
```

## Complete Examples

`examples/`ディレクトリに完全な入出力例があります。few-shot promptingの参考として使用してください。

### 入力例
@import examples/sample_api.yaml

### 出力例
@import examples/output/

詳細は `examples/README.md` を参照してください。

## Notes

- 生成されるコードは`build_runner`による追加コード生成が必要です
- OpenAPI仕様の`operationId`がメソッド名として使用されます
- `tags`がAPIサービスのグルーピングに使用されます
- `$ref`による参照は自動的に解決されます
