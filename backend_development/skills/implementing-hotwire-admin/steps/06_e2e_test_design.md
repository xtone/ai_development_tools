# ステップ6: E2Eテスト設計

## 目次

- [概要](#概要)
- [テストケース洗い出しの方針](#テストケース洗い出しの方針)
- [カテゴリ別テストケース一覧](#カテゴリ別テストケース一覧)
- [テストカバレッジマトリックス](#テストカバレッジマトリックス)
- [テスト優先度の決定](#テスト優先度の決定)
- [テストデータの準備](#テストデータの準備)

---

## 概要

管理画面のE2Eテストを体系的に設計します。テストケースを洗い出し、優先度を付けて計画的に実装します。

## テストケース洗い出しの方針

### 1. 機能カテゴリで分類

| カテゴリ | 内容 |
|---------|------|
| 認証・認可 | ログイン、ログアウト、権限チェック |
| ナビゲーション | サイドバー遷移、パンくず |
| CRUD操作 | 作成、読取、更新、削除 |
| 検索・フィルタ | キーワード検索、条件フィルタ |
| 一括操作 | 一括削除、一括更新 |
| カスタムアクション | 公開/非公開、有効化/無効化 |

### 2. 画面単位で洗い出し

各リソースに対して：

- 一覧画面（index）の表示確認
- 詳細画面（show）の表示確認
- 新規作成画面（new）の表示確認
- 編集画面（edit）の表示確認
- 作成処理（create）の動作確認
- 更新処理（update）の動作確認
- 削除処理（destroy）の動作確認

### 3. エッジケースの考慮

- データが0件の場合
- ページネーションが必要な場合
- バリデーションエラーの場合
- 権限がない場合

## カテゴリ別テストケース一覧

### 認証・認可

```markdown
## 認証テスト
- [ ] 未認証ユーザーがアクセス → ログイン画面にリダイレクト
- [ ] 一般ユーザーがアクセス → 権限エラー表示
- [ ] 管理者ユーザーがアクセス → ダッシュボード表示
- [ ] ログアウトボタンクリック → ログイン画面に遷移
```

### ダッシュボード

```markdown
## ダッシュボードテスト
- [ ] 統計カードが表示される（ユーザー数、プロジェクト数など）
- [ ] 最近のアクティビティが表示される
- [ ] クイックリンクが機能する
```

### ユーザー管理（例）

```markdown
## ユーザー管理テスト

### 一覧画面
- [ ] ユーザー一覧が表示される
- [ ] ページネーションが機能する
- [ ] 名前で検索できる
- [ ] メールで検索できる
- [ ] 権限でフィルタできる
- [ ] 新規作成ボタンがある

### 詳細画面
- [ ] ユーザー情報が正しく表示される
- [ ] 編集ボタンがある
- [ ] 削除ボタンがある
- [ ] 一覧に戻るリンクがある

### 新規作成
- [ ] フォームが表示される
- [ ] 必須項目が入力できる
- [ ] 保存すると一覧に遷移する
- [ ] バリデーションエラーが表示される

### 編集
- [ ] 既存データがフォームに表示される
- [ ] 更新すると詳細画面に遷移する
- [ ] バリデーションエラーが表示される

### 削除
- [ ] 確認ダイアログが表示される
- [ ] 削除後は一覧に遷移する
- [ ] フラッシュメッセージが表示される
```

## テストカバレッジマトリックス

### リソース × アクション マトリックス

| リソース | index | show | new | edit | create | update | destroy |
|---------|:-----:|:----:|:---:|:----:|:------:|:------:|:-------:|
| Users | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Projects | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Reports | ✅ | ✅ | - | ✅ | - | ✅ | ✅ |
| Estimates | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bills | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| UserRoles | ✅ | ✅ | - | - | - | - | - |

### カスタムアクション マトリックス

| リソース | アクション | テスト |
|---------|-----------|:------:|
| Users | soft_delete | ✅ |
| Users | revive | ✅ |
| Users | toggle_role | ✅ |
| Projects | archive | ✅ |
| Reports | summary | ✅ |
| Reports | unsubmitted | ✅ |

## テスト優先度の決定

### P0: 必須（リリースブロッカー）

- 認証・認可
- 基本的なCRUD操作
- データ破壊を伴う操作（削除）

### P1: 重要

- 検索・フィルタリング
- ページネーション
- カスタムアクション

### P2: あれば良い

- レスポンシブ対応
- エラーハンドリング
- エッジケース

## テストデータの準備

### FactoryBot定義

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    sequence(:name) { |n| "テストユーザー#{n}" }
    sequence(:email) { |n| "user#{n}@example.com" }
    password { 'password123' }

    trait :admin do
      after(:create) do |user|
        user.roles << create(:user_role, :admin)
      end
    end

    trait :deleted do
      deleted_at { Time.current }
    end
  end
end

# spec/factories/user_roles.rb
FactoryBot.define do
  factory :user_role do
    trait :admin do
      role { 'admin' }
      name { '管理者' }
    end

    trait :member do
      role { 'member' }
      name { '一般メンバー' }
    end
  end
end
```

### テストヘルパー

```ruby
# spec/support/admin_helpers.rb
module AdminHelpers
  def sign_in_as_admin
    @admin_user = create(:user, :admin)
    visit admin_login_path
    fill_in 'メールアドレス', with: @admin_user.email
    fill_in 'パスワード', with: 'password123'
    click_button 'ログイン'
    expect(page).to have_content('ダッシュボード')
  end

  def sign_in_to_admin(user)
    visit admin_login_path
    fill_in 'メールアドレス', with: user.email
    fill_in 'パスワード', with: 'password123'
    click_button 'ログイン'
  end
end

RSpec.configure do |config|
  config.include AdminHelpers, type: :feature
end
```

### テストデータのセットアップ

```ruby
# spec/features/admin/users_spec.rb
RSpec.describe '管理画面 - ユーザー管理', type: :feature do
  let!(:admin) { create(:user, :admin) }
  let!(:users) { create_list(:user, 25) }  # ページネーション確認用

  before do
    sign_in_to_admin(admin)
  end

  describe '一覧画面' do
    before { visit admin_users_path }

    it 'ユーザー一覧が表示される' do
      expect(page).to have_selector('[data-testid="users-table"]')
      expect(page).to have_content(users.first.name)
    end

    it 'ページネーションが表示される' do
      expect(page).to have_selector('.pagy-nav')
    end
  end
end
```

## チェックリストテンプレート

新しいリソースを追加する際のチェックリスト：

```markdown
## [リソース名] E2Eテストチェックリスト

### 画面表示
- [ ] 一覧画面が表示される
- [ ] 詳細画面が表示される
- [ ] 新規作成画面が表示される
- [ ] 編集画面が表示される

### CRUD操作
- [ ] 新規作成が成功する
- [ ] 新規作成のバリデーションエラーが表示される
- [ ] 更新が成功する
- [ ] 更新のバリデーションエラーが表示される
- [ ] 削除が成功する
- [ ] 削除の確認ダイアログが表示される

### 検索・フィルタ
- [ ] キーワード検索ができる
- [ ] 条件フィルタができる
- [ ] 検索結果が正しく表示される

### ナビゲーション
- [ ] サイドバーからアクセスできる
- [ ] パンくずが正しく表示される
- [ ] 一覧↔詳細の遷移ができる
```

## 次のステップ

E2Eテスト実装に進みます → @steps/07_e2e_test_implementation.md
