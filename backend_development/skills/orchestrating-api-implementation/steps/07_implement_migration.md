# ステップ7: DBマイグレーションを実装する

## 目的

ステップ4, 5で設計したスキーマとインデックスをRailsマイグレーションとして実装する。

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

## 出力

- 全テーブルのマイグレーションファイルが作成されている
- `rails db:migrate` が正常に完了する
- `db/schema.rb` が期待通りのスキーマを反映している
