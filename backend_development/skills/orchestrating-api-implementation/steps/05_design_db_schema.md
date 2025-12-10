# ステップ5: DBスキーマを設計する

## 目次

- [目的](#目的)
- [手順](#手順)
  - [5.1 フィールド型のマッピング](#51-フィールド型のマッピング)
  - [5.2 テーブル設計のルール](#52-テーブル設計のルール)
  - [5.3 リレーションの設計](#53-リレーションの設計)
  - [5.4 relationOptionsに基づく外部キー制約](#54-relationoptionsに基づく外部キー制約)
  - [5.5 カスタム型の展開](#55-カスタム型の展開)
  - [5.6 Enumの定義](#56-enumの定義)
  - [5.7 Role型（配列）の定義](#57-role型配列の定義)
  - [5.8 スキーマ設計書を作成する](#58-スキーマ設計書を作成する)
- [出力](#出力)

---

## 目的

JSON仕様をPostgreSQLのテーブル定義に変換する。
`relationOptions.onDelete`に基づいて外部キー制約を適切に設定する。

## 手順

### 5.1 フィールド型のマッピング

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

### 5.2 テーブル設計のルール

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

### 5.3 リレーションの設計

#### 基本的な外部キー

リレーション型のフィールドには外部キー制約を設定：

```ruby
t.references :author, foreign_key: { to_table: :users }
```

### 5.4 relationOptionsに基づく外部キー制約

JSON仕様の`relationOptions.onDelete`に基づいて、外部キー制約の削除時動作を設定する。

#### onDeleteの値とRails/PostgreSQLマッピング

| onDelete値 | PostgreSQL制約 | Railsマイグレーション | 動作 |
|-----------|---------------|---------------------|------|
| `cascade` | `ON DELETE CASCADE` | `on_delete: :cascade` | 親削除時に子も削除 |
| `nullify` | `ON DELETE SET NULL` | `on_delete: :nullify` | 親削除時にNULL設定 |
| `restrict` | `ON DELETE RESTRICT` | `on_delete: :restrict` | 子がある場合は削除禁止（デフォルト） |

#### マイグレーション例

```ruby
# JSON仕様
# {
#   "name": "author",
#   "type": "relation",
#   "relationTo": "User",
#   "relationOptions": {
#     "onDelete": "nullify"
#   }
# }

# マイグレーション
create_table :posts, id: :uuid do |t|
  # onDelete: nullify の場合
  t.references :author,
    type: :uuid,
    foreign_key: { to_table: :users, on_delete: :nullify },
    null: true  # nullifyの場合はNULL許可が必要

  # onDelete: cascade の場合
  t.references :category,
    type: :uuid,
    foreign_key: { to_table: :categories, on_delete: :cascade },
    null: false

  # onDelete: restrict の場合（デフォルト）
  t.references :department,
    type: :uuid,
    foreign_key: { to_table: :departments, on_delete: :restrict },
    null: false

  t.timestamps
end
```

#### 既存テーブルへの外部キー追加

```ruby
# 外部キーの追加（on_delete指定あり）
add_foreign_key :posts, :users, column: :author_id, on_delete: :nullify
add_foreign_key :posts, :categories, column: :category_id, on_delete: :cascade

# 外部キーの変更（既存の制約を置き換え）
remove_foreign_key :posts, :users
add_foreign_key :posts, :users, column: :author_id, on_delete: :nullify
```

#### onDelete設定の注意事項

| 設定 | 注意点 |
|------|--------|
| `cascade` | 意図しないデータ削除に注意。子テーブルのデータも完全に削除される |
| `nullify` | カラムに`null: true`が必要。必須フィールドには使用不可 |
| `restrict` | 参照しているレコードがある場合、親レコードは削除できない |

### 5.5 カスタム型の展開

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

### 5.6 Enumの定義

Rails 8のenumを使用：

```ruby
# モデル内で定義
enum :status, { draft: 'draft', published: 'published', archived: 'archived' }
```

### 5.7 Role型（配列）の定義

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
# 特定のロールを持つユーザーを検索（固定値の場合）
Account.where("'admin' = ANY(roles)")

# ❌ 危険 - SQLインジェクションのリスク
# role = params[:role]
# Account.where("'#{role}' = ANY(roles)")  # 絶対にこうしないこと!

# ❌ 危険 - 複数の値を検索する場合も同様
# roles = params[:roles] # ["admin", "editor"]
# Account.where("roles && ARRAY[#{roles.map { |r| "'#{r}'" }.join(',')}]")  # 危険!

# ✅ 安全 - プレースホルダーを使用（単一値）
role = params[:role]
Account.where("? = ANY(roles)", role)

# ✅ 安全 - PostgreSQL配列演算子を使用（包含チェック）
role = params[:role]
Account.where("roles @> ARRAY[?]::varchar[]", role)

# ✅ 安全 - 複数ロールの検索（共通要素チェック）
roles = params[:roles]  # ['admin', 'editor']
Account.where("roles && ARRAY[?]::varchar[]", roles)

# Ransackでの検索設定
ransacker :roles do
  Arel.sql("array_to_string(roles, ',')")
end
```

**セキュリティ注意事項:**
- 動的な値をSQL文字列に直接埋め込まないこと
- 必ずプレースホルダー（`?`）を使用してパラメータを渡すこと
- PostgreSQLの配列演算子（`@>`は包含、`&&`は共通要素チェック）を活用

**セキュリティチェックリスト:**
- [ ] 動的な値を直接SQL文字列に埋め込んでいないか
- [ ] プレースホルダー（`?`）を使用しているか
- [ ] 配列操作時も適切にエスケープされているか

### 5.8 スキーマ設計書を作成する

以下の形式でまとめる：

```markdown
## テーブル: posts

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | uuid | NO | gen_random_uuid() | PK |
| title | varchar(255) | NO | - | タイトル |
| content | text | YES | - | 本文 |
| status | varchar(50) | NO | 'draft' | ステータス |
| author_id | uuid | YES | - | FK: users |
| category_id | uuid | NO | - | FK: categories |
| created_at | timestamp | NO | - | 作成日時 |
| updated_at | timestamp | NO | - | 更新日時 |

### 外部キー（relationOptionsから自動導出）

| カラム | 参照先 | 削除時動作 | 由来 |
|--------|--------|-----------|------|
| author_id | users(id) | SET NULL | relationOptions.onDelete: "nullify" |
| category_id | categories(id) | CASCADE | relationOptions.onDelete: "cascade" |

### Enum定義

- status: draft, published, archived
```

## 出力

全テーブルのスキーマ設計書を作成し、マイグレーション実装時に使用する。

### 出力形式

```markdown
## スキーマ設計書

### 1. postsテーブル

[テーブル定義]

#### 外部キー制約（relationOptionsから導出）

| フィールド | 参照先 | onDelete | Railsオプション |
|-----------|--------|----------|----------------|
| author_id | users | nullify | `on_delete: :nullify, null: true` |
| category_id | categories | cascade | `on_delete: :cascade` |

#### マイグレーション例

```ruby
create_table :posts, id: :uuid do |t|
  t.string :title, null: false
  t.text :content
  t.string :status, null: false, default: 'draft'
  t.references :author, type: :uuid, foreign_key: { to_table: :users, on_delete: :nullify }, null: true
  t.references :category, type: :uuid, foreign_key: { to_table: :categories, on_delete: :cascade }, null: false
  t.timestamps
end
```

### 2. usersテーブル

[テーブル定義]

...
```
