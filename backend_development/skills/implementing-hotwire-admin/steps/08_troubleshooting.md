# ステップ8: トラブルシューティング

## 目次

- [概要](#概要)
- [Turbo関連の問題](#turbo関連の問題)
- [フォーム関連の問題](#フォーム関連の問題)
- [E2Eテスト関連の問題](#e2eテスト関連の問題)
- [パフォーマンス問題](#パフォーマンス問題)
- [認証関連の問題](#認証関連の問題)

---

## 概要

Hotwire管理画面とE2Eテスト実装でよく発生する問題と解決策を記載します。

## Turbo関連の問題

### 問題1: 削除リンクが機能しない

**症状**: `link_to`で`method: :delete`を指定しても、GETリクエストになる

**原因**: Rails 8 + Turbo環境では`link_to`の`method:`オプションが機能しない

**解決策**:

```erb
<%# NG %>
<%= link_to '削除', path, method: :delete %>

<%# OK: button_to を使用 %>
<%= button_to '削除', path, method: :delete %>

<%# OK: data-turbo-method を使用 %>
<%= link_to '削除', path, data: { turbo_method: :delete } %>
```

### 問題2: 確認ダイアログが表示されない

**症状**: `data: { confirm: '...' }`が機能しない

**原因**: Turboでは`data-turbo-confirm`を使用する必要がある

**解決策**:

```erb
<%# NG %>
<%= button_to '削除', path, data: { confirm: '削除しますか？' } %>

<%# OK: form オプションで指定 %>
<%= button_to '削除', path, form: { data: { turbo_confirm: '削除しますか？' } } %>
```

### 問題3: Turbo Streamが機能しない

**症状**: `respond_to`の`turbo_stream`フォーマットが呼ばれない

**原因**: Turboがロードされていない、またはレイアウトの設定問題

**解決策**:

```erb
<%# app/views/layouts/admin.html.erb %>
<head>
  <%= javascript_importmap_tags %>  <%# Turboがインポートされることを確認 %>
</head>
```

```javascript
// app/javascript/application.js
import "@hotwired/turbo-rails"
```

### 問題4: フラッシュメッセージが表示されない（Turbo Stream時）

**症状**: HTMLリクエストではフラッシュが表示されるが、Turbo Streamでは表示されない

**原因**: Turbo Streamでは`flash`ではなく`flash.now`を使用する必要がある

**解決策**:

```ruby
def destroy
  @user.destroy
  respond_to do |format|
    format.html { redirect_to admin_users_path, notice: '削除しました' }
    format.turbo_stream {
      flash.now[:notice] = '削除しました'  # flash.now を使用
    }
  end
end
```

## フォーム関連の問題

### 問題5: enumのセレクトボックスが英語表示

**症状**: enumの値が日本語ではなく英語キーで表示される

**解決策**:

```erb
<%# NG %>
<%= f.select :division, User.divisions.keys %>

<%# OK: I18n翻訳を使用 %>
<%= f.select :division, User.divisions.keys.map { |k| [I18n.t("enums.user.division.#{k}"), k] } %>
```

```yaml
# config/locales/ja.yml
ja:
  enums:
    user:
      division:
        engineer: エンジニア
        designer: デザイナー
        manager: マネージャー
```

### 問題6: チェックボックスが重複表示される

**症状**: 同じ権限のチェックボックスが複数表示される

**原因**: レコードの重複がある

**解決策**:

```erb
<%# グループ化して重複を排除 %>
<% UserRole.select("MIN(id) as id, role").group(:role).each do |role| %>
  <label>
    <%= check_box_tag 'user[role_ids][]', role.id, user.roles.pluck(:role).include?(role.role) %>
    <%= I18n.t("enums.user_role.role.#{role.role}") %>
  </label>
<% end %>
```

### 問題7: ネストされたパラメータが送信されない

**症状**: `user[role_ids][]`などの配列パラメータが空になる

**解決策**:

```ruby
# Strong Parametersで配列を許可
def user_params
  params.require(:user).permit(:name, :email, role_ids: [])
end
```

## E2Eテスト関連の問題

### 問題8: click_linkが失敗する（button_toの場合）

**症状**: `click_link '削除'`が要素を見つけられない

**原因**: `button_to`はボタンを生成するため、`click_link`ではなく`click_button`を使用する必要がある

**解決策**:

```ruby
# NG
click_link '削除'

# OK
click_button '削除'
```

### 問題9: Turbo confirmダイアログのテストが失敗

**症状**: 確認ダイアログが処理されない

**解決策**:

```ruby
# spec/support/playwright_helpers.rb
module PlaywrightHelpers
  def accept_confirm(&block)
    page.driver.with_playwright_page do |playwright_page|
      playwright_page.once('dialog', ->(dialog) { dialog.accept })
    end
    yield if block_given?
  end
end

# テストでの使用
accept_confirm do
  click_button '削除'
end
```

### 問題10: Stale Element Reference エラー

**症状**: 要素がDOMから削除された後にアクセスしようとしてエラーが発生

**解決策**:

```ruby
# 要素が削除されるまで待機
expect(page).not_to have_selector("[data-testid='user-row-#{user.id}']")

# または再取得
page.refresh
expect(page).not_to have_content(user.name)
```

### 問題11: レスポンシブテストでサイドバーが見えない

**症状**: ビューポートサイズを変更してもレイアウトが変わらない

**解決策**:

```ruby
# ビューポートサイズ変更後にページをリロード
page.driver.with_playwright_page do |playwright_page|
  playwright_page.viewport_size = { width: 375, height: 667 }
end
visit current_path  # ページをリロード
```

### 問題12: CI環境でテストが失敗する

**症状**: ローカルでは成功するがCI環境で失敗

**原因**: Playwrightブラウザがインストールされていない

**解決策**:

```yaml
# .github/workflows/e2e-test.yml
- name: Install Playwright browsers
  run: npx playwright install chromium --with-deps
```

## パフォーマンス問題

### 問題13: 一覧画面が遅い（N+1問題）

**症状**: レコード数が増えると一覧画面の表示が遅くなる

**解決策**:

```ruby
# コントローラでeager loadingを使用
def index
  @users = User.includes(:roles, :projects).order(created_at: :desc).page(params[:page])
end
```

### 問題14: 検索が遅い

**解決策**:

```ruby
# インデックスを追加
add_index :users, :name
add_index :users, :email

# または全文検索を使用
add_index :users, "to_tsvector('japanese', name || ' ' || email)", using: :gin
```

## 認証関連の問題

### 問題15: Deviseとの統合でセッションが保持されない

**症状**: ログイン後にセッションが失われる

**解決策**:

```ruby
# spec/rails_helper.rb
RSpec.configure do |config|
  config.include Warden::Test::Helpers
  config.include Devise::Test::IntegrationHelpers, type: :feature

  config.after(:each) do
    Warden.test_reset!
  end
end
```

### 問題16: 自作認証でパスワードが正しく検証されない

**症状**: 正しいパスワードでログインできない

**原因**: パスワードのハッシュ化にIDが必要な場合、作成時に問題が発生

**解決策**:

```ruby
# app/models/user.rb
before_create :set_temporary_password_hash
after_create :reencrypt_password_with_correct_salt

private

def set_temporary_password_hash
  return unless password.present?
  @password_for_reencryption = password
  self.encrypted_password = 'temporary'
end

def reencrypt_password_with_correct_salt
  return unless @password_for_reencryption.present?
  update_column(:encrypted_password, encrypt_password(@password_for_reencryption))
end
```

## デバッグのヒント

### Playwrightでスクリーンショットを撮る

```ruby
page.driver.with_playwright_page do |playwright_page|
  playwright_page.screenshot(path: "tmp/debug_#{Time.current.to_i}.png")
end
```

### ヘッドレスモードを無効化してブラウザを表示

```bash
HEADLESS=false bundle exec rspec spec/features/admin/users_spec.rb
```

### Turbo StreamのHTMLを確認

```ruby
# コントローラでデバッグ
def destroy
  @user.destroy
  respond_to do |format|
    format.turbo_stream do
      Rails.logger.debug render_to_string
    end
  end
end
```
