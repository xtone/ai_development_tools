# ステップ10: APIエンドポイントを実装する

## 目的

RESTful APIエンドポイントを実装し、CRUD操作、ページネーション、フィルタリング、ソートを提供する。

## 手順

### 10.1 ルーティングを定義する

`config/routes.rb`:

```ruby
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :posts
      resources :categories
      resources :users, only: [:index, :show]
    end
  end
end
```

### 10.2 コントローラを実装する

`app/controllers/api/v1/posts_controller.rb`:

```ruby
module Api
  module V1
    class PostsController < BaseController
      before_action :set_post, only: [:show, :update, :destroy]

      # GET /api/v1/posts
      def index
        posts = Post.all
        posts = apply_filters(posts)
        posts = apply_sorting(posts)
        posts = apply_includes(posts)

        # Kaminariでページネーション
        posts = posts.page(params[:page]).per(per_page)

        render json: {
          data: PostSerializer.new(posts).serialize,
          meta: pagination_meta(posts)
        }
      end

      # GET /api/v1/posts/:id
      def show
        post = apply_includes(Post.where(id: @post.id)).first

        render json: {
          data: PostSerializer.new(post).serialize
        }
      end

      # POST /api/v1/posts
      def create
        post = Post.new(post_params)

        if post.save
          render json: {
            data: PostSerializer.new(post).serialize
          }, status: :created
        else
          render json: {
            errors: format_errors(post.errors)
          }, status: :unprocessable_entity
        end
      end

      # PATCH/PUT /api/v1/posts/:id
      def update
        if @post.update(post_params)
          render json: {
            data: PostSerializer.new(@post).serialize
          }
        else
          render json: {
            errors: format_errors(@post.errors)
          }, status: :unprocessable_entity
        end
      end

      # DELETE /api/v1/posts/:id
      def destroy
        @post.destroy
        head :no_content
      end

      private

      def set_post
        @post = Post.find(params[:id])
      end

      def post_params
        params.require(:post).permit(
          :title, :content, :status, :author_id, :category_id,
          :seo_settings_title, :seo_settings_description,
          tag_ids: []
        )
      end

      def apply_filters(scope)
        scope = scope.by_status(params[:status]) if params[:status]
        scope = scope.by_author(params[:author_id]) if params[:author_id]
        scope = scope.search(params[:q]) if params[:q]
        scope
      end

      def apply_sorting(scope)
        sort_field = params[:sort] || 'created_at'
        sort_order = params[:order] || 'desc'
        scope.sorted_by(sort_field, sort_order)
      end

      def apply_includes(scope)
        includes = (params[:include] || '').split(',')
        allowed = %w[author category tags]
        includes = includes & allowed
        includes.any? ? scope.includes(*includes.map(&:to_sym)) : scope
      end

      def per_page
        [(params[:per_page] || 20).to_i, 100].min
      end

      def format_errors(errors)
        errors.map do |error|
          {
            field: error.attribute,
            message: error.full_message
          }
        end
      end
    end
  end
end
```

### 10.3 シリアライザを実装する（Alba）

`app/serializers/post_serializer.rb`:

```ruby
class PostSerializer
  include Alba::Resource

  attributes :id, :title, :content, :status, :created_at, :updated_at

  # カスタム型
  attribute :seo_settings do |post|
    {
      title: post.seo_settings_title,
      description: post.seo_settings_description
    }
  end

  # リレーション（条件付き）
  one :author, serializer: UserSerializer, if: proc { |post, params|
    params[:include]&.include?('author')
  }

  one :category, serializer: CategorySerializer, if: proc { |post, params|
    params[:include]&.include?('category')
  }

  many :tags, serializer: TagSerializer, if: proc { |post, params|
    params[:include]&.include?('tags')
  }
end
```

### 10.4 ベースコントローラの拡張

`app/controllers/api/v1/base_controller.rb`:

```ruby
module Api
  module V1
    class BaseController < ApplicationController
      # 重要: 通常モード（--apiなし）でRailsを作成した場合、
      # APIコントローラではCSRF保護を無効化する必要がある
      skip_before_action :verify_authenticity_token

      rescue_from ActiveRecord::RecordNotFound, with: :not_found
      rescue_from ActiveRecord::RecordInvalid, with: :unprocessable_entity
      rescue_from ActionController::ParameterMissing, with: :bad_request

      private

      def not_found
        render json: {
          error: {
            code: 'not_found',
            message: 'リソースが見つかりません'
          }
        }, status: :not_found
      end

      def unprocessable_entity(exception)
        render json: {
          error: {
            code: 'validation_error',
            message: 'バリデーションエラー',
            details: format_errors(exception.record.errors)
          }
        }, status: :unprocessable_entity
      end

      def bad_request(exception)
        render json: {
          error: {
            code: 'bad_request',
            message: exception.message
          }
        }, status: :bad_request
      end

      def format_errors(errors)
        errors.map do |error|
          {
            field: error.attribute,
            message: error.full_message
          }
        end
      end

      # Kaminariのページネーションメタ情報
      def pagination_meta(collection)
        {
          current_page: collection.current_page,
          per_page: collection.limit_value,
          total_pages: collection.total_pages,
          total_count: collection.total_count
        }
      end
    end
  end
end
```

### 10.5 CSRF保護について

#### なぜCSRF保護を無効化するのか

- 通常モード（`--api`オプションなし）でRailsを作成すると、CSRF保護が有効になる
- APIはステートレスでトークンベースの認証を使用するため、CSRFトークンは不要
- 無効化しないと `Can't verify CSRF token authenticity.` エラーが発生する

#### APIモードとの違い

| モード | CSRF保護 | 対応 |
|--------|---------|------|
| `--api`モード | デフォルト無効 | 不要 |
| 通常モード | デフォルト有効 | `skip_before_action :verify_authenticity_token` が必要 |

**注意**: 管理画面を含めるために通常モードで作成した場合は、APIコントローラでのみCSRF保護を無効化する。

### 10.6 Ransackを使用したフィルタリング（代替）

```ruby
def index
  q = Post.ransack(params[:q])
  posts = q.result(distinct: true)
  posts = posts.page(params[:page]).per(per_page)

  render json: {
    data: PostSerializer.new(posts).serialize,
    meta: pagination_meta(posts)
  }
end
```

### 10.7 APIレスポンス形式

#### 成功レスポンス（一覧）

```json
{
  "data": [
    { "id": "uuid", "title": "...", ... }
  ],
  "meta": {
    "current_page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_count": 100
  }
}
```

#### 成功レスポンス（単体）

```json
{
  "data": {
    "id": "uuid",
    "title": "...",
    ...
  }
}
```

#### エラーレスポンス

```json
{
  "error": {
    "code": "validation_error",
    "message": "バリデーションエラー",
    "details": [
      { "field": "title", "message": "タイトルを入力してください" }
    ]
  }
}
```

## 出力

- 全モデルのCRUDエンドポイントが実装されている
- ページネーション、フィルタリング、ソートが動作する
- エラーレスポンスが統一されている
