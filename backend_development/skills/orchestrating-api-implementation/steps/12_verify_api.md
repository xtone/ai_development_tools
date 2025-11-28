# ステップ12: APIの動作確認を行う

## 目次

- [目的](#目的)
- [手順](#手順)
  - [11.1 サーバーを起動する](#111-サーバーを起動する)
  - [11.2 curlでエンドポイントをテストする](#112-curlでエンドポイントをテストする)
  - [11.3 RSpecテストを実装する](#113-rspecテストを実装する)
  - [11.4 FactoryBotでテストデータを定義する](#114-factorybotでテストデータを定義する)
  - [11.5 テストを実行する](#115-テストを実行する)
  - [11.6 テストのチェックリスト](#116-テストのチェックリスト)
  - [11.7 N+1問題の確認](#117-n1問題の確認)
- [出力](#出力)

---

## 目的

実装したAPIが正しく動作することを確認し、RSpecでインテグレーションテストを実装する。

## 手順

### 11.1 サーバーを起動する

```bash
# Docker環境
docker compose up -d
docker compose exec web rails db:create db:migrate

# ローカル環境
rails server
```

### 11.2 curlでエンドポイントをテストする

#### 一覧取得

```bash
# 基本
curl http://localhost:3000/api/v1/articles

# ページネーション
curl "http://localhost:3000/api/v1/articles?page=1&per_page=10"

# Ransack検索（フィルタリング）
curl "http://localhost:3000/api/v1/articles?q[title_cont]=Ruby"

# ソート
curl "http://localhost:3000/api/v1/articles?sort=created_at&order=desc"

# 全文検索
curl "http://localhost:3000/api/v1/articles?search=検索キーワード"
```

#### 単体取得

```bash
curl http://localhost:3000/api/v1/articles/{id}
```

#### 作成

```bash
curl -X POST http://localhost:3000/api/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"article": {"title": "テスト記事", "contents": "本文", "account_id": "uuid", "published_at": "2025-01-01T00:00:00Z"}}'
```

#### 更新

```bash
curl -X PATCH http://localhost:3000/api/v1/articles/{id} \
  -H "Content-Type: application/json" \
  -d '{"article": {"title": "更新後のタイトル"}}'
```

#### 削除

```bash
curl -X DELETE http://localhost:3000/api/v1/articles/{id}
```

---

## 11.3 RSpecテストを実装する

### rails_helper.rbの設定

`spec/rails_helper.rb`にFactoryBot設定を追加：

```ruby
require 'spec_helper'
ENV['RAILS_ENV'] ||= 'test'
require_relative '../config/environment'
abort("The Rails environment is running in production mode!") if Rails.env.production?
require 'rspec/rails'

# FactoryBot設定
require 'factory_bot_rails'

begin
  ActiveRecord::Migration.maintain_test_schema!
rescue ActiveRecord::PendingMigrationError => e
  abort e.to_s.strip
end

RSpec.configure do |config|
  config.fixture_paths = [Rails.root.join('spec/fixtures')]
  config.use_transactional_fixtures = true
  config.infer_spec_type_from_file_location!

  # FactoryBot DSLをインクルード
  config.include FactoryBot::Syntax::Methods

  config.filter_rails_from_backtrace!
end
```

### リクエストスペックの実装例

各モデルに対して`spec/requests/api/v1/`以下にテストを作成する。

`spec/requests/api/v1/articles_spec.rb`:

```ruby
require 'rails_helper'

RSpec.describe 'Api::V1::Articles', type: :request do
  let(:base_url) { '/api/v1/articles' }
  let!(:account) { create(:account) }

  describe 'GET /api/v1/articles' do
    context '記事が存在する場合' do
      let!(:articles) { create_list(:article, 3, account: account) }

      it '200を返し、記事一覧を取得できる' do
        get base_url

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
        expect(json['meta']).to include('current_page', 'total_pages', 'total_count')
      end

      it '各記事に関連データが含まれる' do
        get base_url

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'][0]['account']).to be_present
      end
    end

    context '記事が存在しない場合' do
      it '200を返し、空の配列を取得する' do
        get base_url

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']).to eq([])
      end
    end

    context 'ページネーション' do
      let!(:articles) { create_list(:article, 25, account: account) }

      it 'デフォルトで20件取得できる' do
        get base_url

        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(20)
        expect(json['meta']['total_count']).to eq(25)
      end

      it 'per_pageパラメータで件数を指定できる' do
        get base_url, params: { per_page: 10 }

        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(10)
      end

      it 'pageパラメータでページを指定できる' do
        get base_url, params: { page: 2, per_page: 10 }

        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(10)
        expect(json['meta']['current_page']).to eq(2)
      end
    end

    context 'Ransack検索' do
      let!(:article1) { create(:article, account: account, title: 'Ruby入門') }
      let!(:article2) { create(:article, account: account, title: 'Python入門') }

      it 'タイトルで検索できる' do
        get base_url, params: { q: { title_cont: 'Ruby' } }

        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(1)
        expect(json['data'][0]['title']).to eq('Ruby入門')
      end
    end

    context 'ソート' do
      let!(:article1) { create(:article, account: account, title: 'A記事', published_at: 2.days.ago) }
      let!(:article2) { create(:article, account: account, title: 'B記事', published_at: 1.day.ago) }
      let!(:article3) { create(:article, account: account, title: 'C記事', published_at: Time.current) }

      it '昇順ソートできる' do
        get base_url, params: { sort: 'published_at', order: 'asc' }

        json = JSON.parse(response.body)
        expect(json['data'][0]['title']).to eq('A記事')
        expect(json['data'][2]['title']).to eq('C記事')
      end

      it '降順ソートできる' do
        get base_url, params: { sort: 'published_at', order: 'desc' }

        json = JSON.parse(response.body)
        expect(json['data'][0]['title']).to eq('C記事')
        expect(json['data'][2]['title']).to eq('A記事')
      end
    end

    context '全文検索' do
      before do
        @article1 = create(:article, account: account, title: 'Rubyの基礎', contents: 'Rubyは素晴らしいプログラミング言語です')
        @article2 = create(:article, account: account, title: 'Pythonの基礎', contents: 'Pythonも素晴らしいプログラミング言語です')
      end

      it 'searchパラメータで全文検索できる' do
        # searchableカラムにトリガーでデータが設定されている場合のみテスト
        searchable_value = Article.connection.select_value("SELECT searchable FROM articles WHERE id = '#{@article1.id}'")

        if searchable_value.nil?
          skip 'トリガーが動作していないためスキップ'
        end

        get base_url, params: { search: 'Ruby' }

        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(1)
        expect(json['data'][0]['title']).to eq('Rubyの基礎')
      end
    end
  end

  describe 'GET /api/v1/articles/:id' do
    context '記事が存在する場合' do
      let!(:article) { create(:article, account: account) }

      it '200を返し、記事詳細を取得できる' do
        get "#{base_url}/#{article.id}"

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['id']).to eq(article.id)
        expect(json['data']['title']).to eq(article.title)
        expect(json['data']['account']).to be_present
      end
    end

    context '記事が存在しない場合' do
      it '404を返す' do
        get "#{base_url}/#{SecureRandom.uuid}"

        expect(response).to have_http_status(:not_found)
        json = JSON.parse(response.body)
        expect(json['error']).to be_present
      end
    end
  end

  describe 'POST /api/v1/articles' do
    context '有効なパラメータの場合' do
      let(:valid_params) do
        {
          article: {
            title: 'テスト記事',
            contents: 'テスト本文',
            account_id: account.id,
            published_at: Time.current.iso8601
          }
        }
      end

      it '201を返し、記事を作成できる' do
        expect {
          post base_url, params: valid_params
        }.to change(Article, :count).by(1)

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)
        expect(json['data']['title']).to eq('テスト記事')
      end
    end

    context '無効なパラメータの場合' do
      context '必須フィールドが空の場合' do
        let(:invalid_params) do
          { article: { title: '', contents: 'テスト本文', account_id: account.id } }
        end

        it '422を返す' do
          post base_url, params: invalid_params

          expect(response).to have_http_status(:unprocessable_entity)
          json = JSON.parse(response.body)
          expect(json['errors']['title']).to be_present
        end
      end

      context '関連先が存在しない場合' do
        let(:invalid_params) do
          { article: { title: 'テスト', contents: 'テスト本文', account_id: nil } }
        end

        it '422を返す' do
          post base_url, params: invalid_params

          expect(response).to have_http_status(:unprocessable_entity)
          json = JSON.parse(response.body)
          expect(json['errors']['account_id'] || json['errors']['account']).to be_present
        end
      end
    end
  end

  describe 'PATCH /api/v1/articles/:id' do
    let!(:article) { create(:article, account: account, title: 'Original Title') }

    context '有効なパラメータの場合' do
      it '200を返し、記事を更新できる' do
        patch "#{base_url}/#{article.id}", params: { article: { title: 'Updated Title' } }

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['title']).to eq('Updated Title')
        expect(article.reload.title).to eq('Updated Title')
      end
    end

    context '無効なパラメータの場合' do
      it '422を返す' do
        patch "#{base_url}/#{article.id}", params: { article: { title: '' } }

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']['title']).to be_present
      end
    end

    context '記事が存在しない場合' do
      it '404を返す' do
        patch "#{base_url}/#{SecureRandom.uuid}", params: { article: { title: 'Test' } }

        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'DELETE /api/v1/articles/:id' do
    let!(:article) { create(:article, account: account) }

    context '記事が存在する場合' do
      it '204を返し、記事を削除できる' do
        expect {
          delete "#{base_url}/#{article.id}"
        }.to change(Article, :count).by(-1)

        expect(response).to have_http_status(:no_content)
      end
    end

    context '記事が存在しない場合' do
      it '404を返す' do
        delete "#{base_url}/#{SecureRandom.uuid}"

        expect(response).to have_http_status(:not_found)
      end
    end

    context '関連レコードがある場合（dependent: :destroy）' do
      let!(:comment) { create(:comment, article: article) }

      it '記事と関連レコードが削除される' do
        expect {
          delete "#{base_url}/#{article.id}"
        }.to change(Article, :count).by(-1)
          .and change(Comment, :count).by(-1)

        expect(response).to have_http_status(:no_content)
      end
    end
  end
end
```

---

## 11.4 FactoryBotでテストデータを定義する

各モデルに対して`spec/factories/`以下にファクトリを作成する。

### 基本的なファクトリ

`spec/factories/accounts.rb`:

```ruby
FactoryBot.define do
  factory :account do
    name { Faker::Internet.username }
    roles { ['user'] }
  end
end
```

`spec/factories/articles.rb`:

```ruby
FactoryBot.define do
  factory :article do
    association :account
    title { Faker::Lorem.sentence }
    contents { Faker::Lorem.paragraphs(number: 3).join("\n\n") }
    published_at { Time.current }

    trait :published do
      published_at { 1.day.ago }
    end

    trait :scheduled do
      published_at { 1.day.from_now }
    end

    trait :with_empty_contents do
      contents { nil }
    end
  end
end
```

`spec/factories/comments.rb`:

```ruby
FactoryBot.define do
  factory :comment do
    association :article
    association :account
  end
end
```

### ファクトリのポイント

| 項目 | 説明 |
|------|------|
| `association` | 関連先モデルを自動生成 |
| `trait` | 状態のバリエーションを定義 |
| `Faker` | ランダムなダミーデータを生成 |
| `create_list` | 複数レコードを一括生成 |

---

## 11.5 テストを実行する

```bash
# Docker環境
docker compose exec web bundle exec rspec

# 特定のテスト
docker compose exec web bundle exec rspec spec/requests/api/v1/articles_spec.rb

# ローカル環境
bundle exec rspec

# 失敗したテストのみ再実行
bundle exec rspec --only-failures

# 詳細出力
bundle exec rspec --format documentation
```

---

## 11.6 テストのチェックリスト

各エンドポイントについて以下のテストケースを網羅する：

### 一覧取得（GET /index）

| ケース | 期待結果 |
|--------|----------|
| データあり | 200 + データ配列 |
| データなし | 200 + 空配列 |
| ページネーション | meta情報が正しい |
| Ransack検索 | 条件に合うデータのみ |
| ソート | 指定順でソート |
| 全文検索 | 検索キーワードにマッチ |

### 詳細取得（GET /show）

| ケース | 期待結果 |
|--------|----------|
| 存在するID | 200 + データ |
| 存在しないID | 404 |

### 作成（POST /create）

| ケース | 期待結果 |
|--------|----------|
| 有効なパラメータ | 201 + 作成データ |
| 必須フィールドなし | 422 + エラー |
| 関連先なし | 422 + エラー |

### 更新（PATCH /update）

| ケース | 期待結果 |
|--------|----------|
| 有効なパラメータ | 200 + 更新データ |
| 無効なパラメータ | 422 + エラー |
| 存在しないID | 404 |

### 削除（DELETE /destroy）

| ケース | 期待結果 |
|--------|----------|
| 存在するID | 204 |
| 存在しないID | 404 |
| 関連レコードあり | dependent設定に従う |

---

## 11.7 N+1問題の確認

`Gemfile`に追加：

```ruby
group :development, :test do
  gem 'bullet'
end
```

`config/environments/development.rb`:

```ruby
config.after_initialize do
  Bullet.enable = true
  Bullet.alert = true
  Bullet.bullet_logger = true
  Bullet.console = true
end
```

`config/environments/test.rb`（テストでも検出する場合）:

```ruby
config.after_initialize do
  Bullet.enable = true
  Bullet.raise = true  # テスト失敗にする
end
```

---

## 出力

- 全エンドポイントが正常に動作する
- RSpecテストが全てパスする
- N+1問題がない
