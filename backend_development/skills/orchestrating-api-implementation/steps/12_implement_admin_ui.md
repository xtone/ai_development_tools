# ステップ12: 管理画面を実装する

## 目的

モデルのデータを管理するための管理画面を実装する。

## 手順

### 12.1 管理画面の方式を選択する

ステップ2で決定した方式に基づいて実装。

| 方式 | 実装方法 |
|------|----------|
| ActiveAdmin | Gem導入、DSLで定義 |
| Administrate | Gem導入、ダッシュボード生成 |
| Hotwire | Rails Viewで自作 |
| React/Next.js | 別アプリとしてAPI連携 |

---

## 方式A: ActiveAdminを使用する場合

### A.1 Gemを追加する

```ruby
gem 'activeadmin'
gem 'devise'  # 認証（後のフェーズで詳細実装）
```

```bash
bundle install
rails generate active_admin:install --skip-users
rails db:migrate
```

### A.2 リソースを登録する

`app/admin/posts.rb`:

```ruby
ActiveAdmin.register Post do
  permit_params :title, :content, :status, :author_id, :category_id,
                :seo_settings_title, :seo_settings_description

  # 一覧
  index do
    selectable_column
    id_column
    column :title
    column :status
    column :author
    column :created_at
    actions
  end

  # フィルタ
  filter :title
  filter :status
  filter :author
  filter :created_at

  # 詳細
  show do
    attributes_table do
      row :id
      row :title
      row :content
      row :status
      row :author
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

  # フォーム
  form do |f|
    f.inputs '基本情報' do
      f.input :title
      f.input :content, as: :text
      f.input :status, as: :select, collection: Post.statuses.keys
      f.input :author, as: :select, collection: User.all
      f.input :category
    end

    f.inputs 'SEO設定' do
      f.input :seo_settings_title
      f.input :seo_settings_description
    end

    f.actions
  end
end
```

### A.3 ActiveAdmin::Commentとの名前衝突を回避する

アプリケーションに`Comment`モデルがある場合、ActiveAdminの内部`Comment`モデルと衝突する。
`as`オプションで別名を指定して回避：

```ruby
# app/admin/comments.rb
ActiveAdmin.register Comment, as: "AppComment" do
  menu label: "コメント"

  # ... 設定
end
```

### A.4 管理画面を日本語化する

#### 日本語ロケールの設定

`config/application.rb`:

```ruby
config.i18n.default_locale = :ja
config.i18n.available_locales = [:ja, :en]
config.time_zone = "Tokyo"
```

#### モデル名・属性名の翻訳ファイル

JSON仕様の`displayName`を使用して翻訳ファイルを作成：

`config/locales/ja.yml`:

```yaml
ja:
  activerecord:
    models:
      article: 記事          # displayName
      account: ユーザーアカウント
      comment: コメント
      admin_user: 管理者

    attributes:
      article:
        id: ID
        title: タイトル      # フィールドのdisplayName
        contents: 本文
        account_id: 作成ユーザーID
        published_at: 公開日時
        created_at: 作成日時
        updated_at: 更新日時

  # 日付フォーマット
  date:
    formats:
      default: "%Y/%m/%d"
  time:
    formats:
      default: "%Y/%m/%d %H:%M:%S"

  # エラーメッセージ
  errors:
    messages:
      blank: を入力してください
      taken: はすでに存在します
      # ...
```

#### ActiveAdmin UIの翻訳

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
    # ...
```

#### ActiveAdminリソースでの日本語ラベル

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

### A.5 Deviseのtrackableカラムに関する注意

AdminUserで`current_sign_in_at`や`sign_in_count`を表示する場合、
Deviseの`:trackable`モジュールを有効にする必要がある：

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

---

## 方式B: Administrateを使用する場合

### B.1 Gemを追加する

```ruby
gem 'administrate'
```

```bash
bundle install
rails generate administrate:install
rails generate administrate:dashboard Post
```

### B.2 ダッシュボードをカスタマイズする

`app/dashboards/post_dashboard.rb`:

```ruby
require 'administrate/base_dashboard'

class PostDashboard < Administrate::BaseDashboard
  ATTRIBUTE_TYPES = {
    id: Field::String,
    title: Field::String,
    content: Field::Text,
    status: Field::Select.with_options(
      collection: ->(field) { Post.statuses.keys }
    ),
    author: Field::BelongsTo,
    category: Field::BelongsTo,
    tags: Field::HasMany,
    seo_settings_title: Field::String,
    seo_settings_description: Field::Text,
    created_at: Field::DateTime,
    updated_at: Field::DateTime
  }.freeze

  COLLECTION_ATTRIBUTES = %i[id title status author created_at].freeze
  SHOW_PAGE_ATTRIBUTES = %i[id title content status author category tags seo_settings_title seo_settings_description created_at updated_at].freeze
  FORM_ATTRIBUTES = %i[title content status author category tags seo_settings_title seo_settings_description].freeze
  COLLECTION_FILTERS = {}.freeze
end
```

---

## 方式C: Hotwireで自作する場合

### C.1 管理画面用のコントローラを作成する

```bash
rails generate controller Admin::Posts index show new edit
```

### C.2 ルーティングを設定する

```ruby
namespace :admin do
  resources :posts
  root to: 'dashboard#index'
end
```

### C.3 レイアウトを作成する

`app/views/layouts/admin.html.erb`:

```erb
<!DOCTYPE html>
<html>
<head>
  <title>管理画面</title>
  <%= csrf_meta_tags %>
  <%= csp_meta_tag %>
  <%= stylesheet_link_tag 'tailwind', 'inter-font', 'data-turbo-track': 'reload' %>
  <%= javascript_importmap_tags %>
</head>
<body class="bg-gray-100">
  <div class="flex h-screen">
    <!-- サイドバー -->
    <aside class="w-64 bg-gray-800 text-white">
      <nav class="p-4">
        <ul class="space-y-2">
          <li><%= link_to 'ダッシュボード', admin_root_path, class: 'block p-2 hover:bg-gray-700 rounded' %></li>
          <li><%= link_to '投稿', admin_posts_path, class: 'block p-2 hover:bg-gray-700 rounded' %></li>
        </ul>
      </nav>
    </aside>

    <!-- メインコンテンツ -->
    <main class="flex-1 overflow-y-auto p-8">
      <%= yield %>
    </main>
  </div>
</body>
</html>
```

### C.4 一覧画面を実装する

`app/views/admin/posts/index.html.erb`:

```erb
<div class="bg-white shadow rounded-lg">
  <div class="px-6 py-4 border-b flex justify-between items-center">
    <h1 class="text-xl font-semibold">投稿一覧</h1>
    <%= link_to '新規作成', new_admin_post_path, class: 'bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600' %>
  </div>

  <table class="w-full">
    <thead class="bg-gray-50">
      <tr>
        <th class="px-6 py-3 text-left text-sm font-medium text-gray-500">タイトル</th>
        <th class="px-6 py-3 text-left text-sm font-medium text-gray-500">ステータス</th>
        <th class="px-6 py-3 text-left text-sm font-medium text-gray-500">作成日</th>
        <th class="px-6 py-3"></th>
      </tr>
    </thead>
    <tbody class="divide-y">
      <% @posts.each do |post| %>
        <tr>
          <td class="px-6 py-4"><%= post.title %></td>
          <td class="px-6 py-4"><%= post.status %></td>
          <td class="px-6 py-4"><%= l post.created_at, format: :short %></td>
          <td class="px-6 py-4 text-right">
            <%= link_to '編集', edit_admin_post_path(post), class: 'text-blue-500 hover:underline' %>
            <%= link_to '削除', admin_post_path(post), method: :delete, data: { confirm: '削除しますか？' }, class: 'text-red-500 hover:underline ml-2' %>
          </td>
        </tr>
      <% end %>
    </tbody>
  </table>

  <div class="px-6 py-4">
    <%== pagy_nav(@pagy) %>
  </div>
</div>
```

### C.5 フォーム画面を実装する

`app/views/admin/posts/_form.html.erb`:

```erb
<%= form_with model: [:admin, post], class: 'space-y-6' do |f| %>
  <% if post.errors.any? %>
    <div class="bg-red-50 border border-red-200 rounded p-4">
      <ul class="list-disc list-inside text-red-600">
        <% post.errors.full_messages.each do |message| %>
          <li><%= message %></li>
        <% end %>
      </ul>
    </div>
  <% end %>

  <div>
    <%= f.label :title, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.text_field :title, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <div>
    <%= f.label :content, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.text_area :content, rows: 10, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <div>
    <%= f.label :status, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.select :status, Post.statuses.keys.map { |s| [s.humanize, s] }, {}, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <div class="flex justify-end">
    <%= f.submit '保存', class: 'bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 cursor-pointer' %>
  </div>
<% end %>
```

---

## 共通: 管理画面の動作確認

### チェックリスト

| 機能 | 確認内容 |
|------|----------|
| 一覧 | データが表示される |
| ページネーション | ページ切り替えができる |
| 検索・フィルタ | 条件で絞り込める |
| 詳細 | データが正しく表示される |
| 作成 | 新規データを作成できる |
| 編集 | データを更新できる |
| 削除 | データを削除できる |
| バリデーション | エラーメッセージが表示される |

## 出力

- 管理画面が動作する
- 全モデルのCRUD操作が可能
- バリデーションエラーが適切に表示される
