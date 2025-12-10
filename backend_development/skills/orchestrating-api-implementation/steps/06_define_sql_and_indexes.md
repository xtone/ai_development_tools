# ステップ6: SQLとインデックスを定義する

## 目次

- [目的](#目的)
- [手順](#手順)
  - [6.1 基本CRUDのSQLを確認する](#61-基本crudのsqlを確認する)
  - [6.2 apiOptionsからインデックスを自動導出する](#62-apioptionsからインデックスを自動導出する)
  - [6.3 インデックスの設計方針](#63-インデックスの設計方針)
  - [6.4 通常インデックスの定義](#64-通常インデックスの定義)
  - [6.5 全文検索インデックスの定義](#65-全文検索インデックスの定義)
  - [6.6 インデックス一覧を作成する](#66-インデックス一覧を作成する)
  - [6.7 パフォーマンス考慮事項](#67-パフォーマンス考慮事項)
- [出力](#出力)

---

## 目的

ユースケースで実行されるSQLを洗い出し、`apiOptions`から必要なインデックスを自動導出して定義する。

## 手順

### 6.1 基本CRUDのSQLを確認する

Active Recordが生成するSQLを把握する。

#### 一覧取得

```sql
-- 基本
SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET 0;

-- フィルタリング
SELECT * FROM posts WHERE status = 'published' ORDER BY created_at DESC;

-- 関連データ取得（N+1回避）
SELECT * FROM posts WHERE id IN (...);
SELECT * FROM users WHERE id IN (...);
```

#### 単体取得

```sql
SELECT * FROM posts WHERE id = $1 LIMIT 1;
```

#### 作成

```sql
INSERT INTO posts (title, content, status, author_id, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6) RETURNING *;
```

#### 更新

```sql
UPDATE posts SET title = $1, updated_at = $2 WHERE id = $3 RETURNING *;
```

#### 削除

```sql
DELETE FROM posts WHERE id = $1;
```

### 6.2 apiOptionsからインデックスを自動導出する

JSON仕様の`apiOptions`に基づいて、必要なインデックスを自動的に導出する。

#### 導出ルール

| apiOptions設定 | 導出されるインデックス | 理由 |
|---------------|---------------------|------|
| `filterable: true` | 単一カラムインデックス | WHERE句での高速検索 |
| `sortable: true` | 単一カラムインデックス | ORDER BY での高速ソート |
| `searchable: true` | GINインデックス（全文検索） | 全文検索の高速化 |

#### フィルタ用インデックスの導出

`apiOptions.filterable: true` のフィールドに対してインデックスを作成：

```markdown
## フィルタ用インデックス（apiOptions.filterable: true から自動導出）

| テーブル | カラム | インデックス種類 | 導出元 |
|---------|--------|-----------------|--------|
| posts | status | BTREE | apiOptions.filterable: true |
| posts | category_id | BTREE | apiOptions.filterable: true (relation) |
| posts | created_at | BTREE | apiOptions.filterable: true (date range) |
| products | price | BTREE | apiOptions.filterable: true (range) |
```

```ruby
# マイグレーション
add_index :posts, :status         # filterable: true から導出
add_index :posts, :category_id    # filterable: true (relation) から導出
add_index :posts, :created_at     # filterable: true (date) から導出
add_index :products, :price       # filterable: true (range) から導出
```

#### ソート用インデックスの導出

`apiOptions.sortable: true` のフィールドに対してインデックスを作成：

```markdown
## ソート用インデックス（apiOptions.sortable: true から自動導出）

| テーブル | カラム | インデックス種類 | 導出元 |
|---------|--------|-----------------|--------|
| posts | created_at | BTREE | apiOptions.sortable: true |
| posts | updated_at | BTREE | apiOptions.sortable: true |
| posts | title | BTREE | apiOptions.sortable: true |
| products | price | BTREE | apiOptions.sortable: true |
```

**注意**: `filterable`と`sortable`の両方が`true`の場合、インデックスは1つで十分。

#### 全文検索インデックスの導出

`apiOptions.searchable: true` のフィールドに対してGINインデックスを作成：

```markdown
## 全文検索インデックス（apiOptions.searchable: true から自動導出）

| テーブル | 対象カラム | インデックス種類 | 導出元 |
|---------|-----------|-----------------|--------|
| posts | title, content | GIN (tsvector) | apiOptions.searchable: true |
| products | name, description | GIN (tsvector) | apiOptions.searchable: true |
```

### 6.3 インデックスの設計方針

#### 必須インデックス

| 対象 | 理由 |
|------|------|
| プライマリキー | 自動作成 |
| 外部キー | JOINの高速化 |
| `isIndex: true` のフィールド | 仕様で指定 |
| `unique: true` のフィールド | ユニーク制約 |
| `apiOptions.filterable: true` | **自動導出** |
| `apiOptions.sortable: true` | **自動導出** |
| `apiOptions.searchable: true` | **自動導出** |

#### 推奨インデックス

| 対象 | 理由 |
|------|------|
| 複合条件 | 複合インデックス検討 |

### 6.4 通常インデックスの定義

```ruby
# 単一カラムインデックス（apiOptionsから自動導出）
add_index :posts, :status      # filterable: true
add_index :posts, :created_at  # filterable: true, sortable: true

# 外部キーインデックス
add_index :posts, :author_id

# ユニークインデックス（validation.unique: true から導出）
add_index :users, :email, unique: true

# 複合インデックス（複数のfilterableフィールドの組み合わせ）
add_index :posts, [:status, :created_at]

# 部分インデックス（PostgreSQL）
add_index :posts, :created_at, where: "status = 'published'", name: 'index_posts_published_on_created_at'
```

### 6.5 全文検索インデックスの定義（PostgreSQL）

`apiOptions.searchable: true` のフィールドに対して全文検索インデックスを作成する。

#### tsvectorカラムの追加

```ruby
# マイグレーション
add_column :posts, :searchable, :tsvector

# GINインデックスの作成
add_index :posts, :searchable, using: :gin
```

#### searchableフィールドからトリガーを生成

JSON仕様の`apiOptions.searchable: true`のフィールドを対象にトリガーを作成：

```ruby
# マイグレーション内でSQL実行
# searchable: true のフィールド: title, content

execute <<-SQL
  CREATE OR REPLACE FUNCTION posts_searchable_trigger() RETURNS trigger AS $$
  BEGIN
    NEW.searchable :=
      setweight(to_tsvector('japanese', coalesce(NEW.title, '')), 'A') ||
      setweight(to_tsvector('japanese', coalesce(NEW.content, '')), 'B');
    RETURN NEW;
  END
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER posts_searchable_update
    BEFORE INSERT OR UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION posts_searchable_trigger();
SQL
```

#### 全文検索クエリ

```sql
-- 基本検索
SELECT * FROM posts
WHERE searchable @@ plainto_tsquery('japanese', '検索キーワード');

-- ランキング付き
SELECT *, ts_rank(searchable, query) AS rank
FROM posts, plainto_tsquery('japanese', '検索キーワード') query
WHERE searchable @@ query
ORDER BY rank DESC;
```

#### Railsモデルでのスコープ

```ruby
class Post < ApplicationRecord
  scope :search, ->(query) {
    return all if query.blank?

    # プレースホルダーとsanitize_sql_arrayを使用した安全な実装
    where("searchable @@ plainto_tsquery('japanese', ?)", query)
      .order(
        Arel.sql(
          sanitize_sql_array([
            "ts_rank(searchable, plainto_tsquery('japanese', ?)) DESC",
            query
          ])
        )
      )
  }
end
```

**セキュリティ注意事項:**
- WHERE句ではプレースホルダー（`?`）を使用
- ORDER BY句では`sanitize_sql_array`でパラメータをサニタイズ
- `plainto_tsquery`自体も入力をサニタイズするため二重の保護

### 6.6 インデックス一覧を作成する

```markdown
## テーブル: posts

### インデックス一覧

| インデックス名 | カラム | 種類 | 用途 | 導出元 |
|--------------|--------|------|------|--------|
| posts_pkey | id | PRIMARY | PK | - |
| index_posts_on_author_id | author_id | BTREE | FK | relation |
| index_posts_on_status | status | BTREE | フィルタ | apiOptions.filterable: true |
| index_posts_on_category_id | category_id | BTREE | フィルタ | apiOptions.filterable: true |
| index_posts_on_created_at | created_at | BTREE | フィルタ/ソート | apiOptions.filterable: true, sortable: true |
| index_posts_on_updated_at | updated_at | BTREE | ソート | apiOptions.sortable: true |
| index_posts_on_title | title | BTREE | ソート | apiOptions.sortable: true |
| index_posts_on_searchable | searchable | GIN | 全文検索 | apiOptions.searchable: true (title, content) |
```

### 6.7 パフォーマンス考慮事項

- インデックスは更新性能に影響するため、必要最小限に
- `filterable`と`sortable`の両方が`true`の場合、インデックスは共有可能
- 複合インデックスのカラム順序は選択性の高い順
- 全文検索インデックスは更新コストが高いため、検索頻度と更新頻度のバランスを考慮
- PostgreSQLのEXPLAIN ANALYZEで実行計画を確認

## 出力

全テーブルのインデックス定義をまとめ、マイグレーション実装時に使用する。

### 出力形式

```markdown
## インデックス設計書

### apiOptionsから自動導出されたインデックス

#### フィルタ用（filterable: true）
| テーブル | カラム | 型 |
|---------|--------|-----|
| posts | status | enum |
| posts | category_id | relation |
| posts | created_at | date |
| products | price | integer |

#### ソート用（sortable: true）
| テーブル | カラム | 型 |
|---------|--------|-----|
| posts | created_at | date |
| posts | title | string |
| products | price | integer |

#### 全文検索用（searchable: true）
| テーブル | 対象カラム | 型 |
|---------|-----------|-----|
| posts | title | string |
| posts | content | richText |
| products | name | string |
| products | description | text |

### マイグレーション例

```ruby
class AddIndexesToPosts < ActiveRecord::Migration[8.0]
  def change
    # フィルタ用インデックス（apiOptions.filterable: true から導出）
    add_index :posts, :status
    add_index :posts, :category_id

    # フィルタ/ソート兼用インデックス
    add_index :posts, :created_at

    # ソート用インデックス（apiOptions.sortable: true から導出）
    add_index :posts, :updated_at
    add_index :posts, :title

    # 全文検索用（apiOptions.searchable: true から導出）
    add_column :posts, :searchable, :tsvector
    add_index :posts, :searchable, using: :gin

    # 全文検索トリガー
    execute <<-SQL
      CREATE OR REPLACE FUNCTION posts_searchable_trigger() RETURNS trigger AS $$
      BEGIN
        NEW.searchable :=
          setweight(to_tsvector('japanese', coalesce(NEW.title, '')), 'A') ||
          setweight(to_tsvector('japanese', coalesce(NEW.content, '')), 'B');
        RETURN NEW;
      END
      $$ LANGUAGE plpgsql;

      CREATE TRIGGER posts_searchable_update
        BEFORE INSERT OR UPDATE ON posts
        FOR EACH ROW EXECUTE FUNCTION posts_searchable_trigger();
    SQL
  end
end
```
```
