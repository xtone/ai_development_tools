# ステップ3: CRUD画面の実装

## 目次

- [概要](#概要)
- [一覧画面](#一覧画面)
- [詳細画面](#詳細画面)
- [新規作成・編集画面](#新規作成編集画面)
- [フォームヘルパー](#フォームヘルパー)
- [ページネーション](#ページネーション)
- [検索・フィルタリング](#検索フィルタリング)

---

## 概要

一覧・詳細・新規作成・編集の各CRUD画面を実装します。data-testid属性を付与してE2Eテストに対応します。

## 一覧画面

`app/views/admin/users/index.html.erb`:

```erb
<% content_for :page_title, 'ユーザー管理' %>

<div class="bg-white shadow rounded-lg" data-testid="users-list">
  <!-- ヘッダー -->
  <div class="px-6 py-4 border-b flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <h2 class="text-xl font-semibold text-gray-800">ユーザー一覧</h2>
    <%= link_to '新規作成', new_admin_user_path,
        class: 'inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors',
        data: { testid: 'new-user-button' } %>
  </div>

  <!-- 検索・フィルタ -->
  <div class="px-6 py-4 border-b bg-gray-50">
    <%= form_with url: admin_users_path, method: :get, class: 'flex flex-wrap gap-4', data: { turbo_frame: 'users-table' } do |f| %>
      <div class="flex-1 min-w-[200px]">
        <%= f.text_field :q, value: params[:q], placeholder: '名前・メールで検索',
            class: 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            data: { testid: 'search-input' } %>
      </div>
      <div>
        <%= f.select :role, [['すべて', ''], ['管理者', 'admin'], ['一般', 'user']],
            { selected: params[:role] },
            class: 'rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            data: { testid: 'role-filter' } %>
      </div>
      <%= f.submit '検索', class: 'px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 cursor-pointer',
          data: { testid: 'search-button' } %>
    <% end %>
  </div>

  <!-- テーブル -->
  <%= turbo_frame_tag 'users-table' do %>
    <div class="overflow-x-auto">
      <table class="w-full" data-testid="users-table">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">名前</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">メール</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">権限</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">作成日</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <% @users.each do |user| %>
            <tr data-testid="user-row-<%= user.id %>">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500"><%= user.id %></td>
              <td class="px-6 py-4 whitespace-nowrap">
                <%= link_to user.name, admin_user_path(user),
                    class: 'text-blue-600 hover:text-blue-800',
                    data: { testid: "user-name-#{user.id}" } %>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500"><%= user.email %></td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs rounded-full <%= user.admin? ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800' %>">
                  <%= user.admin? ? '管理者' : '一般' %>
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <%= l user.created_at, format: :short %>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm">
                <%= link_to '編集', edit_admin_user_path(user),
                    class: 'text-blue-600 hover:text-blue-800 mr-3',
                    data: { testid: "edit-user-#{user.id}" } %>
                <%= button_to '削除', admin_user_path(user),
                    method: :delete,
                    class: 'text-red-600 hover:text-red-800',
                    form: { data: { turbo_confirm: "#{user.name}を削除しますか？" } },
                    data: { testid: "delete-user-#{user.id}" } %>
              </td>
            </tr>
          <% end %>
        </tbody>
      </table>
    </div>

    <!-- ページネーション -->
    <div class="px-6 py-4 border-t">
      <%== pagy_nav(@pagy) if @pagy.pages > 1 %>
    </div>
  <% end %>
</div>
```

## 詳細画面

`app/views/admin/users/show.html.erb`:

```erb
<% content_for :page_title, @user.name %>

<div class="max-w-4xl" data-testid="user-detail">
  <!-- ヘッダー -->
  <div class="bg-white shadow rounded-lg mb-6">
    <div class="px-6 py-4 border-b flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-800"><%= @user.name %></h2>
      <div class="flex items-center space-x-3">
        <%= link_to '編集', edit_admin_user_path(@user),
            class: 'px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700',
            data: { testid: 'edit-button' } %>
        <%= button_to '削除', admin_user_path(@user),
            method: :delete,
            class: 'px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700',
            form: { data: { turbo_confirm: '本当に削除しますか？' } },
            data: { testid: 'delete-button' } %>
      </div>
    </div>

    <!-- 詳細情報 -->
    <dl class="divide-y divide-gray-200">
      <div class="px-6 py-4 grid grid-cols-3 gap-4">
        <dt class="text-sm font-medium text-gray-500">ID</dt>
        <dd class="text-sm text-gray-900 col-span-2" data-testid="user-id"><%= @user.id %></dd>
      </div>
      <div class="px-6 py-4 grid grid-cols-3 gap-4">
        <dt class="text-sm font-medium text-gray-500">名前</dt>
        <dd class="text-sm text-gray-900 col-span-2" data-testid="user-name"><%= @user.name %></dd>
      </div>
      <div class="px-6 py-4 grid grid-cols-3 gap-4">
        <dt class="text-sm font-medium text-gray-500">メールアドレス</dt>
        <dd class="text-sm text-gray-900 col-span-2" data-testid="user-email"><%= @user.email %></dd>
      </div>
      <div class="px-6 py-4 grid grid-cols-3 gap-4">
        <dt class="text-sm font-medium text-gray-500">権限</dt>
        <dd class="text-sm text-gray-900 col-span-2">
          <span class="px-2 py-1 text-xs rounded-full <%= @user.admin? ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800' %>"
                data-testid="user-role">
            <%= @user.admin? ? '管理者' : '一般' %>
          </span>
        </dd>
      </div>
      <div class="px-6 py-4 grid grid-cols-3 gap-4">
        <dt class="text-sm font-medium text-gray-500">作成日時</dt>
        <dd class="text-sm text-gray-900 col-span-2"><%= l @user.created_at, format: :long %></dd>
      </div>
      <div class="px-6 py-4 grid grid-cols-3 gap-4">
        <dt class="text-sm font-medium text-gray-500">更新日時</dt>
        <dd class="text-sm text-gray-900 col-span-2"><%= l @user.updated_at, format: :long %></dd>
      </div>
    </dl>
  </div>

  <!-- 戻るリンク -->
  <div>
    <%= link_to '← 一覧に戻る', admin_users_path,
        class: 'text-gray-600 hover:text-gray-800',
        data: { testid: 'back-to-list' } %>
  </div>
</div>
```

## 新規作成・編集画面

`app/views/admin/users/new.html.erb`:

```erb
<% content_for :page_title, 'ユーザー新規作成' %>

<div class="max-w-2xl">
  <div class="bg-white shadow rounded-lg">
    <div class="px-6 py-4 border-b">
      <h2 class="text-xl font-semibold text-gray-800">ユーザー新規作成</h2>
    </div>
    <div class="p-6">
      <%= render 'form', user: @user %>
    </div>
  </div>
</div>
```

`app/views/admin/users/edit.html.erb`:

```erb
<% content_for :page_title, "#{@user.name}の編集" %>

<div class="max-w-2xl">
  <div class="bg-white shadow rounded-lg">
    <div class="px-6 py-4 border-b">
      <h2 class="text-xl font-semibold text-gray-800">ユーザー編集</h2>
    </div>
    <div class="p-6">
      <%= render 'form', user: @user %>
    </div>
  </div>
</div>
```

`app/views/admin/users/_form.html.erb`:

```erb
<%= form_with model: [:admin, user], class: 'space-y-6', data: { testid: 'user-form' } do |f| %>
  <% if user.errors.any? %>
    <div class="bg-red-50 border border-red-200 rounded-md p-4" data-testid="error-messages">
      <h3 class="text-sm font-medium text-red-800">
        <%= pluralize(user.errors.count, 'エラー') %>があります
      </h3>
      <ul class="mt-2 list-disc list-inside text-sm text-red-700">
        <% user.errors.full_messages.each do |message| %>
          <li><%= message %></li>
        <% end %>
      </ul>
    </div>
  <% end %>

  <!-- 名前 -->
  <div>
    <%= f.label :name, '名前', class: 'block text-sm font-medium text-gray-700' %>
    <%= f.text_field :name,
        class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
        data: { testid: 'input-name' } %>
  </div>

  <!-- メールアドレス -->
  <div>
    <%= f.label :email, 'メールアドレス', class: 'block text-sm font-medium text-gray-700' %>
    <%= f.email_field :email,
        class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
        data: { testid: 'input-email' } %>
  </div>

  <!-- パスワード -->
  <% if user.new_record? %>
    <div>
      <%= f.label :password, 'パスワード', class: 'block text-sm font-medium text-gray-700' %>
      <%= f.password_field :password,
          class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
          data: { testid: 'input-password' } %>
    </div>
  <% end %>

  <!-- 職種（enum） -->
  <div>
    <%= f.label :division, '職種', class: 'block text-sm font-medium text-gray-700' %>
    <%= f.select :division,
        User.divisions.keys.map { |k| [I18n.t("enums.user.division.#{k}"), k] },
        { include_blank: '選択してください' },
        class: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
        data: { testid: 'input-division' } %>
  </div>

  <!-- 権限（チェックボックス） -->
  <div>
    <span class="block text-sm font-medium text-gray-700 mb-2">権限</span>
    <div class="space-y-2">
      <% UserRole.select("MIN(id) as id, role").group(:role).each do |role| %>
        <label class="flex items-center">
          <%= check_box_tag 'user[role_ids][]', role.id,
              user.roles.pluck(:role).include?(role.role),
              class: 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
              data: { testid: "input-role-#{role.role}" } %>
          <span class="ml-2 text-sm text-gray-700">
            <%= I18n.t("enums.user_role.role.#{role.role}", default: role.role) %>
          </span>
        </label>
      <% end %>
    </div>
  </div>

  <!-- 送信ボタン -->
  <div class="flex items-center justify-between pt-4">
    <%= link_to 'キャンセル', admin_users_path,
        class: 'text-gray-600 hover:text-gray-800',
        data: { testid: 'cancel-button' } %>
    <%= f.submit user.new_record? ? '作成' : '更新',
        class: 'px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer',
        data: { testid: 'submit-button' } %>
  </div>
<% end %>
```

## フォームヘルパー

`app/helpers/admin/form_helper.rb`:

```ruby
module Admin::FormHelper
  # データ型に応じた入力フィールドを生成
  def admin_field_for(form, field_name, field_type, options = {})
    case field_type.to_sym
    when :string
      form.text_field field_name, class: admin_input_class, **options
    when :text
      form.text_area field_name, rows: options[:rows] || 5, class: admin_input_class, **options.except(:rows)
    when :integer
      form.number_field field_name, step: 1, class: admin_input_class, **options
    when :decimal, :float
      form.number_field field_name, step: 0.01, class: admin_input_class, **options
    when :boolean
      form.check_box field_name, class: 'h-4 w-4 text-blue-600 border-gray-300 rounded', **options
    when :date
      form.date_field field_name, class: admin_input_class, **options
    when :datetime
      form.datetime_local_field field_name, class: admin_input_class, **options
    when :email
      form.email_field field_name, class: admin_input_class, **options
    when :password
      form.password_field field_name, class: admin_input_class, **options
    when :enum
      enum_options = options.delete(:collection) || []
      form.select field_name, enum_options, { include_blank: '選択してください' }, class: admin_input_class
    when :belongs_to
      collection = options.delete(:collection) || []
      label_method = options.delete(:label_method) || :name
      form.collection_select field_name, collection, :id, label_method, { include_blank: '選択してください' }, class: admin_input_class
    when :file
      form.file_field field_name, class: admin_file_input_class, **options
    else
      form.text_field field_name, class: admin_input_class, **options
    end
  end

  private

  def admin_input_class
    'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
  end

  def admin_file_input_class
    'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
  end
end
```

## ページネーション

Pagyを使用したページネーション：

```ruby
# Gemfile
gem 'pagy'

# config/initializers/pagy.rb
require 'pagy/extras/overflow'
Pagy::DEFAULT[:items] = 20
Pagy::DEFAULT[:overflow] = :last_page

# app/controllers/admin/base_controller.rb
class Admin::BaseController < ApplicationController
  include Pagy::Backend
end

# app/helpers/application_helper.rb
module ApplicationHelper
  include Pagy::Frontend
end
```

## 検索・フィルタリング

```ruby
# app/controllers/admin/users_controller.rb
def index
  @users = User.all
  @users = @users.where('name LIKE ? OR email LIKE ?', "%#{params[:q]}%", "%#{params[:q]}%") if params[:q].present?
  @users = @users.where(role: params[:role]) if params[:role].present?
  @pagy, @users = pagy(@users.order(created_at: :desc))
end
```

## 次のステップ

Turbo対応アクションの実装に進みます → @steps/04_turbo_actions.md
