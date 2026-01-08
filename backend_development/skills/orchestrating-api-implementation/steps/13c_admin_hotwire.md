# ステップ13c: Hotwireで管理画面を自作する

> **重要**: Hotwire管理画面の完全な実装ガイドは **implementing-hotwire-admin** スキルを参照してください。
>
> 詳細: @/backend_development/skills/implementing-hotwire-admin/SKILL.md
>
> このスキルには以下が含まれます：
> - セットアップからCRUD画面の実装
> - Turbo対応アクション（削除ボタン等）
> - Stimulusコントローラ
> - **E2Eテスト設計と実装（Playwright + Capybara）**
> - トラブルシューティング

---

## 目次

- [概要](#概要)
- [クイックリファレンス](#クイックリファレンス)
- [コントローラを作成する](#コントローラを作成する)
- [ルーティングを設定する](#ルーティングを設定する)
- [レイアウトを作成する](#レイアウトを作成する)
- [一覧画面を実装する](#一覧画面を実装する)
- [フォーム画面を実装する](#フォーム画面を実装する)
- [フォームヘルパー](#フォームヘルパー)
- [カスタムアクションの実装](#カスタムアクションの実装)
- [確認ダイアログ（Stimulus）](#確認ダイアログstimulus)
- [data-testid属性の追加](#data-testid属性の追加)

---

## 概要

HotwireはRails標準のフロントエンドフレームワークです。Claudeは、Turbo + Stimulusを使用して、完全にカスタマイズ可能な管理画面を構築します。

## クイックリファレンス

### Turbo対応の削除ボタン（重要）

Rails 8 + Turbo環境では、`link_to`の`method:`オプションが**機能しません**。必ず`button_to`を使用してください：

```erb
<%# NG: Turbo環境では動作しない %>
<%= link_to '削除', path, method: :delete, data: { confirm: '削除しますか？' } %>

<%# OK: button_to を使用 %>
<%= button_to '削除', path,
    method: :delete,
    class: 'text-red-600 hover:text-red-800',
    form: { data: { turbo_confirm: '削除しますか？' } },
    data: { testid: 'delete-button' } %>
```

### E2Eテストでの注意点

- `button_to`を使用した場合、テストでは`click_button`を使用（`click_link`ではない）
- Turbo確認ダイアログは`accept_confirm`ヘルパーで処理

詳細は implementing-hotwire-admin スキルを参照してください。

## コントローラを作成する

```bash
rails generate controller Admin::Posts index show new edit
```

## ルーティングを設定する

```ruby
namespace :admin do
  resources :posts
  root to: 'dashboard#index'
end
```

## レイアウトを作成する

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

## 一覧画面を実装する

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

## フォーム画面を実装する

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

  <%# string: 一行テキスト %>
  <div>
    <%= f.label :title, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.text_field :title, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <%# richText: リッチテキストエディタ（Action Text） %>
  <div>
    <%= f.label :content, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.rich_text_area :content, class: 'mt-1 block w-full' %>
  </div>

  <%# text: 複数行テキストエリア %>
  <div>
    <%= f.label :summary, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.text_area :summary, rows: 5, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <%# integer: 整数入力 %>
  <div>
    <%= f.label :view_count, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.number_field :view_count, step: 1, min: 0, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <%# number: 小数入力 %>
  <div>
    <%= f.label :price, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.number_field :price, step: 0.01, min: 0, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <%# boolean: チェックボックス %>
  <div class="flex items-center">
    <%= f.check_box :is_published, class: 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500' %>
    <%= f.label :is_published, class: 'ml-2 block text-sm text-gray-700' %>
  </div>

  <%# date: 日時入力 %>
  <div>
    <%= f.label :published_at, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.datetime_field :published_at, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <%# enum: セレクトボックス %>
  <div>
    <%= f.label :status, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.select :status, Post.statuses.keys.map { |s| [Post.human_attribute_name("status.#{s}"), s] }, { include_blank: '選択してください' }, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <%# relation: 関連モデル選択 %>
  <div>
    <%= f.label :author_id, class: 'block text-sm font-medium text-gray-700' %>
    <%= f.collection_select :author_id, User.all, :id, :name, { include_blank: '選択してください' }, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
  </div>

  <%# image: ファイルアップロード（Active Storage） %>
  <div>
    <%= f.label :featured_image, class: 'block text-sm font-medium text-gray-700' %>
    <% if post.featured_image.attached? %>
      <div class="mt-2 mb-2">
        <%= image_tag post.featured_image, height: 100, class: 'rounded' %>
      </div>
    <% end %>
    <%= f.file_field :featured_image, accept: 'image/*', class: 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100' %>
  </div>

  <%# custom: カスタム型（SEO設定）のフィールド %>
  <fieldset class="border border-gray-200 rounded-md p-4">
    <legend class="text-sm font-medium text-gray-700 px-2">SEO設定</legend>

    <div class="space-y-4">
      <div>
        <%= f.label :seo_settings_title, 'SEOタイトル', class: 'block text-sm font-medium text-gray-700' %>
        <%= f.text_field :seo_settings_title, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
      </div>

      <div>
        <%= f.label :seo_settings_description, 'SEO説明文', class: 'block text-sm font-medium text-gray-700' %>
        <%= f.text_area :seo_settings_description, rows: 3, class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500' %>
      </div>
    </div>
  </fieldset>

  <div class="flex justify-end">
    <%= f.submit '保存', class: 'bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 cursor-pointer' %>
  </div>
<% end %>
```

## フォームヘルパー

データ型に応じた入力フォームを生成するヘルパー：

`app/helpers/admin/form_helper.rb`:

```ruby
module Admin::FormHelper
  def field_input_for(form, field_name, field_type, options = {})
    case field_type.to_sym
    when :string
      form.text_field field_name, class: input_class, **options
    when :text
      form.text_area field_name, rows: options[:rows] || 5, class: input_class, **options.except(:rows)
    when :richText
      form.rich_text_area field_name, class: 'mt-1 block w-full', **options
    when :integer
      form.number_field field_name, step: 1, class: input_class, **options
    when :number
      form.number_field field_name, step: 0.01, class: input_class, **options
    when :boolean
      form.check_box field_name, class: 'h-4 w-4 text-blue-600 border-gray-300 rounded', **options
    when :date
      form.datetime_field field_name, class: input_class, **options
    when :enum
      form.select field_name, options[:collection], { include_blank: '選択してください' }, class: input_class
    when :relation
      form.collection_select field_name, options[:collection], :id, options[:label_method] || :name, { include_blank: '選択してください' }, class: input_class
    when :image
      form.file_field field_name, accept: 'image/*', class: file_input_class
    else
      form.text_field field_name, class: input_class, **options
    end
  end

  private

  def input_class
    'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
  end

  def file_input_class
    'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
  end
end
```

## カスタムアクションの実装

`app/controllers/admin/articles_controller.rb`:

```ruby
class Admin::ArticlesController < Admin::BaseController
  # POST /admin/articles/:id/publish
  def publish
    @article = Article.find(params[:id])
    @article.update!(publish_status: 'published', published_at: Time.current)

    respond_to do |format|
      format.html { redirect_to admin_article_path(@article), notice: '記事を公開しました' }
      format.turbo_stream {
        flash.now[:notice] = '記事を公開しました'
      }
    end
  end

  # POST /admin/articles/:id/unpublish
  def unpublish
    @article = Article.find(params[:id])
    @article.update!(publish_status: 'draft')

    respond_to do |format|
      format.html { redirect_to admin_article_path(@article), notice: '記事を下書きに戻しました' }
      format.turbo_stream
    end
  end
end
```

`config/routes.rb`:

```ruby
namespace :admin do
  resources :articles do
    member do
      post :publish
      post :unpublish
    end
  end
end
```

`app/views/admin/articles/show.html.erb`:

```erb
<div id="article-actions" class="flex space-x-4">
  <% if @article.publish_status != 'published' %>
    <%= button_to '公開する', publish_admin_article_path(@article),
        method: :post,
        class: 'bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700',
        data: {
          turbo_confirm: '記事を公開しますか？',
          testid: 'publish-button'
        } %>
  <% else %>
    <%= button_to '下書きに戻す', unpublish_admin_article_path(@article),
        method: :post,
        class: 'bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700',
        data: {
          turbo_confirm: '記事を下書きに戻しますか？',
          testid: 'unpublish-button'
        } %>
  <% end %>
</div>
```

## 確認ダイアログ（Stimulus）

`app/javascript/controllers/confirm_dialog_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = {
    title: String,
    message: String,
    confirmText: { type: String, default: '実行' },
    cancelText: { type: String, default: 'キャンセル' }
  }

  confirm(event) {
    event.preventDefault()

    const dialog = document.createElement('div')
    dialog.innerHTML = `
      <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
          <div class="px-6 py-4 border-b">
            <h3 class="text-lg font-medium">${this.titleValue}</h3>
          </div>
          <div class="px-6 py-4">
            <p class="text-gray-600">${this.messageValue}</p>
          </div>
          <div class="px-6 py-4 bg-gray-50 flex justify-end space-x-3">
            <button type="button" class="cancel-btn px-4 py-2 text-gray-700 hover:text-gray-900">
              ${this.cancelTextValue}
            </button>
            <button type="button" class="confirm-btn px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              ${this.confirmTextValue}
            </button>
          </div>
        </div>
      </div>
    `

    document.body.appendChild(dialog)

    dialog.querySelector('.cancel-btn').addEventListener('click', () => {
      dialog.remove()
    })

    dialog.querySelector('.confirm-btn').addEventListener('click', () => {
      dialog.remove()
      if (this.element.tagName === 'FORM') {
        this.element.submit()
      } else {
        window.location.href = this.element.href
      }
    })
  }
}
```

## data-testid属性の追加

```erb
<%# 一覧テーブル %>
<table data-testid="articles-table">
  <tbody>
    <% @articles.each do |article| %>
      <tr data-testid="article-row-<%= article.id %>">
        <td><%= article.title %></td>
        <td>
          <%= link_to '詳細', admin_article_path(article),
              data: { testid: "article-detail-#{article.id}" } %>
          <%= link_to '編集', edit_admin_article_path(article),
              data: { testid: "article-edit-#{article.id}" } %>
          <%= link_to '削除', admin_article_path(article),
              method: :delete,
              data: {
                testid: "article-delete-#{article.id}",
                turbo_confirm: '削除しますか？'
              } %>
        </td>
      </tr>
    <% end %>
  </tbody>
</table>

<%# ナビゲーション %>
<nav data-testid="admin-sidebar">
  <%= link_to 'ダッシュボード', admin_root_path, data: { testid: 'nav-dashboard' } %>
  <%= link_to '記事', admin_articles_path, data: { testid: 'nav-articles' } %>
</nav>

<%# フォーム %>
<%= form_with model: [:admin, @article], data: { testid: 'article-form' } do |f| %>
  <%= f.text_field :title, data: { testid: 'input-title' } %>
  <%= f.text_area :contents, data: { testid: 'input-contents' } %>
  <%= f.submit '保存', data: { testid: 'submit-button' } %>
<% end %>
```
