# ステップ9: ORマッピングを実装する

## 目次

- [目的](#目的)
- [手順](#手順)
  - [9.1 モデルファイルを作成する](#91-モデルファイルを作成する)
  - [9.2 基本的なモデル構造](#92-基本的なモデル構造)
  - [9.3 リレーションの実装](#93-リレーションの実装)
  - [9.4 relationOptionsに基づくdependentオプション](#94-relationoptionsに基づくdependentオプション)
  - [9.5 apiOptionsからスコープを自動導出する](#95-apioptionsからスコープを自動導出する)
  - [9.6 Ransackの設定（apiOptionsから自動導出）](#96-ransackの設定apioptionsから自動導出)
  - [9.7 Enum定義の実装](#97-enum定義の実装)
  - [9.8 全文検索の実装](#98-全文検索の実装)
  - [9.9 カスタム型の実装](#99-カスタム型の実装)
  - [9.10 コールバックの実装](#910-コールバックの実装)
  - [9.11 クエリメソッドの実装](#911-クエリメソッドの実装)
  - [9.12 ApplicationRecordの共通設定](#912-applicationrecordの共通設定)
- [出力](#出力)

---

## 目的

Active Recordモデルを作成し、JSON仕様の`apiOptions`と`relationOptions`に基づいてリレーション、スコープ、クエリメソッドを実装する。

## 手順

### 9.1 モデルファイルを作成する

```bash
rails generate model Post --skip-migration
```

または手動で `app/models/post.rb` を作成。

### 9.2 基本的なモデル構造

```ruby
# app/models/post.rb
class Post < ApplicationRecord
  # リレーション
  belongs_to :author, class_name: 'User'
  has_many :comments, dependent: :destroy
  has_many :taggings, dependent: :destroy
  has_many :tags, through: :taggings

  # Enum定義
  enum :status, {
    draft: 'draft',
    published: 'published',
    archived: 'archived'
  }, default: :draft

  # バリデーション（次のステップで詳細実装）
  validates :title, presence: true
  validates :status, presence: true

  # スコープ
  scope :recent, -> { order(created_at: :desc) }
  scope :by_status, ->(status) { where(status: status) if status.present? }
end
```

### 9.3 リレーションの実装

JSON仕様の`relationTo`に基づいてリレーションを定義：

#### 1対多（belongs_to / has_many）

```ruby
# Post belongs_to User
class Post < ApplicationRecord
  belongs_to :author, class_name: 'User', foreign_key: :author_id
end

class User < ApplicationRecord
  has_many :posts, foreign_key: :author_id, dependent: :destroy
end
```

#### 多対多（has_many through）

```ruby
class Post < ApplicationRecord
  has_many :taggings, dependent: :destroy
  has_many :tags, through: :taggings
end

class Tag < ApplicationRecord
  has_many :taggings, dependent: :destroy
  has_many :posts, through: :taggings
end

class Tagging < ApplicationRecord
  belongs_to :post
  belongs_to :tag
end
```

### 9.4 relationOptionsに基づくdependentオプション

JSON仕様の`relationOptions.onDelete`に基づいて、`has_many`/`has_one`の`dependent`オプションを設定する。

#### onDeleteとdependentオプションのマッピング

| onDelete値 | dependentオプション | 動作 |
|-----------|-------------------|------|
| `cascade` | `dependent: :destroy` | 親削除時に子も削除 |
| `nullify` | `dependent: :nullify` | 親削除時に外部キーをNULL設定 |
| `restrict` | `dependent: :restrict_with_error` | 子がある場合は削除禁止（デフォルト） |

#### 実装例

```ruby
# JSON仕様から自動導出
# User has_many posts (relationOptions.onDelete: "nullify")
# Category has_many posts (relationOptions.onDelete: "cascade")
# Department has_many users (relationOptions.onDelete: "restrict")

class User < ApplicationRecord
  # onDelete: nullify → dependent: :nullify
  has_many :posts,
    foreign_key: :author_id,
    dependent: :nullify  # relationOptions.onDelete: "nullify" から導出
end

class Category < ApplicationRecord
  # onDelete: cascade → dependent: :destroy
  has_many :posts,
    dependent: :destroy  # relationOptions.onDelete: "cascade" から導出
end

class Department < ApplicationRecord
  # onDelete: restrict → dependent: :restrict_with_error
  has_many :users,
    dependent: :restrict_with_error  # relationOptions.onDelete: "restrict" から導出
end
```

#### 注意事項

- `dependent: :destroy`は関連レコードのコールバックを実行する（`before_destroy`等）
- 大量データの場合は`dependent: :delete_all`を検討（コールバックなし）
- `dependent: :nullify`を使用する場合、外部キーカラムは`null: true`が必要

### 9.5 apiOptionsからスコープを自動導出する

JSON仕様の`apiOptions`に基づいて、フィルタリング・ソート用のスコープを自動導出する。

#### 導出ルール

| apiOptions設定 | 導出されるスコープ |
|---------------|------------------|
| `filterable: true` | `by_{field_name}` スコープ |
| `sortable: true` | ソート可能フィールドリスト |
| `searchable: true` | `search` スコープ |

#### フィルタ用スコープの導出（filterable: true）

```ruby
class Post < ApplicationRecord
  # apiOptions.filterable: true のフィールドからスコープを自動導出

  # status (enum, filterable: true)
  scope :by_status, ->(status) { where(status: status) if status.present? }

  # category_id (relation, filterable: true)
  scope :by_category, ->(category_id) { where(category_id: category_id) if category_id.present? }

  # created_at (date, filterable: true) - 範囲フィルタ
  scope :created_from, ->(date) { where('created_at >= ?', date) if date.present? }
  scope :created_to, ->(date) { where('created_at <= ?', date) if date.present? }

  # price (integer, filterable: true) - 範囲フィルタ
  scope :price_min, ->(value) { where('price >= ?', value) if value.present? }
  scope :price_max, ->(value) { where('price <= ?', value) if value.present? }
end
```

#### ソート用設定の導出（sortable: true）

```ruby
class Post < ApplicationRecord
  # apiOptions.sortable: true のフィールドをリスト化
  SORTABLE_FIELDS = %w[created_at updated_at title price].freeze

  class << self
    def sorted_by(field, direction = 'desc')
      field = SORTABLE_FIELDS.include?(field) ? field : 'created_at'
      direction = %w[asc desc].include?(direction) ? direction : 'desc'
      order(field => direction)
    end
  end
end
```

#### 全文検索スコープの導出（searchable: true）

```ruby
class Post < ApplicationRecord
  # apiOptions.searchable: true のフィールド: title, content
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

### 9.6 Ransackの設定（apiOptionsから自動導出）

JSON仕様の`apiOptions`に基づいて、Ransackで検索可能な属性を自動導出する。

#### ransackable_attributesの導出

`apiOptions.filterable: true` または `apiOptions.sortable: true` のフィールドを抽出：

```ruby
class Post < ApplicationRecord
  # apiOptions.filterable: true または sortable: true から導出
  def self.ransackable_attributes(auth_object = nil)
    %w[
      title        # filterable: true, sortable: true
      status       # filterable: true
      created_at   # filterable: true, sortable: true
      updated_at   # sortable: true
      author_id    # filterable: true (relation)
      category_id  # filterable: true (relation)
    ]
  end

  # relationOptions.expandable: true から導出
  def self.ransackable_associations(auth_object = nil)
    %w[author category tags]
  end
end
```

#### マッピング表

```markdown
## Ransack設定（JSON仕様から自動導出）

### ransackable_attributes
| フィールド | 由来 |
|-----------|------|
| title | apiOptions.filterable: true, sortable: true |
| status | apiOptions.filterable: true |
| created_at | apiOptions.filterable: true, sortable: true |
| updated_at | apiOptions.sortable: true |
| author_id | apiOptions.filterable: true (relation) |
| category_id | apiOptions.filterable: true (relation) |

### ransackable_associations
| リレーション | 由来 |
|-------------|------|
| author | relationOptions.expandable: true |
| category | relationOptions.expandable: true |
| tags | relationOptions.expandable: true |
```

### 9.7 Enum定義の実装

Rails 8のenumを使用してEnum型フィールドを実装：

```ruby
class Post < ApplicationRecord
  # JSON仕様のenum定義から導出
  enum :status, {
    draft: 'draft',
    published: 'published',
    archived: 'archived'
  }, default: :draft
end
```

### 9.8 全文検索の実装

`apiOptions.searchable: true`のフィールドに対して全文検索を実装：

```ruby
class Post < ApplicationRecord
  # apiOptions.searchable: true のフィールド: title, content
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

**注意**: ORDER BY句では`sanitize_sql_array`を使用してパラメータをサニタイズします。

### 9.9 カスタム型の実装（Virtual Attributes）

カスタム型をネストした属性として扱う：

```ruby
class Post < ApplicationRecord
  # カスタム型のアクセサ
  def seo_settings
    {
      title: seo_settings_title,
      description: seo_settings_description
    }
  end

  def seo_settings=(value)
    self.seo_settings_title = value[:title] || value['title']
    self.seo_settings_description = value[:description] || value['description']
  end
end
```

### 9.10 コールバックの実装（必要な場合）

```ruby
class Post < ApplicationRecord
  before_validation :set_default_status, on: :create

  private

  def set_default_status
    self.status ||= :draft
  end
end
```

### 9.11 クエリメソッドの実装

複雑なクエリをクラスメソッドとして実装。`apiOptions`から導出したフィルタ・ソートを組み合わせる：

```ruby
class Post < ApplicationRecord
  # apiOptions.filterable: true から導出したフィールドリスト
  FILTERABLE_FIELDS = %w[status category_id author_id].freeze

  # apiOptions.sortable: true から導出したフィールドリスト
  SORTABLE_FIELDS = %w[created_at updated_at title].freeze

  class << self
    def filter_by(params)
      result = all

      # apiOptions.filterable: true のフィールドでフィルタ
      result = result.by_status(params[:status]) if params[:status]
      result = result.by_category(params[:category_id]) if params[:category_id]
      result = result.by_author(params[:author_id]) if params[:author_id]

      # 日付範囲フィルタ (filterable: true の date型)
      result = result.created_from(params[:created_at_from]) if params[:created_at_from]
      result = result.created_to(params[:created_at_to]) if params[:created_at_to]

      # 全文検索 (apiOptions.searchable: true)
      result = result.search(params[:q]) if params[:q]

      result
    end

    def sorted_by(field, direction = 'desc')
      # apiOptions.sortable: true のフィールドのみ許可
      field = SORTABLE_FIELDS.include?(field) ? field : 'created_at'
      direction = %w[asc desc].include?(direction) ? direction : 'desc'
      order(field => direction)
    end
  end
end
```

### 9.12 ApplicationRecordの共通設定

```ruby
# app/models/application_record.rb
class ApplicationRecord < ActiveRecord::Base
  primary_abstract_class

  # UUID主キーを使用する場合
  # self.implicit_order_column = 'created_at'
end
```

## 出力

以下の形式でORマッピング実装結果をまとめる：

```markdown
## ORマッピング実装結果

### モデル一覧

| モデル | ファイル | リレーション数 | スコープ数 |
|--------|---------|--------------|-----------|
| Post | app/models/post.rb | 4 | 8 |
| User | app/models/user.rb | 2 | 3 |
| Category | app/models/category.rb | 1 | 2 |

### dependent設定（relationOptions.onDeleteから導出）

| 親モデル | 子モデル | onDelete | dependent |
|---------|---------|----------|-----------|
| User | Post | nullify | :nullify |
| Category | Post | cascade | :destroy |
| Department | User | restrict | :restrict_with_error |

### フィルタ用スコープ（apiOptions.filterableから導出）

| モデル | スコープ名 | 対象フィールド | 型 |
|--------|-----------|---------------|-----|
| Post | by_status | status | enum |
| Post | by_category | category_id | relation |
| Post | created_from/to | created_at | date |

### ソート設定（apiOptions.sortableから導出）

| モデル | SORTABLE_FIELDS |
|--------|-----------------|
| Post | created_at, updated_at, title |
| Product | created_at, price, name |

### Ransack設定（apiOptionsから導出）

| モデル | ransackable_attributes | ransackable_associations |
|--------|------------------------|--------------------------|
| Post | title, status, created_at, author_id | author, category, tags |
```

### 確認事項

- 全モデルのファイルが作成されている
- リレーションとdependentオプションが正しく定義されている
- apiOptionsから導出したスコープが実装されている
- `rails console` でモデルが正常に動作することを確認
