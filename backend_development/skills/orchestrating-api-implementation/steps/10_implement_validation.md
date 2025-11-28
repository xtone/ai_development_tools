# ステップ10: バリデーションを実装する

## 目次

- [目的](#目的)
- [手順](#手順)
  - [9.1 JSON仕様とRailsバリデーションのマッピング](#91-json仕様とrailsバリデーションのマッピング)
  - [9.2 基本バリデーションの実装](#92-基本バリデーションの実装)
  - [9.3 Enum値のバリデーション](#93-enum値のバリデーション)
  - [9.4 日本語enumValuesの対応方法](#94-日本語enumvaluesの対応方法)
  - [9.5 リレーションのバリデーション](#95-リレーションのバリデーション)
  - [9.6 カスタムバリデーション](#96-カスタムバリデーション)
  - [9.7 エラーメッセージのカスタマイズ](#97-エラーメッセージのカスタマイズ)
- [出力](#出力)

---

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

#### 英語キーの場合（推奨）

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

#### 日本語enumValuesの対応方法

JSON仕様で `enumValues: ["ドラフト", "公開"]` のように日本語が定義されている場合、以下の方法で対応する：

**方法1: 英語キーを使用し、i18nで日本語表示（推奨）**

```ruby
# app/models/article.rb
class Article < ApplicationRecord
  # DBには英語キーで保存
  enum :publish_status, {
    draft: 'draft',
    published: 'published'
  }
end
```

```yaml
# config/locales/ja.yml
ja:
  activerecord:
    attributes:
      article:
        publish_status: 公開ステータス
    enums:
      article:
        publish_status:
          draft: ドラフト
          published: 公開
```

```ruby
# 表示時
Article.human_attribute_name("publish_status.#{article.publish_status}")
# => "ドラフト" または "公開"

# フォームでの選択肢
Article.publish_statuses.keys.map { |k| [Article.human_attribute_name("publish_status.#{k}"), k] }
# => [["ドラフト", "draft"], ["公開", "published"]]
```

**方法2: string型でinclusion validationを使用**

日本語の値をそのままDBに保存する場合：

```ruby
# app/models/article.rb
class Article < ApplicationRecord
  PUBLISH_STATUSES = %w[ドラフト 公開].freeze

  validates :publish_status, inclusion: {
    in: PUBLISH_STATUSES,
    message: "は「#{PUBLISH_STATUSES.join('」「')}」のいずれかを選択してください"
  }, allow_blank: true

  # スコープ
  scope :draft, -> { where(publish_status: 'ドラフト') }
  scope :published, -> { where(publish_status: '公開') }

  def draft?
    publish_status == 'ドラフト'
  end

  def published?
    publish_status == '公開'
  end
end
```

> **注意**: 方法2はDBに日本語が保存されるため、将来の多言語対応が困難になります。特別な理由がない限り、**方法1（英語キー + i18n）を推奨**します。

**enumとinclusion validationの衝突を避ける**

Rails enumを使用する場合、enumが自動的にバリデーションを行うため、別途inclusion validationを追加すると衝突する可能性があります：

```ruby
# NG: enumとinclusionを併用するとエラーになる場合がある
enum :status, { draft: 'draft', published: 'published' }
validates :status, inclusion: { in: %w[draft published] }  # 不要

# OK: enumのみ使用
enum :status, { draft: 'draft', published: 'published' }
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
