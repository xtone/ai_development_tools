# ステップ4: Turbo対応アクション

## 目次

- [概要](#概要)
- [削除アクションの実装](#削除アクションの実装)
- [カスタムアクション](#カスタムアクション)
- [Turbo Stream応答](#turbo-stream応答)
- [フラッシュメッセージの更新](#フラッシュメッセージの更新)
- [よくある間違いと対処法](#よくある間違いと対処法)

---

## 概要

Rails 8 + Turbo環境では、従来の`link_to`の`method:`オプションが機能しません。この章では、Turbo対応の正しいアクション実装方法を解説します。

## 削除アクションの実装

### 重要: link_to の method: は使用しない

```erb
<%# NG: Rails 8 Turbo環境では動作しない %>
<%= link_to '削除', admin_user_path(@user), method: :delete, data: { confirm: '削除しますか？' } %>

<%# OK: button_to を使用 %>
<%= button_to '削除', admin_user_path(@user),
    method: :delete,
    class: 'text-red-600 hover:text-red-800',
    form: { data: { turbo_confirm: '削除しますか？' } },
    data: { testid: 'delete-button' } %>
```

### ボタンのスタイリング

`button_to`はデフォルトでフォーム要素を生成するため、リンクのようにインラインで表示するにはスタイリングが必要です：

```erb
<%# 一覧画面のアクションボタン（インライン表示） %>
<%= button_to '削除', admin_user_path(user),
    method: :delete,
    class: 'text-red-600 hover:text-red-800 bg-transparent border-0 p-0 cursor-pointer',
    form: { class: 'inline', data: { turbo_confirm: "#{user.name}を削除しますか？" } },
    data: { testid: "delete-user-#{user.id}" } %>

<%# 詳細画面のボタン %>
<%= button_to '削除', admin_user_path(@user),
    method: :delete,
    class: 'px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700',
    form: { data: { turbo_confirm: '本当に削除しますか？' } },
    data: { testid: 'delete-button' } %>
```

### コントローラの実装

```ruby
# app/controllers/admin/users_controller.rb
class Admin::UsersController < Admin::BaseController
  def destroy
    @user = User.find(params[:id])
    @user.destroy

    respond_to do |format|
      format.html { redirect_to admin_users_path, notice: 'ユーザーを削除しました' }
      format.turbo_stream {
        flash.now[:notice] = 'ユーザーを削除しました'
      }
    end
  end
end
```

## カスタムアクション

### 論理削除と復活

```ruby
# config/routes.rb
namespace :admin do
  resources :users do
    member do
      post :soft_delete
      post :revive
      post :toggle_role
    end
  end
end
```

```ruby
# app/controllers/admin/users_controller.rb
class Admin::UsersController < Admin::BaseController
  # POST /admin/users/:id/soft_delete
  def soft_delete
    @user = User.find(params[:id])
    @user.update!(deleted_at: Time.current)

    respond_to do |format|
      format.html { redirect_to admin_user_path(@user), notice: 'ユーザーを削除しました' }
      format.turbo_stream {
        flash.now[:notice] = 'ユーザーを削除しました'
      }
    end
  end

  # POST /admin/users/:id/revive
  def revive
    @user = User.find(params[:id])
    @user.update!(deleted_at: nil)

    respond_to do |format|
      format.html { redirect_to admin_user_path(@user), notice: 'ユーザーを復活しました' }
      format.turbo_stream {
        flash.now[:notice] = 'ユーザーを復活しました'
      }
    end
  end

  # POST /admin/users/:id/toggle_role
  def toggle_role
    @user = User.find(params[:id])
    role = UserRole.find(params[:role_id])

    if @user.roles.include?(role)
      @user.roles.delete(role)
      message = "#{role.name}権限を削除しました"
    else
      @user.roles << role
      message = "#{role.name}権限を付与しました"
    end

    respond_to do |format|
      format.html { redirect_to admin_user_path(@user), notice: message }
      format.turbo_stream {
        flash.now[:notice] = message
      }
    end
  end
end
```

### ビューでのカスタムアクションボタン

```erb
<%# app/views/admin/users/show.html.erb %>
<div class="flex items-center space-x-3">
  <% if @user.deleted? %>
    <%= button_to '復活させる', revive_admin_user_path(@user),
        method: :post,
        class: 'px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700',
        form: { data: { turbo_confirm: 'ユーザーを復活させますか？' } },
        data: { testid: 'revive-button' } %>
  <% else %>
    <%= button_to '無効化', soft_delete_admin_user_path(@user),
        method: :post,
        class: 'px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700',
        form: { data: { turbo_confirm: 'ユーザーを無効化しますか？' } },
        data: { testid: 'soft-delete-button' } %>
  <% end %>

  <%= link_to '編集', edit_admin_user_path(@user),
      class: 'px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700',
      data: { testid: 'edit-button' } %>

  <%= button_to '完全削除', admin_user_path(@user),
      method: :delete,
      class: 'px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700',
      form: { data: { turbo_confirm: '本当に削除しますか？この操作は取り消せません。' } },
      data: { testid: 'delete-button' } %>
</div>
```

## Turbo Stream応答

### 削除後にテーブルから行を削除

`app/views/admin/users/destroy.turbo_stream.erb`:

```erb
<%= turbo_stream.remove "user-row-#{@user.id}" %>
<%= turbo_stream.update "flash-messages" do %>
  <%= render 'layouts/admin/flash' %>
<% end %>
```

### 更新後に行を差し替え

`app/views/admin/users/update.turbo_stream.erb`:

```erb
<%= turbo_stream.replace "user-row-#{@user.id}" do %>
  <%= render 'admin/users/user_row', user: @user %>
<% end %>
<%= turbo_stream.update "flash-messages" do %>
  <%= render 'layouts/admin/flash' %>
<% end %>
```

## フラッシュメッセージの更新

### レイアウトにTurbo Frame追加

```erb
<%# app/views/layouts/admin.html.erb %>
<main class="flex-1 overflow-y-auto p-6">
  <%= turbo_frame_tag 'flash-messages' do %>
    <%= render 'layouts/admin/flash' %>
  <% end %>
  <%= yield %>
</main>
```

### コントローラでの設定

```ruby
def destroy
  @user.destroy

  respond_to do |format|
    format.html { redirect_to admin_users_path, notice: '削除しました' }
    format.turbo_stream {
      flash.now[:notice] = '削除しました'
      # Turbo Streamテンプレートが自動でレンダリングされる
    }
  end
end
```

## よくある間違いと対処法

### 1. data: { confirm: ... } が効かない

```erb
<%# NG %>
<%= button_to '削除', path, data: { confirm: '削除しますか？' } %>

<%# OK: turbo_confirm を使用 %>
<%= button_to '削除', path, form: { data: { turbo_confirm: '削除しますか？' } } %>
```

### 2. method: :delete が効かない

```erb
<%# NG: link_to + method %>
<%= link_to '削除', path, method: :delete %>

<%# OK: button_to を使用 %>
<%= button_to '削除', path, method: :delete %>

<%# OK: link_to + data-turbo-method %>
<%= link_to '削除', path, data: { turbo_method: :delete } %>
```

### 3. フォームの外観がおかしい

```erb
<%# button_to はデフォルトでブロック要素のフォームを生成 %>
<%# インラインにするには form: { class: 'inline' } を指定 %>
<%= button_to '削除', path,
    method: :delete,
    form: { class: 'inline', data: { turbo_confirm: '確認' } },
    class: 'text-red-600' %>
```

### 4. 確認ダイアログをスキップしたい（テスト用）

```ruby
# spec/support/turbo_helpers.rb
module TurboHelpers
  def accept_turbo_confirm
    page.driver.with_playwright_page do |playwright_page|
      playwright_page.on('dialog', ->(dialog) { dialog.accept })
    end
  end
end

RSpec.configure do |config|
  config.include TurboHelpers, type: :feature
end
```

## 次のステップ

Stimulusコントローラの実装に進みます → @steps/05_stimulus_controllers.md
