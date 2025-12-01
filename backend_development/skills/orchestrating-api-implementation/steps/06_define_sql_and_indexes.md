# ステップ6: SQLとインデックスを定義する

## サブエージェント実行情報

| 項目 | 値 |
|------|-----|
| **入力ファイル** | `.artifacts/03_usecases.json`, `.artifacts/05_db_schema.json` |
| **出力ファイル** | `.artifacts/06_indexes.json` |
| **依存ステップ** | ステップ3, ステップ5 |

### 出力ファイル形式

```json
{
  "version": "1.0",
  "generatedAt": "2025-01-01T00:00:00Z",
  "step": "06_indexes",
  "data": {
    "indexes": [
      {
        "table": "posts",
        "name": "index_posts_on_status",
        "columns": ["status"],
        "type": "btree",
        "unique": false
      },
      {
        "table": "posts",
        "name": "index_posts_on_author_id",
        "columns": ["author_id"],
        "type": "btree",
        "unique": false,
        "foreignKey": true
      },
      {
        "table": "posts",
        "name": "index_posts_on_status_and_created_at",
        "columns": ["status", "created_at"],
        "type": "btree",
        "unique": false,
        "composite": true
      },
      {
        "table": "posts",
        "name": "index_posts_on_searchable",
        "columns": ["searchable"],
        "type": "gin",
        "unique": false
      }
    ],
    "fullTextSearch": [
      {
        "table": "posts",
        "column": "searchable",
        "type": "tsvector",
        "sources": [
          { "column": "title", "weight": "A" },
          { "column": "content", "weight": "B" }
        ],
        "language": "japanese",
        "trigger": "posts_searchable_trigger"
      }
    ],
    "uniqueConstraints": [
      {
        "table": "users",
        "name": "index_users_on_email",
        "columns": ["email"]
      }
    ]
  }
}
```

### 完了報告に含める情報

- 通常インデックス数
- 全文検索インデックス数
- ユニーク制約数
- 出力ファイルパス

---

## 目次

- [目的](#目的)
- [手順](#手順)
  - [5.1 基本CRUDのSQLを確認する](#51-基本crudのsqlを確認する)
  - [5.2 インデックスを設計する](#52-インデックスを設計する)
  - [5.3 全文検索インデックスを設計する](#53-全文検索インデックスを設計する)
  - [5.4 インデックス一覧を作成する](#54-インデックス一覧を作成する)
- [出力](#出力)

---

## 目的

ユースケースで実行されるSQLを洗い出し、必要なインデックスを定義する。

## 手順

### 5.1 基本CRUDのSQLを確認する

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

### 5.2 インデックスの設計方針

#### 必須インデックス

| 対象 | 理由 |
|------|------|
| プライマリキー | 自動作成 |
| 外部キー | JOINの高速化 |
| `isIndex: true` のフィールド | 仕様で指定 |
| `unique: true` のフィールド | ユニーク制約 |

#### 推奨インデックス

| 対象 | 理由 |
|------|------|
| フィルタリング対象カラム | WHERE句の高速化 |
| ソート対象カラム | ORDER BY の高速化 |
| 複合条件 | 複合インデックス検討 |
| テキスト検索対象 | 全文検索インデックス |

### 5.3 通常インデックスの定義

```ruby
# 単一カラムインデックス
add_index :posts, :status
add_index :posts, :created_at

# 外部キーインデックス
add_index :posts, :author_id

# ユニークインデックス
add_index :users, :email, unique: true

# 複合インデックス
add_index :posts, [:status, :created_at]

# 部分インデックス（PostgreSQL）
add_index :posts, :created_at, where: "status = 'published'", name: 'index_posts_published_on_created_at'
```

### 5.4 全文検索インデックスの定義（PostgreSQL）

テキスト型（`text`, `richText`, `string`）のフィールドに対して全文検索を有効にする。

#### tsvectorカラムの追加

```ruby
# マイグレーション
add_column :posts, :searchable, :tsvector

# GINインデックスの作成
add_index :posts, :searchable, using: :gin
```

#### トリガーで自動更新

```ruby
# マイグレーション内でSQL実行
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
    where("searchable @@ plainto_tsquery('japanese', ?)", query)
      .order(Arel.sql("ts_rank(searchable, plainto_tsquery('japanese', '#{sanitize_sql_like(query)}')) DESC"))
  }
end
```

### 5.5 pg_bigmによる日本語検索（代替案）

日本語の部分一致検索が必要な場合は `pg_bigm` 拡張を検討：

```sql
-- 拡張のインストール
CREATE EXTENSION IF NOT EXISTS pg_bigm;

-- GINインデックス（bigm）
CREATE INDEX idx_posts_title_bigm ON posts USING gin (title gin_bigm_ops);
CREATE INDEX idx_posts_content_bigm ON posts USING gin (content gin_bigm_ops);
```

```ruby
# Railsでの検索
Post.where("title LIKE ?", "%#{query}%")  # pg_bigmで高速化
```

### 5.6 インデックス一覧を作成する

```markdown
## テーブル: posts

| インデックス名 | カラム | 種類 | 用途 |
|--------------|--------|------|------|
| posts_pkey | id | PRIMARY | PK |
| index_posts_on_author_id | author_id | BTREE | FK |
| index_posts_on_status | status | BTREE | フィルタ |
| index_posts_on_created_at | created_at | BTREE | ソート |
| index_posts_on_searchable | searchable | GIN | 全文検索 |
```

### 5.7 パフォーマンス考慮事項

- インデックスは更新性能に影響するため、必要最小限に
- 複合インデックスのカラム順序は選択性の高い順
- 全文検索インデックスは更新コストが高いため、検索頻度と更新頻度のバランスを考慮
- PostgreSQLのEXPLAIN ANALYZEで実行計画を確認

## 出力

全テーブルのインデックス定義（全文検索含む）をまとめ、マイグレーション実装時に使用する。
