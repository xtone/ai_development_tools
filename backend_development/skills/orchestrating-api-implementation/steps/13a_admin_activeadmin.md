# ステップ13a: ActiveAdminで管理画面を実装する

## 目次

- [概要](#概要)
- [セットアップ](#セットアップ)
- [リソースを登録する](#リソースを登録する)
- [リッチテキストエディタのセットアップ](#リッチテキストエディタのセットアップ)
- [画像アップロードのセットアップ](#画像アップロードのセットアップ)
- [名前衝突を回避する](#名前衝突を回避する)
- [日本語化する](#日本語化する)
- [Deviseのtrackableカラム](#deviseのtrackableカラム)
- [カスタムアクションの実装](#カスタムアクションの実装)
- [data-testid属性の追加](#data-testid属性の追加)

---

## 概要

ActiveAdminはDSLベースの管理画面ライブラリです。Claudeは、シンプルな設定で高機能な管理画面を素早く構築します。

## セットアップ

### Gemを追加する

```ruby
gem 'activeadmin'
gem 'devise'  # 認証
gem 'dartsass-rails'  # ActiveAdminがSassに依存
```

```bash
bundle install
rails generate active_admin:install --skip-users
rails db:migrate
```

## リソースを登録する

`app/admin/posts.rb`:

```ruby
ActiveAdmin.register Post do
  permit_params :title, :content, :summary, :view_count, :price, :is_published,
                :published_at, :status, :author_id, :category_id, :featured_image,
                :seo_settings_title, :seo_settings_description

  # 一覧
  index do
    selectable_column
    id_column
    column :title
    column :status
    column :is_published
    column :author
    column :created_at
    actions
  end

  # フィルタ
  filter :title
  filter :status
  filter :is_published
  filter :author
  filter :created_at

  # 詳細
  show do
    attributes_table do
      row :id
      row :title
      row(:content) { |post| post.content.html_safe }  # richText
      row :summary
      row :view_count
      row :price
      row :is_published
      row :published_at
      row :status
      row :author
      row(:featured_image) { |post| image_tag(post.featured_image) if post.featured_image.attached? }
      row :created_at
      row :updated_at
    end

    panel 'SEO設定' do
      attributes_table_for post do
        row :seo_settings_title
        row :seo_settings_description
      end
    end
  end

  # フォーム（データ型に応じた入力フォーム）
  form do |f|
    f.inputs '基本情報' do
      # string: 一行テキスト
      f.input :title, as: :string

      # richText: リッチテキストエディタ（Action Text使用）
      f.input :content, as: :trix_editor

      # text: 複数行テキストエリア
      f.input :summary, as: :text, input_html: { rows: 5 }

      # integer: 整数入力
      f.input :view_count, as: :number, input_html: { step: 1, min: 0 }

      # number: 小数入力
      f.input :price, as: :number, input_html: { step: 0.01, min: 0 }

      # boolean: チェックボックス
      f.input :is_published, as: :boolean

      # date: 日時ピッカー
      f.input :published_at, as: :datetime_picker

      # enum: セレクトボックス
      f.input :status, as: :select, collection: Post.statuses.keys.map { |s| [Post.human_attribute_name("status.#{s}"), s] }

      # relation: 関連モデル選択
      f.input :author, as: :select, collection: User.all.map { |u| [u.name, u.id] }
      f.input :category, as: :select, collection: Category.all.map { |c| [c.name, c.id] }

      # image: ファイルアップロード
      f.input :featured_image, as: :file, hint: f.object.featured_image.attached? ? image_tag(f.object.featured_image, height: 100) : nil
    end

    f.inputs 'SEO設定' do
      f.input :seo_settings_title, as: :string
      f.input :seo_settings_description, as: :text, input_html: { rows: 3 }
    end

    f.actions
  end
end
```

## リッチテキストエディタのセットアップ

Action Textを使用する場合：

```bash
rails action_text:install
rails db:migrate
```

`app/models/post.rb`:

```ruby
class Post < ApplicationRecord
  has_rich_text :content
end
```

ActiveAdminでTrixエディタを使用：

```ruby
# app/admin/inputs/trix_editor_input.rb
class TrixEditorInput < Formtastic::Inputs::TextInput
  def to_html
    input_wrapping do
      label_html <<
      template.content_tag(:div, class: 'trix-editor-wrapper') do
        builder.rich_text_area(method, input_html_options)
      end
    end
  end
end
```

## 画像アップロードのセットアップ

Active Storageを使用：

```bash
rails active_storage:install
rails db:migrate
```

`app/models/post.rb`:

```ruby
class Post < ApplicationRecord
  has_one_attached :featured_image
end
```

## 名前衝突を回避する

アプリケーションに`Comment`モデルがある場合、ActiveAdminの内部`Comment`モデルと衝突します。`as`オプションで別名を指定して回避：

```ruby
# app/admin/comments.rb
ActiveAdmin.register Comment, as: "AppComment" do
  menu label: "コメント"
  # ... 設定
end
```

## 日本語化する

### 日本語ロケールの設定

`config/application.rb`:

```ruby
config.i18n.default_locale = :ja
config.i18n.available_locales = [:ja, :en]
config.time_zone = "Tokyo"
```

### モデル名・属性名の翻訳ファイル

`config/locales/ja.yml`:

```yaml
ja:
  activerecord:
    models:
      article: 記事
      account: ユーザーアカウント
      comment: コメント
      admin_user: 管理者

    attributes:
      article:
        id: ID
        title: タイトル
        contents: 本文
        account_id: 作成ユーザーID
        published_at: 公開日時
        created_at: 作成日時
        updated_at: 更新日時

  date:
    formats:
      default: "%Y/%m/%d"
  time:
    formats:
      default: "%Y/%m/%d %H:%M:%S"

  errors:
    messages:
      blank: を入力してください
      taken: はすでに存在します
```

### ActiveAdmin UIの翻訳

`config/locales/active_admin.ja.yml`:

```yaml
ja:
  active_admin:
    dashboard: ダッシュボード
    dashboard_welcome:
      welcome: ようこそ
      call_to_action: 左メニューからリソースを選択してください
    view: 詳細
    edit: 編集
    delete: 削除
    delete_confirmation: 本当に削除しますか？
    new_model: "%{model}を作成"
    edit_model: "%{model}を編集"
    create_model: "%{model}を作成"
    update_model: "%{model}を更新"
    delete_model: "%{model}を削除"
```

### リソースでの日本語ラベル

```ruby
ActiveAdmin.register Article do
  menu label: "記事", priority: 1

  index title: "記事一覧" do
    selectable_column
    id_column
    column "タイトル", :title
    column "作成ユーザー", :account
    column "公開日時", :published_at
    actions
  end

  filter :title, label: "タイトル"
  filter :account, label: "作成ユーザー"

  form title: "記事" do |f|
    f.inputs "基本情報" do
      f.input :title, label: "タイトル"
      f.input :contents, label: "本文", as: :text
    end
    f.actions
  end
end
```

## Deviseのtrackableカラム

AdminUserで`current_sign_in_at`や`sign_in_count`を表示する場合、Deviseの`:trackable`モジュールを有効にする必要があります：

```ruby
# app/models/admin_user.rb
class AdminUser < ApplicationRecord
  devise :database_authenticatable,
         :recoverable, :rememberable, :validatable,
         :trackable  # これを追加
end
```

マイグレーションで必要なカラムを追加：

```ruby
add_column :admin_users, :sign_in_count, :integer, default: 0, null: false
add_column :admin_users, :current_sign_in_at, :datetime
add_column :admin_users, :last_sign_in_at, :datetime
add_column :admin_users, :current_sign_in_ip, :string
add_column :admin_users, :last_sign_in_ip, :string
```

## カスタムアクションの実装

### ステータス変更アクション（公開/非公開）

```ruby
ActiveAdmin.register Article do
  # バッチアクション
  batch_action :publish do |ids|
    batch_action_collection.find(ids).each do |article|
      article.update!(publish_status: 'published', published_at: Time.current)
    end
    redirect_to collection_path, notice: "#{ids.size}件の記事を公開しました"
  end

  batch_action :unpublish do |ids|
    batch_action_collection.find(ids).each do |article|
      article.update!(publish_status: 'draft')
    end
    redirect_to collection_path, notice: "#{ids.size}件の記事を下書きに戻しました"
  end

  # 個別アクション
  member_action :publish, method: :post do
    resource.update!(publish_status: 'published', published_at: Time.current)
    redirect_to admin_article_path(resource), notice: '記事を公開しました'
  end

  member_action :unpublish, method: :post do
    resource.update!(publish_status: 'draft')
    redirect_to admin_article_path(resource), notice: '記事を下書きに戻しました'
  end

  action_item :publish, only: :show, if: proc { resource.publish_status != 'published' } do
    link_to '公開する', publish_admin_article_path(resource), method: :post,
            data: { confirm: '記事を公開しますか？' },
            class: 'action-item-button'
  end

  action_item :unpublish, only: :show, if: proc { resource.publish_status == 'published' } do
    link_to '下書きに戻す', unpublish_admin_article_path(resource), method: :post,
            data: { confirm: '記事を下書きに戻しますか？' },
            class: 'action-item-button'
  end
end
```

## data-testid属性の追加

Playwright等の自動テストツールで確実に要素を選択できるようにします：

```ruby
ActiveAdmin.register Article do
  index do
    selectable_column
    id_column
    column :title do |article|
      link_to article.title, admin_article_path(article),
              'data-testid': "article-link-#{article.id}"
    end
    actions defaults: false do |article|
      item '詳細', admin_article_path(article), 'data-testid': "detail-#{article.id}"
      item '編集', edit_admin_article_path(article), 'data-testid': "edit-#{article.id}"
      item '削除', admin_article_path(article), method: :delete,
           'data-testid': "delete-#{article.id}",
           data: { confirm: '削除しますか？' }
    end
  end
end
```
