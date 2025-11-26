# ステップ8: ORマッピングを実装する

## 目的

Active Recordモデルを作成し、リレーション、スコープ、クエリメソッドを実装する。

## 手順

### 8.1 モデルファイルを作成する

```bash
rails generate model Post --skip-migration
```

または手動で `app/models/post.rb` を作成。

### 8.2 基本的なモデル構造

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

### 8.3 リレーションの実装

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

### 8.4 スコープの実装

よく使うクエリをスコープとして定義：

```ruby
class Post < ApplicationRecord
  # 基本スコープ
  scope :recent, -> { order(created_at: :desc) }
  scope :published, -> { where(status: :published) }

  # フィルタリング用スコープ
  scope :by_status, ->(status) { where(status: status) if status.present? }
  scope :by_author, ->(author_id) { where(author_id: author_id) if author_id.present? }
  scope :created_after, ->(date) { where('created_at >= ?', date) if date.present? }
  scope :created_before, ->(date) { where('created_at <= ?', date) if date.present? }

  # 全文検索スコープ
  scope :search, ->(query) {
    return all if query.blank?
    where("searchable @@ plainto_tsquery('japanese', ?)", query)
  }

  # 関連データの事前読み込み
  scope :with_author, -> { includes(:author) }
  scope :with_tags, -> { includes(:tags) }
end
```

### 8.5 Ransackの設定（検索用）

```ruby
class Post < ApplicationRecord
  # Ransackで検索可能な属性を制限
  def self.ransackable_attributes(auth_object = nil)
    %w[title status created_at updated_at author_id]
  end

  def self.ransackable_associations(auth_object = nil)
    %w[author tags]
  end
end
```

### 8.6 カスタム型の実装（Virtual Attributes）

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

### 8.7 コールバックの実装（必要な場合）

```ruby
class Post < ApplicationRecord
  before_validation :set_default_status, on: :create

  private

  def set_default_status
    self.status ||= :draft
  end
end
```

### 8.8 クエリメソッドの実装

複雑なクエリをクラスメソッドとして実装：

```ruby
class Post < ApplicationRecord
  class << self
    def filter_by(params)
      result = all
      result = result.by_status(params[:status]) if params[:status]
      result = result.by_author(params[:author_id]) if params[:author_id]
      result = result.search(params[:q]) if params[:q]
      result
    end

    def sorted_by(sort_field, sort_order = 'desc')
      allowed_fields = %w[created_at updated_at title]
      field = allowed_fields.include?(sort_field) ? sort_field : 'created_at'
      order = %w[asc desc].include?(sort_order) ? sort_order : 'desc'
      order(field => order)
    end
  end
end
```

### 8.9 ApplicationRecordの共通設定

```ruby
# app/models/application_record.rb
class ApplicationRecord < ActiveRecord::Base
  primary_abstract_class

  # UUID主キーを使用する場合
  # self.implicit_order_column = 'created_at'
end
```

## 出力

- 全モデルのファイルが作成されている
- リレーションが正しく定義されている
- `rails console` でモデルが正常に動作することを確認
