# ステップ8: DBマイグレーションを実装する

## 目次

- [目的](#目的)
- [手順](#手順)
  - [7.1 マイグレーションファイルを生成する](#71-マイグレーションファイルを生成する)
  - [7.2 マイグレーションを実装する](#72-マイグレーションを実装する)
  - [7.3 全文検索用マイグレーションを実装する](#73-全文検索用マイグレーションを実装する)
  - [7.4 カスタム型のカラムを実装する](#74-カスタム型のカラムを実装する)
  - [7.5 Enumカラムのチェック制約を追加](#75-enumカラムのチェック制約を追加オプション)
  - [7.6 マイグレーションを実行する](#76-マイグレーションを実行する)
  - [7.7 マイグレーションの命名規則](#77-マイグレーションの命名規則)
  - [7.8 ロールバック対応](#78-ロールバック対応)
- [トラブルシューティング](#トラブルシューティング)
- [出力](#出力)

---

## 目的

ステップ5, 6で設計したスキーマとインデックスをRailsマイグレーションとして実装する。

## 手順

### 7.1 マイグレーションファイルを生成する

各モデルごとにマイグレーションを生成：

```bash
rails generate migration CreatePosts
```

### 7.2 マイグレーションを実装する

`db/migrate/YYYYMMDDHHMMSS_create_posts.rb`:

```ruby
class CreatePosts < ActiveRecord::Migration[8.1]
  def change
    # UUID拡張を有効化（必要な場合）
    enable_extension 'pgcrypto' unless extension_enabled?('pgcrypto')

    create_table :posts, id: :uuid do |t|
      t.string :title, null: false
      t.text :content
      t.string :status, null: false, default: 'draft'
      t.references :author, type: :uuid, foreign_key: { to_table: :users }, null: false

      t.timestamps
    end

    # 通常インデックス
    add_index :posts, :status
    add_index :posts, :created_at
    add_index :posts, [:status, :created_at]
  end
end
```

### 7.3 全文検索用マイグレーションを実装する

テキスト検索が必要なテーブルに対して：

```ruby
class AddSearchableToPosts < ActiveRecord::Migration[8.1]
  def up
    # tsvectorカラムを追加
    add_column :posts, :searchable, :tsvector

    # GINインデックスを作成
    add_index :posts, :searchable, using: :gin

    # トリガー関数を作成
    execute <<-SQL
      CREATE OR REPLACE FUNCTION posts_searchable_trigger() RETURNS trigger AS $$
      BEGIN
        NEW.searchable :=
          setweight(to_tsvector('japanese', coalesce(NEW.title, '')), 'A') ||
          setweight(to_tsvector('japanese', coalesce(NEW.content, '')), 'B');
        RETURN NEW;
      END
      $$ LANGUAGE plpgsql;
    SQL

    # トリガーを作成
    execute <<-SQL
      CREATE TRIGGER posts_searchable_update
        BEFORE INSERT OR UPDATE ON posts
        FOR EACH ROW EXECUTE FUNCTION posts_searchable_trigger();
    SQL

    # 既存データを更新
    execute <<-SQL
      UPDATE posts SET searchable =
        setweight(to_tsvector('japanese', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('japanese', coalesce(content, '')), 'B');
    SQL
  end

  def down
    execute "DROP TRIGGER IF EXISTS posts_searchable_update ON posts"
    execute "DROP FUNCTION IF EXISTS posts_searchable_trigger()"
    remove_column :posts, :searchable
  end
end
```

### 7.4 カスタム型のカラムを実装する

カスタム型は展開してカラム化：

```ruby
class AddSeoSettingsToPosts < ActiveRecord::Migration[8.1]
  def change
    add_column :posts, :seo_settings_title, :string
    add_column :posts, :seo_settings_description, :text
  end
end
```

### 7.5 Enumカラムのチェック制約を追加（オプション）

データベースレベルでのEnum値の制約：

```ruby
class AddStatusCheckConstraintToPosts < ActiveRecord::Migration[8.1]
  def up
    execute <<-SQL
      ALTER TABLE posts
      ADD CONSTRAINT posts_status_check
      CHECK (status IN ('draft', 'published', 'archived'));
    SQL
  end

  def down
    execute <<-SQL
      ALTER TABLE posts DROP CONSTRAINT posts_status_check;
    SQL
  end
end
```

### 7.6 マイグレーションを実行する

```bash
# マイグレーションを実行
rails db:migrate

# ステータス確認
rails db:migrate:status

# スキーマ確認
rails db:schema:dump
```

### 7.7 マイグレーションの命名規則

| 操作 | 命名パターン |
|------|-------------|
| テーブル作成 | `CreateTableName` |
| カラム追加 | `AddColumnNameToTableName` |
| カラム削除 | `RemoveColumnNameFromTableName` |
| インデックス追加 | `AddIndexToTableName` |
| 参照追加 | `AddReferenceToTableName` |

### 7.8 ロールバック対応

`change` メソッドで自動的にロールバック可能な操作を使用。
複雑な操作は `up` / `down` メソッドを分けて実装。

```ruby
def up
  # 適用時の処理
end

def down
  # ロールバック時の処理
end
```

## トラブルシューティング

### 8.1 テーブル/インデックスが既に存在するエラー

**エラー**: `PG::DuplicateTable: ERROR: relation "xxx" already exists`

マイグレーションが途中で失敗した後、再実行した場合に発生する。

**解決方法1**: データベースをリセット（開発環境のみ）

```bash
# データベースを削除して再作成
docker compose exec web rails db:drop db:create db:migrate

# または
docker compose exec web rails db:migrate:reset
```

**解決方法2**: 問題のあるマイグレーションを手動で調整

```bash
# マイグレーション状態を確認
docker compose exec web rails db:migrate:status

# 特定のマイグレーションのステータスを変更（upに設定）
docker compose exec web rails db:migrate:up VERSION=20241128123456
```

**解決方法3**: 条件付きでテーブル作成

```ruby
class CreateUsers < ActiveRecord::Migration[8.1]
  def change
    # テーブルが存在しない場合のみ作成
    unless table_exists?(:users)
      create_table :users, id: :uuid do |t|
        t.string :name
        t.timestamps
      end
    end
  end
end
```

### 8.2 インデックス重複エラー

**エラー**: `PG::DuplicateObject: ERROR: relation "index_xxx" already exists`

```ruby
class AddIndexToUsers < ActiveRecord::Migration[8.1]
  def change
    # インデックスが存在しない場合のみ作成
    unless index_exists?(:users, :email)
      add_index :users, :email, unique: true
    end
  end
end
```

### 8.3 外部キー制約エラー

**エラー**: テーブルの作成順序が原因で外部キーが設定できない

**解決方法**: 外部キーを別マイグレーションで追加

```ruby
# 1. まずテーブルを作成（外部キーなし）
class CreatePosts < ActiveRecord::Migration[8.1]
  def change
    create_table :posts, id: :uuid do |t|
      t.uuid :author_id  # 外部キー制約なしで作成
      t.timestamps
    end
  end
end

# 2. 依存テーブル作成後に外部キーを追加
class AddForeignKeysToPosts < ActiveRecord::Migration[8.1]
  def change
    add_foreign_key :posts, :users, column: :author_id
  end
end
```

### 8.4 マイグレーションの状態を確認・修復

```bash
# 現在のマイグレーション状態を確認
docker compose exec web rails db:migrate:status

# 出力例:
#  Status   Migration ID    Migration Name
# --------------------------------------------------
#    up     20241128050000  Enable pgcrypto extension
#    up     20241128050100  Create users
#   down    20241128050200  Create posts  # ← 失敗している

# 特定バージョンまでロールバック
docker compose exec web rails db:rollback STEP=1

# 特定バージョンを実行
docker compose exec web rails db:migrate:up VERSION=20241128050200
```

### 8.5 スキーマの差分を確認

```bash
# 現在のスキーマをダンプ
docker compose exec web rails db:schema:dump

# スキーマの差分を確認（Git使用時）
git diff db/schema.rb
```

## 出力

- 全テーブルのマイグレーションファイルが作成されている
- `rails db:migrate` が正常に完了する
- `db/schema.rb` が期待通りのスキーマを反映している
