# ステップ13b: Administrateで管理画面を実装する

## 目次

- [概要](#概要)
- [セットアップ](#セットアップ)
- [ダッシュボードをカスタマイズする](#ダッシュボードをカスタマイズする)
- [カスタムフィールドの作成](#カスタムフィールドの作成)
- [RichTextフィールドの設定](#richtextフィールドの設定)

---

## 概要

Administrateはシンプルでカスタマイズ性の高い管理画面ライブラリです。Claudeは、ダッシュボードファイルを編集して管理画面を構築します。

## セットアップ

### Gemを追加する

```ruby
gem 'administrate'
```

```bash
bundle install
rails generate administrate:install
rails generate administrate:dashboard Post
```

## ダッシュボードをカスタマイズする

`app/dashboards/post_dashboard.rb`:

```ruby
require 'administrate/base_dashboard'

class PostDashboard < Administrate::BaseDashboard
  ATTRIBUTE_TYPES = {
    # uuid: 読み取り専用のID
    id: Field::String.with_options(searchable: false),

    # string: 一行テキスト
    title: Field::String,

    # richText: Action Textエディタ
    content: Field::RichText,

    # text: 複数行テキスト
    summary: Field::Text,

    # integer: 整数
    view_count: Field::Number.with_options(decimals: 0),

    # number: 小数
    price: Field::Number.with_options(decimals: 2, prefix: '¥'),

    # boolean: チェックボックス
    is_published: Field::Boolean,

    # date: 日時
    published_at: Field::DateTime.with_options(format: '%Y/%m/%d %H:%M'),

    # enum: セレクトボックス
    status: Field::Select.with_options(
      collection: ->(field) { Post.statuses.keys.map { |s| [Post.human_attribute_name("status.#{s}"), s] } }
    ),

    # relation: 関連モデル
    author: Field::BelongsTo.with_options(searchable: true, searchable_field: 'name'),
    category: Field::BelongsTo,
    tags: Field::HasMany,

    # image: 画像（カスタムフィールド）
    featured_image: Field::ActiveStorage,

    # custom型のフラット化されたフィールド
    seo_settings_title: Field::String,
    seo_settings_description: Field::Text,

    created_at: Field::DateTime,
    updated_at: Field::DateTime
  }.freeze

  COLLECTION_ATTRIBUTES = %i[
    id
    title
    status
    is_published
    author
    created_at
  ].freeze

  SHOW_PAGE_ATTRIBUTES = %i[
    id
    title
    content
    summary
    view_count
    price
    is_published
    published_at
    status
    author
    category
    tags
    featured_image
    seo_settings_title
    seo_settings_description
    created_at
    updated_at
  ].freeze

  FORM_ATTRIBUTES = %i[
    title
    content
    summary
    view_count
    price
    is_published
    published_at
    status
    author
    category
    tags
    featured_image
    seo_settings_title
    seo_settings_description
  ].freeze

  COLLECTION_FILTERS = {
    status: ->(resources, value) { resources.where(status: value) },
    is_published: ->(resources, value) { resources.where(is_published: value == 'true') }
  }.freeze
end
```

## カスタムフィールドの作成

### Active Storage用のカスタムフィールド

`app/fields/active_storage_field.rb`:

```ruby
require 'administrate/field/base'

class ActiveStorageField < Administrate::Field::Base
  def to_s
    data.filename if data.attached?
  end

  def attached?
    data.attached?
  end

  def url
    Rails.application.routes.url_helpers.rails_blob_path(data, only_path: true) if attached?
  end
end
```

`app/views/fields/active_storage_field/_show.html.erb`:

```erb
<% if field.attached? %>
  <%= image_tag field.url, height: 200 %>
<% else %>
  <span class="text-muted">画像なし</span>
<% end %>
```

`app/views/fields/active_storage_field/_form.html.erb`:

```erb
<div class="field-unit__field">
  <%= f.file_field field.attribute %>
  <% if field.attached? %>
    <div class="mt-2">
      <%= image_tag field.url, height: 100 %>
    </div>
  <% end %>
</div>
```

## RichTextフィールドの設定

Action Textを使用したリッチテキストフィールド：

`app/fields/rich_text_field.rb`:

```ruby
require 'administrate/field/base'

class RichTextField < Administrate::Field::Base
  def to_s
    data.to_s.truncate(100)
  end
end
```

`app/views/fields/rich_text_field/_form.html.erb`:

```erb
<div class="field-unit__field">
  <%= f.rich_text_area field.attribute %>
</div>
```

`app/views/fields/rich_text_field/_show.html.erb`:

```erb
<div class="rich-text-content">
  <%= field.data %>
</div>
```
