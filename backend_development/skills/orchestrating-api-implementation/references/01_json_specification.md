# モデル永続化仕様 (JSON Specification)

API Designerで作成されるモデルデータのJSON構造仕様です。
このデータ構造は、プロジェクトの保存・読み込み（インポート/エクスポート）に使用されます。

> [!TIP]
> **JSON Schema**: [model-persistence-schema.json](./model-persistence-schema.json)

## ルートオブジェクト (ApiProject)

プロジェクト全体を表すルートオブジェクトです。

| プロパティ名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `projectName` | string | Yes | プロジェクト名 |
| `version` | string | Yes | プロジェクトのバージョン (例: "1.0.0") |
| `models` | Model[] | Yes | 定義されたモデルのリスト |
| `customTypes` | CustomType[] | No | **[New]** カスタム型定義のリスト |
| `authConfig` | AuthConfig | No | **[New]** 認証・ユーザー管理設定 |
| `roles` | string[] | No | **[New]** グローバルロールのリスト |
| `actors` | Actor[] | No | **[New]** アクターのリスト |
| `useCases` | UseCase[] | No | **[New]** ユースケースのリスト |

```json
{
  "projectName": "My CMS",
  "version": "1.0.0",
  "models": [ ... ],
  "customTypes": [ ... ],
  "authConfig": { ... }
}
```

## モデル (Model)

1つのデータモデル（テーブル定義）を表します。

| プロパティ名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | string | Yes | モデルの一意なID (UUID) |
| `name` | string | Yes | モデル名（テーブル名） |
| `displayName` | string | No | **[New]** モデルの表示名 |
| `description` | string | No | モデルの説明 |
| `fields` | Field[] | Yes | フィールド定義のリスト |
| `accessControl` | AccessControl | No | アクセス制御設定 |
| `webhooks` | Webhook[] | No | Webhook設定 |

### アクセス制御 (AccessControl)

| プロパティ名 | 型 | 説明 |
| --- | --- | --- |
| `read` | string[] | 読み取り権限を持つロール (例: `['public', 'admin']`) |
| `write` | string[] | 書き込み権限を持つロール |
| `delete` | string[] | 削除権限を持つロール |
| `rowLevel` | RowLevelAccess | **[New]** 行レベルのアクセス制御ルール |

#### 行レベルアクセス制御 (RowLevelAccess)

特定の条件に一致するレコードのみアクセスを許可する設定です。

| プロパティ名 | 型 | 説明 |
| --- | --- | --- |
| `ownerField` | string | 作成者（所有者）を保持するフィールド名 (例: `createdBy`) |
| `rules` | AccessRule[] | 詳細な条件ルール |

```json
"rowLevel": {
  "ownerField": "author", // authorフィールドが現在のユーザーと一致する場合のみアクセス可
  "rules": [
    {
      "action": "read",
      "role": "member",
      "condition": { "status": "published" } // memberロールはstatusがpublishedのものだけ読める
    }
  ]
}
```

### Webhook

| プロパティ名 | 型 | 説明 |
| --- | --- | --- |
| `event` | string | イベントタイプ (`onCreate`, `onUpdate`, `onDelete`) |
| `url` | string | 通知先URL |

## フィールド (Field)

モデル内の各フィールド（カラム）定義です。

| プロパティ名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | string | Yes | フィールドの一意なID |
| `name` | string | Yes | フィールド名 |
| `displayName` | string | No | **[New]** フィールドの表示名 |
| `type` | FieldType | Yes | データ型 |
| `isPrimary` | boolean | No | プライマリキーかどうか |
| `isList` | boolean | No | 配列（リスト）かどうか |
| `isIndex` | boolean | No | インデックスを作成するかどうか |
| `validation` | FieldValidation | No | バリデーションルール |
| `options` | FieldOptions | No | その他のオプション |
| `relationTo` | string | No | リレーション先のモデル名 (`type`が`relation`の場合) |
| `customTypeName` | string | No | **[New]** カスタム型名 (`type`が`custom`の場合) |
| `enumValues` | string[] | No | Enumの選択肢 (`type`が`enum`の場合) |
| `apiOptions` | ApiOptions | No | **[New]** API公開オプション |
| `relationOptions` | RelationOptions | No | **[New]** リレーション設定オプション |

### データ型 (FieldType)

以下の文字列のいずれか:
- `string`: 文字列 (一行)
- `text`: **[New]** 文字列 (複数行)
- `richText`: **[New]** リッチテキスト (HTML)
- `number`: 数値 (浮動小数点数)
- `integer`: **[New]** 数値 (整数)
- `boolean`: 真偽値
- `date`: 日時
- `uuid`: UUID
- `image`: 画像
- `enum`: 列挙型
- `relation`: リレーション
- `custom`: **[New]** カスタム型
- `role`: **[New]** ロール型 (Global Rolesと連携)

### バリデーション (FieldValidation)

| プロパティ名 | 型 | 説明 |
| --- | --- | --- |
| `required` | boolean | 必須項目かどうか |
| `min` | number | 最小値（数値）または最小長（文字列） |
| `max` | number | 最大値（数値）または最大長（文字列） |
| `pattern` | string | 正規表現パターン |
| `unique` | boolean | ユニーク制約 |

### オプション (FieldOptions)

| プロパティ名 | 型 | 説明 |
| --- | --- | --- |
| `resize` | boolean | 画像のリサイズを行うか |
| `format` | string | 画像フォーマット (`webp`, `jpeg`, `png`) |
| `default` | any | デフォルト値 |

### APIオプション (ApiOptions) **[New]**

API経由でのアクセス制御に関するオプションです。

| プロパティ名 | 型 | 説明 |
| --- | --- | --- |
| `filterable` | boolean | フィルタリング可能にするか |
| `sortable` | boolean | ソート可能にするか |
| `searchable` | boolean | 検索対象にするか |

### リレーションオプション (RelationOptions) **[New]**

リレーションフィールドに対する追加設定です。

| プロパティ名 | 型 | 説明 |
| --- | --- | --- |
| `expandable` | boolean | APIレスポンスで展開(join)可能にするか |
| `defaultExpand` | boolean | デフォルトで展開するか |
| `onDelete` | string | 参照先削除時の挙動 (`cascade`, `nullify`, `restrict`) |

## カスタム型 (CustomType) **[New]**

再利用可能なフィールドの集合定義です（例: 住所、SEO設定など）。

| プロパティ名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `name` | string | Yes | カスタム型名 (例: "Address") |
| `fields` | Field[] | Yes | フィールド定義のリスト |

```json
{
  "name": "Address",
  "fields": [
    { "name": "zipCode", "type": "string" },
    { "name": "city", "type": "string" }
  ]
}
```

## ユーザー管理・認証 (AuthConfig) **[New]**

ユーザー管理機能と認証に関する設定です。
有効にすると、システム内部で `User` モデルが自動的に管理されます。

| プロパティ名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `enabled` | boolean | Yes | ユーザー管理機能を有効にするか |
| `userModelName` | string | No | ユーザー情報を格納するモデル名 (デフォルト: "User") |
| `authFields` | AuthFields | No | 認証に使用するフィールド設定 |

### ユーザーモデルとの連携

ユーザー管理を有効にすると、他のモデルからユーザーモデルへのリレーションを定義することで、
**「誰が作成したか」「誰が閲覧できるか」** といった行レベルのアクセス制御が可能になります。

例: `Post` モデルに `author` フィールド (Userへのリレーション) を追加し、
`AccessControl.rowLevel.ownerField` に `author` を指定する。

## アクター (Actor) **[New]**

システムを利用するユーザーや外部システムの役割を定義します。

| プロパティ名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | string | Yes | アクターの一意なID |
| `name` | string | Yes | アクター名 |
| `description` | string | No | アクターの説明 |

## ユースケース (UseCase) **[New]**

システムが提供する機能や振る舞いを定義します。自然言語による設計をサポートするため、構造化された各フィールドを持ちます。

| プロパティ名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | string | Yes | ユースケースの一意なID |
| `name` | string | Yes | ユースケース名 |
| `description` | string | No | ユースケースの説明 |
| `actorIds` | string[] | Yes | このユースケースを実行できるアクターのIDリスト |
| `preconditions` | string[] | No | 事前条件 |
| `postconditions` | string[] | No | 事後条件 |
| `modelInteractions` | ModelInteraction[] | No | モデルとのインタラクション |
| `notes` | string | No | 設計に関するメモ・特記事項 |

### モデルインタラクション (ModelInteraction)

ユースケース内でどのモデルに対してどのような操作を行うかを定義します。

| プロパティ名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `model` | string | Yes | 対象モデル名 |
| `description` | string | Yes | 操作の説明（自然言語） |
| `hint` | string | No | 操作の種類のヒント (`read`, `write`, `delete`, `search`, `aggregate`, `other`) |

## JSONサンプル (拡張版)

```json
{
  "projectName": "E-commerce API",
  "version": "1.1.0",
  "authConfig": {
    "enabled": true,
    "userModelName": "User"
  },
  "roles": ["public", "admin", "user"],
  "actors": [
    {
      "id": "actor-1",
      "name": "Customer",
      "description": "一般顧客"
    }
  ],
  "useCases": [
    {
      "id": "uc-1",
      "name": "Purchase Product",
      "description": "商品を購入する",
      "actorIds": ["actor-1"],
      "preconditions": ["User must be logged in", "Product must be in stock"],
      "postconditions": ["Order created", "Stock decreased", "Email sent"],
      "modelInteractions": [
        {
          "model": "Product",
          "description": "Check availability and price",
          "hint": "read"
        },
        {
          "model": "Order",
          "description": "Create new order record",
          "hint": "write"
        }
      ]
    }
  ],
  "customTypes": [
    {
      "name": "SEO",
      "fields": [
        { "id": "seo1", "name": "title", "type": "string" },
        { "id": "seo2", "name": "description", "type": "text" }
      ]
    }
  ],
  "models": [
    {
      "id": "uuid-1",
      "name": "Product",
      "description": "商品情報",
      "accessControl": {
        "read": ["public"],
        "write": ["admin"],
        "rowLevel": {
          "ownerField": "createdBy"
        }
      },
      "fields": [
        {
          "id": "f1",
          "name": "id",
          "type": "uuid",
          "isPrimary": true
        },
        {
          "id": "f2",
          "name": "description",
          "type": "richText",
          "apiOptions": {
              "searchable": true
          }
        },
        {
          "id": "f3",
          "name": "stock",
          "type": "integer",
          "validation": { "min": 0 },
          "apiOptions": {
              "sortable": true,
              "filterable": true
          }
        },
        {
          "id": "f4",
          "name": "seoSettings",
          "type": "custom",
          "customTypeName": "SEO"
        },
        {
          "id": "f5",
          "name": "createdBy",
          "type": "relation",
          "relationTo": "User",
          "relationOptions": {
              "onDelete": "restrict"
          }
        }
      ]
    }
  ]
}
```
