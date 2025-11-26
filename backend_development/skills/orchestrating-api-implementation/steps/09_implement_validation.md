# ステップ9: バリデーションを実装する

## 目的

JSON仕様の`validation`設定に基づいて、Active Recordバリデーションを実装する。

## 手順

### 9.1 JSON仕様とRailsバリデーションのマッピング

| JSON仕様 | Railsバリデーション |
|---------|-------------------|
| `required: true` | `validates :field, presence: true` |
| `min` (数値) | `validates :field, numericality: { greater_than_or_equal_to: min }` |
| `max` (数値) | `validates :field, numericality: { less_than_or_equal_to: max }` |
| `min` (文字列) | `validates :field, length: { minimum: min }` |
| `max` (文字列) | `validates :field, length: { maximum: max }` |
| `pattern` | `validates :field, format: { with: /pattern/ }` |
| `unique: true` | `validates :field, uniqueness: true` |

### 9.2 基本バリデーションの実装

```ruby
class Post < ApplicationRecord
  # 必須
  validates :title, presence: true
  validates :status, presence: true

  # 文字列長
  validates :title, length: { maximum: 255 }
  validates :content, length: { maximum: 65535 }, allow_blank: true

  # 数値
  validates :view_count, numericality: {
    only_integer: true,
    greater_than_or_equal_to: 0
  }, allow_nil: true

  # ユニーク
  validates :slug, uniqueness: true, allow_blank: true

  # フォーマット
  validates :email, format: {
    with: URI::MailTo::EMAIL_REGEXP,
    message: 'は有効なメールアドレス形式で入力してください'
  }, allow_blank: true
end
```

### 9.3 Enum値のバリデーション

```ruby
class Post < ApplicationRecord
  enum :status, {
    draft: 'draft',
    published: 'published',
    archived: 'archived'
  }

  # Enumは自動的にバリデーションされるが、明示的に追加も可能
  validates :status, inclusion: { in: statuses.keys }
end
```

### 9.4 リレーションのバリデーション

```ruby
class Post < ApplicationRecord
  belongs_to :author, class_name: 'User'

  # belongs_toはRails 5以降デフォルトでrequired
  # optional: true で任意に変更可能
  belongs_to :category, optional: true

  # 存在確認を明示的に
  validates :author, presence: true
end
```

### 9.5 カスタムバリデーションの実装

```ruby
class Post < ApplicationRecord
  validate :published_at_must_be_in_past, if: :published?

  private

  def published_at_must_be_in_past
    if published_at.present? && published_at > Time.current
      errors.add(:published_at, '公開日は現在時刻より前である必要があります')
    end
  end
end
```

### 9.6 条件付きバリデーション

```ruby
class Post < ApplicationRecord
  # 公開時のみ必須
  validates :content, presence: true, if: :published?

  # 下書き以外は必須
  validates :slug, presence: true, unless: :draft?
end
```

### 9.7 ネストした属性のバリデーション（カスタム型）

```ruby
class Post < ApplicationRecord
  # カスタム型のバリデーション
  validate :validate_seo_settings

  private

  def validate_seo_settings
    if seo_settings_title.present? && seo_settings_title.length > 60
      errors.add(:seo_settings_title, 'は60文字以内で入力してください')
    end

    if seo_settings_description.present? && seo_settings_description.length > 160
      errors.add(:seo_settings_description, 'は160文字以内で入力してください')
    end
  end
end
```

### 9.8 バリデーションヘルパーの作成

共通のバリデーションロジックをconcernに抽出：

```ruby
# app/models/concerns/validatable.rb
module Validatable
  extend ActiveSupport::Concern

  class_methods do
    def validates_json_spec(field, spec)
      validations = {}

      validations[:presence] = true if spec[:required]

      if spec[:min] || spec[:max]
        if column_for_attribute(field).type == :string
          validations[:length] = {}
          validations[:length][:minimum] = spec[:min] if spec[:min]
          validations[:length][:maximum] = spec[:max] if spec[:max]
        else
          validations[:numericality] = {}
          validations[:numericality][:greater_than_or_equal_to] = spec[:min] if spec[:min]
          validations[:numericality][:less_than_or_equal_to] = spec[:max] if spec[:max]
        end
      end

      validations[:format] = { with: Regexp.new(spec[:pattern]) } if spec[:pattern]
      validations[:uniqueness] = true if spec[:unique]

      validates field, validations unless validations.empty?
    end
  end
end
```

### 9.9 エラーメッセージのカスタマイズ

`config/locales/ja.yml`:

```yaml
ja:
  activerecord:
    errors:
      messages:
        blank: を入力してください
        too_short: は%{count}文字以上で入力してください
        too_long: は%{count}文字以内で入力してください
        invalid: は不正な値です
        taken: はすでに使用されています
      models:
        post:
          attributes:
            title:
              blank: タイトルを入力してください
```

## 出力

- 全モデルにJSON仕様に基づくバリデーションが実装されている
- `rails console` で `model.valid?` が正しく動作する
- エラーメッセージが適切に表示される
