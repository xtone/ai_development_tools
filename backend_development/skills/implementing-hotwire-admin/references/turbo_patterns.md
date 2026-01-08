# Turboパターンリファレンス

## 概要

Rails 8 + Turbo環境で管理画面を実装する際の主要なパターンをまとめたリファレンスです。

## 基本パターン

### 1. 削除アクション

```erb
<%# 推奨: button_to + turbo_confirm %>
<%= button_to '削除', admin_user_path(@user),
    method: :delete,
    class: 'btn btn-danger',
    form: { data: { turbo_confirm: '本当に削除しますか？' } },
    data: { testid: 'delete-button' } %>
```

### 2. インライン削除ボタン（テーブル内）

```erb
<%= button_to '削除', admin_user_path(user),
    method: :delete,
    class: 'text-red-600 hover:text-red-800 bg-transparent border-0 p-0 cursor-pointer',
    form: { class: 'inline', data: { turbo_confirm: "#{user.name}を削除しますか？" } },
    data: { testid: "delete-user-#{user.id}" } %>
```

### 3. カスタムPOSTアクション

```erb
<%# 公開/非公開トグル %>
<%= button_to(@article.published? ? '非公開にする' : '公開する'),
    toggle_publish_admin_article_path(@article),
    method: :post,
    class: 'btn btn-secondary',
    form: { data: { turbo_confirm: '状態を変更しますか？' } } %>
```

### 4. リンク + turbo_method（非推奨だが可能）

```erb
<%# button_toが使えない場合の代替 %>
<%= link_to '削除', admin_user_path(@user),
    data: { turbo_method: :delete, turbo_confirm: '削除しますか？' },
    class: 'text-red-600' %>
```

## Turbo Stream パターン

### 5. 削除後に行を削除

```ruby
# app/controllers/admin/users_controller.rb
def destroy
  @user.destroy
  respond_to do |format|
    format.html { redirect_to admin_users_path, notice: '削除しました' }
    format.turbo_stream { flash.now[:notice] = '削除しました' }
  end
end
```

```erb
<%# app/views/admin/users/destroy.turbo_stream.erb %>
<%= turbo_stream.remove dom_id(@user) %>
<%= turbo_stream.update 'flash-messages' do %>
  <%= render 'layouts/admin/flash' %>
<% end %>
```

### 6. 更新後に行を差し替え

```erb
<%# app/views/admin/users/update.turbo_stream.erb %>
<%= turbo_stream.replace dom_id(@user) do %>
  <%= render 'admin/users/user_row', user: @user %>
<% end %>
```

### 7. 新規作成後にテーブルに追加

```erb
<%# app/views/admin/users/create.turbo_stream.erb %>
<%= turbo_stream.prepend 'users-list' do %>
  <%= render 'admin/users/user_row', user: @user %>
<% end %>
<%= turbo_stream.update 'flash-messages' do %>
  <%= render 'layouts/admin/flash' %>
<% end %>
```

## Turbo Frame パターン

### 8. 検索結果の部分更新

```erb
<%# app/views/admin/users/index.html.erb %>
<%= form_with url: admin_users_path, method: :get, data: { turbo_frame: 'users-table' } do |f| %>
  <%= f.text_field :q, placeholder: '検索...' %>
  <%= f.submit '検索' %>
<% end %>

<%= turbo_frame_tag 'users-table' do %>
  <table>
    <%# テーブル内容 %>
  </table>
  <%== pagy_nav(@pagy) %>
<% end %>
```

### 9. モーダル内フォーム

```erb
<%# 一覧画面 %>
<%= turbo_frame_tag 'modal' %>

<%= link_to '新規作成', new_admin_user_path, data: { turbo_frame: 'modal' } %>

<%# new.html.erb %>
<%= turbo_frame_tag 'modal' do %>
  <div class="modal">
    <%= render 'form', user: @user %>
  </div>
<% end %>
```

## フラッシュメッセージ

### 10. Turbo対応フラッシュ

```erb
<%# app/views/layouts/admin.html.erb %>
<%= turbo_frame_tag 'flash-messages' do %>
  <%= render 'layouts/admin/flash' %>
<% end %>
```

```ruby
# コントローラ
respond_to do |format|
  format.html { redirect_to path, notice: 'メッセージ' }
  format.turbo_stream { flash.now[:notice] = 'メッセージ' }
end
```

## data属性一覧

| 属性 | 用途 | 例 |
|------|------|-----|
| `data-turbo-method` | HTTPメソッド指定 | `data: { turbo_method: :delete }` |
| `data-turbo-confirm` | 確認ダイアログ | `data: { turbo_confirm: '確認' }` |
| `data-turbo-frame` | Turbo Frame指定 | `data: { turbo_frame: 'modal' }` |
| `data-turbo-stream` | Turbo Stream有効化 | `data: { turbo_stream: true }` |
| `data-turbo-permanent` | 永続化（Morphing） | `data: { turbo_permanent: true }` |
| `data-turbo` | Turbo無効化 | `data: { turbo: false }` |

## コントローラのレスポンス

### 基本パターン

```ruby
def create
  @user = User.new(user_params)

  if @user.save
    respond_to do |format|
      format.html { redirect_to admin_user_path(@user), notice: '作成しました' }
      format.turbo_stream { flash.now[:notice] = '作成しました' }
    end
  else
    render :new, status: :unprocessable_entity
  end
end

def update
  if @user.update(user_params)
    respond_to do |format|
      format.html { redirect_to admin_user_path(@user), notice: '更新しました' }
      format.turbo_stream { flash.now[:notice] = '更新しました' }
    end
  else
    render :edit, status: :unprocessable_entity
  end
end

def destroy
  @user.destroy

  respond_to do |format|
    format.html { redirect_to admin_users_path, notice: '削除しました' }
    format.turbo_stream { flash.now[:notice] = '削除しました' }
  end
end
```

## E2Eテストでの対応

### button_toのテスト

```ruby
# link_toではなくbutton_toを使用している場合
click_button '削除'  # click_link ではない

# 確認ダイアログの処理
accept_confirm do
  click_button '削除'
end
```

### Turbo Frame内の要素

```ruby
within_frame 'users-table' do
  expect(page).to have_content(user.name)
end
```
