# ステップ7: E2Eテスト実装

## 目次

- [概要](#概要)
- [テスト環境のセットアップ](#テスト環境のセットアップ)
- [Playwright + Capybaraの設定](#playwright--capybaraの設定)
- [テストファイルの構造](#テストファイルの構造)
- [基本的なテストパターン](#基本的なテストパターン)
- [Turbo対応のテスト](#turbo対応のテスト)
- [レスポンシブテスト](#レスポンシブテスト)
- [CI/CD設定](#cicd設定)

---

## 概要

Playwright + Capybaraを使用してE2Eテストを実装します。TDDアプローチで、テストを先に書いてから実装を進めます。

## テスト環境のセットアップ

### Gemfile

```ruby
group :test do
  gem 'capybara'
  gem 'capybara-playwright-driver'
  gem 'factory_bot_rails'
  gem 'database_cleaner-active_record'
end
```

### package.json

```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

### Playwrightのインストール

```bash
bundle install
yarn install
npx playwright install chromium --with-deps
```

## Playwright + Capybaraの設定

`spec/support/capybara.rb`:

```ruby
require 'capybara/rspec'
require 'capybara/playwright'

Capybara.register_driver(:playwright) do |app|
  Capybara::Playwright::Driver.new(
    app,
    browser_type: :chromium,
    headless: ENV['HEADLESS'] != 'false'
  )
end

Capybara.default_driver = :playwright
Capybara.javascript_driver = :playwright

Capybara.configure do |config|
  config.default_max_wait_time = 10
  config.server = :puma, { Silent: true }
end
```

`spec/rails_helper.rb`:

```ruby
require 'spec_helper'
ENV['RAILS_ENV'] ||= 'test'
require_relative '../config/environment'
abort("The Rails environment is running in production mode!") if Rails.env.production?
require 'rspec/rails'
require 'capybara/rspec'

# ヘルパーファイル読み込み
Dir[Rails.root.join('spec/support/**/*.rb')].sort.each { |f| require f }

RSpec.configure do |config|
  config.use_transactional_fixtures = false

  config.before(:suite) do
    DatabaseCleaner.strategy = :truncation
    DatabaseCleaner.clean_with(:truncation)
  end

  config.around(:each) do |example|
    DatabaseCleaner.cleaning do
      example.run
    end
  end

  config.include FactoryBot::Syntax::Methods
end
```

## テストファイルの構造

```
spec/
├── features/
│   └── admin/
│       ├── authentication_spec.rb    # 認証テスト
│       ├── dashboard_spec.rb         # ダッシュボード
│       ├── users_spec.rb             # ユーザー管理
│       ├── projects_spec.rb          # プロジェクト管理
│       └── reports_spec.rb           # 日報管理
├── support/
│   ├── capybara.rb                   # Capybara設定
│   ├── admin_helpers.rb              # 管理画面ヘルパー
│   └── playwright_helpers.rb         # Playwrightヘルパー
└── factories/
    ├── users.rb
    ├── projects.rb
    └── reports.rb
```

## 基本的なテストパターン

### 認証テスト

`spec/features/admin/authentication_spec.rb`:

```ruby
require 'rails_helper'

RSpec.describe '管理画面 - 認証', type: :feature do
  let!(:admin) { create(:user, :admin) }
  let!(:normal_user) { create(:user) }

  describe '未認証ユーザー' do
    it 'ログイン画面にリダイレクトされる' do
      visit admin_root_path
      expect(page).to have_current_path(admin_login_path)
    end
  end

  describe '一般ユーザー' do
    before do
      sign_in_to_admin(normal_user)
    end

    it '権限エラーが表示される' do
      expect(page).to have_content('管理者権限が必要です')
    end
  end

  describe '管理者ユーザー' do
    before do
      sign_in_to_admin(admin)
    end

    it 'ダッシュボードが表示される' do
      expect(page).to have_content('ダッシュボード')
      expect(page).to have_selector('[data-testid="admin-sidebar"]')
    end
  end

  describe 'ログアウト' do
    before do
      sign_in_to_admin(admin)
    end

    it 'ログアウトできる' do
      click_button 'ログアウト'
      expect(page).to have_current_path(admin_login_path)
    end
  end
end
```

### CRUD テスト

`spec/features/admin/users_spec.rb`:

```ruby
require 'rails_helper'

RSpec.describe '管理画面 - ユーザー管理', type: :feature do
  let!(:admin) { create(:user, :admin) }
  let!(:users) { create_list(:user, 5) }

  before do
    sign_in_to_admin(admin)
  end

  describe '一覧画面' do
    before { visit admin_users_path }

    it 'ユーザー一覧が表示される' do
      expect(page).to have_selector('[data-testid="users-table"]')
      users.each do |user|
        expect(page).to have_content(user.name)
      end
    end

    it '新規作成ボタンがある' do
      expect(page).to have_selector('[data-testid="new-user-button"]')
    end

    it '検索ができる' do
      target_user = users.first
      fill_in 'q', with: target_user.name
      click_button '検索'

      expect(page).to have_content(target_user.name)
      users[1..].each do |user|
        expect(page).not_to have_content(user.name)
      end
    end
  end

  describe '詳細画面' do
    let(:user) { users.first }
    before { visit admin_user_path(user) }

    it 'ユーザー情報が表示される' do
      expect(page).to have_selector('[data-testid="user-detail"]')
      expect(page).to have_content(user.name)
      expect(page).to have_content(user.email)
    end

    it '編集ボタンがある' do
      expect(page).to have_selector('[data-testid="edit-button"]')
    end

    it '削除ボタンがある' do
      expect(page).to have_selector('[data-testid="delete-button"]')
    end
  end

  describe '新規作成' do
    before { visit new_admin_user_path }

    it 'フォームが表示される' do
      expect(page).to have_selector('[data-testid="user-form"]')
    end

    context '正常な入力の場合' do
      it 'ユーザーが作成される' do
        fill_in 'user[name]', with: '新規ユーザー'
        fill_in 'user[email]', with: 'new@example.com'
        fill_in 'user[password]', with: 'password123'
        click_button '作成'

        expect(page).to have_content('ユーザーを作成しました')
        expect(page).to have_content('新規ユーザー')
      end
    end

    context 'バリデーションエラーの場合' do
      it 'エラーメッセージが表示される' do
        click_button '作成'

        expect(page).to have_selector('[data-testid="error-messages"]')
      end
    end
  end

  describe '編集' do
    let(:user) { users.first }
    before { visit edit_admin_user_path(user) }

    it '既存データがフォームに表示される' do
      expect(page).to have_field('user[name]', with: user.name)
      expect(page).to have_field('user[email]', with: user.email)
    end

    it '更新できる' do
      fill_in 'user[name]', with: '更新後の名前'
      click_button '更新'

      expect(page).to have_content('ユーザーを更新しました')
      expect(page).to have_content('更新後の名前')
    end
  end

  describe '削除' do
    let(:user) { users.first }
    before { visit admin_user_path(user) }

    it '削除できる' do
      accept_confirm do
        click_button '削除'
      end

      expect(page).to have_content('ユーザーを削除しました')
      expect(page).to have_current_path(admin_users_path)
      expect(page).not_to have_content(user.name)
    end
  end
end
```

## Turbo対応のテスト

### 確認ダイアログのテスト

```ruby
# spec/support/playwright_helpers.rb
module PlaywrightHelpers
  # Turbo confirmダイアログを自動承認
  def accept_confirm(&block)
    page.driver.with_playwright_page do |playwright_page|
      playwright_page.once('dialog', ->(dialog) { dialog.accept })
    end
    yield if block_given?
  end

  # Turbo confirmダイアログをキャンセル
  def dismiss_confirm(&block)
    page.driver.with_playwright_page do |playwright_page|
      playwright_page.once('dialog', ->(dialog) { dialog.dismiss })
    end
    yield if block_given?
  end
end

RSpec.configure do |config|
  config.include PlaywrightHelpers, type: :feature
end
```

### button_toのテスト

```ruby
describe '削除' do
  it '削除ボタンをクリックすると確認ダイアログが表示される' do
    visit admin_user_path(user)

    # button_toなのでclick_buttonを使用
    accept_confirm do
      click_button '削除'
    end

    expect(page).to have_content('削除しました')
  end
end
```

## レスポンシブテスト

```ruby
describe 'レスポンシブ対応', type: :feature do
  before { sign_in_to_admin(admin) }

  context 'モバイル表示' do
    before do
      page.driver.with_playwright_page do |playwright_page|
        playwright_page.viewport_size = { width: 375, height: 667 }
      end
      visit admin_users_path
    end

    it 'モバイルメニューボタンが表示される' do
      expect(page).to have_selector('[data-testid="mobile-menu-button"]')
    end

    it 'サイドバーが隠れている' do
      expect(page).not_to have_selector('[data-testid="admin-sidebar"]:visible')
    end
  end

  context 'タブレット表示' do
    before do
      page.driver.with_playwright_page do |playwright_page|
        playwright_page.viewport_size = { width: 768, height: 1024 }
      end
      visit admin_users_path
    end

    it 'コンテンツが正しく表示される' do
      expect(page).to have_selector('[data-testid="users-table"]')
    end
  end

  context 'デスクトップ表示' do
    before do
      page.driver.with_playwright_page do |playwright_page|
        playwright_page.viewport_size = { width: 1280, height: 800 }
      end
      visit admin_users_path
    end

    it 'サイドバーが表示される' do
      expect(page).to have_selector('[data-testid="admin-sidebar"]:visible')
    end
  end
end
```

## CI/CD設定

### GitHub Actions

`.github/workflows/e2e-test.yml`:

```yaml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  e2e-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.3'
          bundler-cache: true

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'yarn'

      - name: Install dependencies
        run: |
          bundle install
          yarn install

      - name: Install Playwright browsers
        run: npx playwright install chromium --with-deps

      - name: Setup database
        env:
          RAILS_ENV: test
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test
        run: |
          bin/rails db:create
          bin/rails db:schema:load

      - name: Run E2E tests
        env:
          RAILS_ENV: test
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test
          HEADLESS: true
        run: bundle exec rspec spec/features --format documentation

      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: screenshots
          path: tmp/capybara/
```

### Makefile

```makefile
.PHONY: e2e-test e2e-test-headed

e2e-test:
	@echo "Installing Playwright browsers..."
	npx playwright install chromium --with-deps
	@echo "Running E2E tests..."
	HEADLESS=true bundle exec rspec spec/features

e2e-test-headed:
	@echo "Running E2E tests (headed mode)..."
	HEADLESS=false bundle exec rspec spec/features
```

## 次のステップ

トラブルシューティングに進みます → @steps/08_troubleshooting.md
