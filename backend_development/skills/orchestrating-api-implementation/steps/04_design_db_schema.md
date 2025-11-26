# ステップ4: DBスキーマを設計する

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
| `relation` | `bigint` (FK) | `references` |
| `custom` | 展開してカラム化 | 複数カラム |

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

### 4.5 スキーマ設計書を作成する

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
