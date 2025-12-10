# ステップ11: APIエンドポイントを実装する

## 目次

- [目的](#目的)
- [手順](#手順)
  - [11.1 ルーティングを定義する](#111-ルーティングを定義する)
  - [11.2 コントローラを実装する](#112-コントローラを実装する)
  - [11.3 apiOptionsから許可フィールドを自動導出する](#113-apioptionsから許可フィールドを自動導出する)
  - [11.4 relationOptionsから展開設定を自動導出する](#114-relationoptionsから展開設定を自動導出する)
  - [11.5 シリアライザを実装する](#115-シリアライザを実装する)
  - [11.6 ベースコントローラの拡張](#116-ベースコントローラの拡張)
  - [11.7 CSRF保護について](#117-csrf保護について)
  - [11.8 Ransackを使用したフィルタリング（代替）](#118-ransackを使用したフィルタリング代替)
  - [11.9 APIレスポンス形式](#119-apiレスポンス形式)
- [出力](#出力)

---

## 目的

JSON仕様の`apiOptions`と`relationOptions`に基づいて、RESTful APIエンドポイントを実装し、CRUD操作、ページネーション、フィルタリング、ソート、リレーション展開を提供する。

## 手順

### 11.1 ルーティングを定義する

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

### 11.2 コントローラを実装する

`app/controllers/api/v1/posts_controller.rb`:

```ruby
module Api
  module V1
    class PostsController < BaseController
      before_action :set_post, only: [:show, :update, :destroy]

      # apiOptions.filterable: true から導出
      ALLOWED_FILTERS = %w[status category_id author_id created_at_from created_at_to].freeze

      # apiOptions.sortable: true から導出
      ALLOWED_SORTS = %w[created_at updated_at title].freeze

      # relationOptions.expandable: true から導出
      ALLOWED_INCLUDES = %w[author category tags].freeze

      # relationOptions.defaultExpand: true から導出
      DEFAULT_INCLUDES = %w[category].freeze

      # GET /api/v1/posts
      def index
        posts = Post.all
        posts = apply_filters(posts)
        posts = apply_sorting(posts)
        posts = apply_includes(posts)

        # Kaminariでページネーション
        posts = posts.page(params[:page]).per(per_page)

        render json: {
          data: PostSerializer.new(posts, params: { include: include_params }).serialize,
          meta: pagination_meta(posts)
        }
      end

      # GET /api/v1/posts/:id
      def show
        post = apply_includes(Post.where(id: @post.id)).first

        render json: {
          data: PostSerializer.new(post, params: { include: include_params }).serialize
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

      # apiOptions.filterable: true のフィールドでフィルタリング
      def apply_filters(scope)
        scope = scope.by_status(params[:status]) if params[:status].present?
        scope = scope.by_category(params[:category_id]) if params[:category_id].present?
        scope = scope.by_author(params[:author_id]) if params[:author_id].present?
        scope = scope.created_from(params[:created_at_from]) if params[:created_at_from].present?
        scope = scope.created_to(params[:created_at_to]) if params[:created_at_to].present?
        scope = scope.search(params[:q]) if params[:q].present?  # apiOptions.searchable: true
        scope
      end

      # apiOptions.sortable: true のフィールドでソート
      def apply_sorting(scope)
        sort_field = params[:sort].to_s
        sort_order = params[:order].to_s.downcase

        # ホワイトリストチェック - 不正な値はデフォルト値に戻す
        sort_field = 'created_at' unless ALLOWED_SORTS.include?(sort_field)
        sort_order = 'desc' unless %w[asc desc].include?(sort_order)

        # Arelを使用した完全に安全なソート実装
        table = scope.arel_table

        # 防御的プログラミング: カラム存在確認
        unless scope.column_names.include?(sort_field)
          sort_field = 'created_at'
        end

        column = table[sort_field.to_sym]
        order_node = sort_order == 'asc' ? column.asc : column.desc
        scope.order(order_node)
      end

      # relationOptions.expandable: true のリレーションを展開
      def apply_includes(scope)
        includes = include_params
        includes.any? ? scope.includes(*includes.map(&:to_sym)) : scope
      end

      # include パラメータの処理（defaultExpand対応）
      def include_params
        requested = (params[:include] || '').split(',').map(&:strip)

        # ALLOWED_INCLUDESに含まれるリレーションのみ許可
        requested = requested & ALLOWED_INCLUDES

        # defaultExpand: true のリレーションを追加
        (DEFAULT_INCLUDES + requested).uniq
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

### 11.3 apiOptionsから許可フィールドを自動導出する

JSON仕様の`apiOptions`に基づいて、コントローラで許可するフィルタ・ソートフィールドを定義する。

#### 導出ルール

| apiOptions設定 | 導出される定数 | 用途 |
|---------------|--------------|------|
| `filterable: true` | `ALLOWED_FILTERS` | フィルタパラメータの許可リスト |
| `sortable: true` | `ALLOWED_SORTS` | ソートフィールドの許可リスト |
| `searchable: true` | 全文検索の有効化 | `?q=` パラメータ対応 |

#### 実装例

```ruby
class PostsController < BaseController
  # apiOptions.filterable: true から導出
  # - status (enum, filterable: true)
  # - category_id (relation, filterable: true)
  # - author_id (relation, filterable: true)
  # - created_at (date, filterable: true) → created_at_from, created_at_to
  ALLOWED_FILTERS = %w[status category_id author_id created_at_from created_at_to].freeze

  # apiOptions.sortable: true から導出
  # - created_at (sortable: true)
  # - updated_at (sortable: true)
  # - title (sortable: true)
  ALLOWED_SORTS = %w[created_at updated_at title].freeze

  # 全文検索有効化 (apiOptions.searchable: true が1つ以上存在)
  SEARCH_ENABLED = true

  private

  def apply_filters(scope)
    # セキュリティ: params.sliceでホワイトリストのキーのみを取得
    # これにより、ALLOWED_FILTERSに含まれないパラメータは無視される
    params.slice(*ALLOWED_FILTERS).each do |filter, value|
      next if value.blank?

      scope = case filter
      when 'status'
        scope.by_status(value)
      when 'category_id'
        scope.by_category(value)
      when 'author_id'
        scope.by_author(value)
      when 'created_at_from'
        scope.created_from(value)
      when 'created_at_to'
        scope.created_to(value)
      else
        scope  # ホワイトリストにない場合はスキップ
      end
    end

    # searchable: true のフィールドが存在する場合のみ
    scope = scope.search(params[:q]) if SEARCH_ENABLED && params[:q].present?

    scope
  end
end
```

### 11.4 relationOptionsから展開設定を自動導出する

JSON仕様の`relationOptions`に基づいて、リレーション展開の設定を定義する。

#### 導出ルール

| relationOptions設定 | 導出される設定 | 動作 |
|-------------------|--------------|------|
| `expandable: true` | `ALLOWED_INCLUDES` | 展開可能リレーションリスト |
| `defaultExpand: true` | `DEFAULT_INCLUDES` | 常に展開するリレーション |

#### 実装例

```ruby
class PostsController < BaseController
  # relationOptions.expandable: true から導出
  # - author (expandable: true, defaultExpand: false)
  # - category (expandable: true, defaultExpand: true)
  # - tags (expandable: true, defaultExpand: false)
  ALLOWED_INCLUDES = %w[author category tags].freeze

  # relationOptions.defaultExpand: true から導出
  # - category (defaultExpand: true)
  DEFAULT_INCLUDES = %w[category].freeze

  private

  def include_params
    # リクエストで指定されたinclude
    requested = (params[:include] || '').split(',').map(&:strip)

    # expandable: true のリレーションのみ許可
    requested = requested & ALLOWED_INCLUDES

    # defaultExpand: true のリレーションを追加
    (DEFAULT_INCLUDES + requested).uniq
  end

  def apply_includes(scope)
    includes = include_params
    includes.any? ? scope.includes(*includes.map(&:to_sym)) : scope
  end
end
```

#### マッピング表

```markdown
## リレーション展開設定（JSON仕様から自動導出）

| リレーション | expandable | defaultExpand | ALLOWED_INCLUDES | DEFAULT_INCLUDES |
|-------------|------------|---------------|------------------|------------------|
| author | true | false | ✓ | - |
| category | true | true | ✓ | ✓ |
| tags | true | false | ✓ | - |
```

### 11.5 シリアライザを実装する（Alba）

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

  # リレーション（条件付き）- relationOptions.expandable: true から導出
  one :author, serializer: UserSerializer, if: proc { |post, params|
    params[:include]&.include?('author')
  }

  # defaultExpand: true のリレーションは常に展開
  one :category, serializer: CategorySerializer, if: proc { |post, params|
    params[:include]&.include?('category')
  }

  many :tags, serializer: TagSerializer, if: proc { |post, params|
    params[:include]&.include?('tags')
  }
end
```

### 11.6 ベースコントローラの拡張

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

### 11.7 CSRF保護について

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

### 11.8 Ransackを使用したフィルタリング（代替）

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

### 11.9 APIレスポンス形式

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

以下の形式でAPI実装結果をまとめる：

```markdown
## API実装結果

### コントローラ一覧

| コントローラ | エンドポイント数 | フィルタ数 | ソート数 | 展開可能リレーション |
|-------------|----------------|-----------|---------|-------------------|
| PostsController | 5 | 5 | 3 | 3 |
| UsersController | 2 | 2 | 2 | 1 |

### apiOptionsから導出した設定

#### PostsController

| 設定 | 導出元 | 値 |
|------|--------|-----|
| ALLOWED_FILTERS | apiOptions.filterable: true | status, category_id, author_id, created_at_from, created_at_to |
| ALLOWED_SORTS | apiOptions.sortable: true | created_at, updated_at, title |
| SEARCH_ENABLED | apiOptions.searchable: true | true |

### relationOptionsから導出した設定

#### PostsController

| 設定 | 導出元 | 値 |
|------|--------|-----|
| ALLOWED_INCLUDES | relationOptions.expandable: true | author, category, tags |
| DEFAULT_INCLUDES | relationOptions.defaultExpand: true | category |

### エンドポイント一覧

| メソッド | パス | フィルタパラメータ | ソートパラメータ | 展開パラメータ |
|---------|------|------------------|-----------------|---------------|
| GET | /api/v1/posts | status, category_id, author_id, q, created_at_from/to | sort, order | include |
| GET | /api/v1/posts/:id | - | - | include |
| POST | /api/v1/posts | - | - | - |
| PATCH | /api/v1/posts/:id | - | - | - |
| DELETE | /api/v1/posts/:id | - | - | - |
```

### 確認事項

- 全モデルのCRUDエンドポイントが実装されている
- apiOptionsから導出したフィルタ・ソートが動作する
- relationOptionsから導出した展開設定が動作する
- defaultExpand: trueのリレーションが自動展開される
- ページネーション、フィルタリング、ソートが動作する
- エラーレスポンスが統一されている
