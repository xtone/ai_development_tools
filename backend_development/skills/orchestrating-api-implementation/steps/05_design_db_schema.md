# ステップ5: DBスキーマを設計する

## サブエージェント実行情報

| 項目 | 値 |
|------|-----|
| **入力ファイル** | `.artifacts/01_specification.json` |
| **出力ファイル** | `.artifacts/05_db_schema.json` |
| **依存ステップ** | ステップ1 |

### 出力ファイル形式

```json
{
  "version": "1.0",
  "generatedAt": "2025-01-01T00:00:00Z",
  "step": "05_db_schema",
  "data": {
    "tables": [
      {
        "name": "posts",
        "primaryKey": {
          "name": "id",
          "type": "uuid",
          "default": "gen_random_uuid()"
        },
        "columns": [
          {
            "name": "title",
            "type": "string",
            "limit": 255,
            "null": false
          },
          {
            "name": "content",
            "type": "text",
            "null": true
          },
          {
            "name": "status",
            "type": "string",
            "limit": 50,
            "null": false,
            "default": "draft",
            "enum": ["draft", "published", "archived"]
          },
          {
            "name": "author_id",
            "type": "uuid",
            "null": false,
            "foreignKey": {
              "table": "users",
              "column": "id"
            }
          }
        ],
        "timestamps": true,
        "customTypeColumns": [
          {
            "prefix": "seo_settings",
            "fields": ["title", "description"]
          }
        ]
      }
    ],
    "enums": [
      {
        "name": "post_status",
        "values": ["draft", "published", "archived"]
      }
    ]
  }
}
```

### 完了報告に含める情報

- テーブル数
- カラム総数
- 外部キー数
- 出力ファイルパス

---

## 目次

- [目的](#目的)
- [手順](#手順)
  - [4.1 フィールド型のマッピング](#41-フィールド型のマッピング)
  - [4.2 テーブル設計のルール](#42-テーブル設計のルール)
  - [4.3 リレーションの設計](#43-リレーションの設計)
  - [4.4 role型（配列カラム）の設計](#44-role型配列カラムの設計)
  - [4.5 カスタム型の展開](#45-カスタム型の展開)
  - [4.6 論理削除の検討](#46-論理削除の検討)
- [出力](#出力)

---

## 目的

JSON仕様をPostgreSQLのテーブル定義に変換する。

## 手順

### 4.1 フィールド型のマッピング

JSON仕様の`type`をPostgreSQLの型にマッピング：

| JSON仕様の型 | PostgreSQL型 | Railsマイグレーション |
|-------------|--------------|---------------------|
| `string` | `varchar(255)` | `string` |
| `text` | `text` | `text` |
| `richText` | `text` | `text` |
| `number` | `decimal` | `decimal` |
| `integer` | `integer` / `bigint` | `integer` / `bigint` |
| `boolean` | `boolean` | `boolean` |
| `date` | `timestamp` | `datetime` |
| `uuid` | `uuid` | `uuid` |
| `image` | `varchar(255)` | `string` (URLを格納) |
| `enum` | `varchar(50)` | `string` + enum定義 |
| `relation` | `bigint` / `uuid` (FK) | `references` |
| `custom` | 展開してカラム化 | 複数カラム |
| `role` | `varchar[]` (配列) | `string, array: true` |

### 4.2 テーブル設計のルール

#### プライマリキー

```ruby
# UUID を使用する場合
create_table :posts, id: :uuid do |t|
  # ...
end

# BIGINT を使用する場合（デフォルト）
create_table :posts do |t|
  # ...
end
```

#### タイムスタンプ

全テーブルに `created_at`, `updated_at` を追加：

```ruby
t.timestamps
```

#### 外部キー

リレーション型のフィールドには外部キー制約を設定：

```ruby
t.references :author, foreign_key: { to_table: :users }
```

### 4.3 カスタム型の展開

カスタム型はプレフィックス付きのカラムとして展開：

```json
{
  "name": "seoSettings",
  "type": "custom",
  "customTypeName": "SEO"
}
```

↓

```ruby
t.string :seo_settings_title
t.text :seo_settings_description
```

### 4.4 Enumの定義

Rails 8のenumを使用：

```ruby
# モデル内で定義
enum :status, { draft: 'draft', published: 'published', archived: 'archived' }
```

### 4.5 Role型（配列）の定義

`isList: true` の `role` 型はPostgreSQLの配列カラムとして定義：

```ruby
# マイグレーション
t.string :roles, array: true, default: []

# インデックス（GINインデックスで高速検索）
add_index :accounts, :roles, using: :gin
```

モデルでの使用：

```ruby
# app/models/account.rb
class Account < ApplicationRecord
  # 配列カラムはそのまま使用可能
  # account.roles = ['admin', 'user']
  # account.roles << 'editor'

  # ロールのバリデーション
  VALID_ROLES = %w[public admin user editor].freeze

  validate :validate_roles

  def has_role?(role)
    roles.include?(role.to_s)
  end

  def admin?
    has_role?('admin')
  end

  private

  def validate_roles
    return if roles.blank?

    invalid_roles = roles - VALID_ROLES
    if invalid_roles.any?
      errors.add(:roles, "に無効な値が含まれています: #{invalid_roles.join(', ')}")
    end
  end
end
```

クエリ例：

```ruby
# 特定のロールを持つユーザーを検索
Account.where("'admin' = ANY(roles)")

# Ransackでの検索設定
ransacker :roles do
  Arel.sql("array_to_string(roles, ',')")
end
```

### 4.6 スキーマ設計書を作成する

以下の形式でまとめる：

```markdown
## テーブル: posts

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | uuid | NO | gen_random_uuid() | PK |
| title | varchar(255) | NO | - | タイトル |
| content | text | YES | - | 本文 |
| status | varchar(50) | NO | 'draft' | ステータス |
| author_id | uuid | NO | - | FK: users |
| created_at | timestamp | NO | - | 作成日時 |
| updated_at | timestamp | NO | - | 更新日時 |

### 外部キー
- author_id → users(id)

### Enum定義
- status: draft, published, archived
```

## 出力

全テーブルのスキーマ設計書を作成し、マイグレーション実装時に使用する。
