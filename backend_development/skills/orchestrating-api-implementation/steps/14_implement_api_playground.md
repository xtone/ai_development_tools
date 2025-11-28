# ステップ14: API Playgroundを実装する（オプション）

## 目次

- [目的](#目的)
- [手順](#手順)
  - [14.1 rswag gemをインストールする](#141-rswag-gemをインストールする)
  - [14.2 Swagger UIを設定する](#142-swagger-uiを設定する)
  - [14.3 OpenAPIファイルを配置する](#143-openapiファイルを配置する)
  - [14.4 ルーティングを追加する](#144-ルーティングを追加する)
  - [14.5 JWT認証をSwagger UIで使用する](#145-jwt認証をswagger-uiで使用する)
  - [14.6 カスタムPlaygroundを実装する（Hotwire版）](#146-カスタムplaygroundを実装するhotwire版)
  - [14.7 動作確認](#147-動作確認)
  - [14.8 本番環境での注意事項](#148-本番環境での注意事項)
- [出力](#出力)

---

## 目的

OpenAPI定義を活用して、APIを対話的にテストできるPlayground（Swagger UI）を実装する。

## 手順

### 14.1 rswag gemをインストールする

```ruby
# Gemfile
group :development, :test do
  gem 'rswag-api'
  gem 'rswag-ui'
  gem 'rswag-specs'  # RSpecでOpenAPIスペックを生成する場合
end
```

```bash
docker compose exec web bundle install
docker compose exec web bundle exec rails g rswag:install
```

### 14.2 Swagger UIを設定する

`config/initializers/rswag_ui.rb`:

```ruby
Rswag::Ui.configure do |c|
  # OpenAPIファイルのパスを指定
  c.openapi_endpoint '/api-docs/v1/swagger.yaml', 'API V1 Docs'

  # 認証設定（JWT Bearer Token）
  c.config_object['persistAuthorization'] = true
end
```

### 14.3 OpenAPIファイルを配置する

ステップ4で作成したOpenAPI定義を配置：

```bash
mkdir -p public/api-docs/v1
cp docs/api/openapi.yaml public/api-docs/v1/swagger.yaml
```

または、動的に生成する場合は `rswag-specs` を使用：

```bash
docker compose exec web bundle exec rails g rswag:specs:install
```

### 14.4 ルーティングを追加する

`config/routes.rb`:

```ruby
Rails.application.routes.draw do
  # Swagger UI
  mount Rswag::Ui::Engine => '/api-docs'
  mount Rswag::Api::Engine => '/api-docs'

  namespace :api do
    namespace :v1 do
      # 既存のAPIルート
    end
  end
end
```

### 14.5 JWT認証をSwagger UIで使用する

OpenAPI定義にセキュリティスキームを追加（ステップ4で作成済みの場合は確認）：

```yaml
# public/api-docs/v1/swagger.yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT認証トークン。
        ログインAPIで取得したトークンを入力してください。
        形式: Bearer {token}

security:
  - bearerAuth: []
```

### 14.6 カスタムPlaygroundを実装する（Hotwire版）

より高度なカスタマイズが必要な場合、独自のPlaygroundを実装：

#### コントローラを作成

```ruby
# app/controllers/playground_controller.rb
class PlaygroundController < ApplicationController
  def index
    @openapi_spec = YAML.load_file(Rails.root.join('docs/api/openapi.yaml'))
    @endpoints = extract_endpoints(@openapi_spec)
  end

  def execute
    # APIリクエストを実行
    uri = URI.parse("http://localhost:3000#{params[:path]}")
    http = Net::HTTP.new(uri.host, uri.port)

    request = build_request(uri, params[:method], params[:body], params[:token])
    response = http.request(request)

    render json: {
      status: response.code,
      headers: response.to_hash,
      body: parse_body(response.body)
    }
  end

  private

  def extract_endpoints(spec)
    endpoints = []
    spec['paths'].each do |path, methods|
      methods.each do |method, details|
        next if method == 'parameters'
        endpoints << {
          path: path,
          method: method.upcase,
          summary: details['summary'],
          description: details['description'],
          parameters: details['parameters'] || [],
          requestBody: details['requestBody']
        }
      end
    end
    endpoints
  end

  def build_request(uri, method, body, token)
    request = case method.upcase
              when 'GET' then Net::HTTP::Get.new(uri)
              when 'POST' then Net::HTTP::Post.new(uri)
              when 'PATCH' then Net::HTTP::Patch.new(uri)
              when 'PUT' then Net::HTTP::Put.new(uri)
              when 'DELETE' then Net::HTTP::Delete.new(uri)
              end

    request['Content-Type'] = 'application/json'
    request['Authorization'] = "Bearer #{token}" if token.present?
    request.body = body if body.present? && %w[POST PATCH PUT].include?(method.upcase)

    request
  end

  def parse_body(body)
    JSON.parse(body)
  rescue JSON::ParserError
    body
  end
end
```

#### ビューを作成

`app/views/playground/index.html.erb`:

```erb
<div class="container mx-auto p-8" data-controller="playground">
  <h1 class="text-2xl font-bold mb-6">API Playground</h1>

  <!-- ログインセクション -->
  <div class="bg-white shadow rounded-lg p-6 mb-6">
    <h2 class="text-lg font-semibold mb-4">認証</h2>
    <div class="grid grid-cols-3 gap-4">
      <input type="email" data-playground-target="email" placeholder="Email"
             class="border rounded px-3 py-2" value="admin@example.com">
      <input type="password" data-playground-target="password" placeholder="Password"
             class="border rounded px-3 py-2" value="password">
      <button data-action="click->playground#login"
              class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
        ログイン
      </button>
    </div>
    <div data-playground-target="tokenDisplay" class="mt-4 text-sm text-gray-600"></div>
  </div>

  <!-- API選択 -->
  <div class="bg-white shadow rounded-lg p-6 mb-6">
    <h2 class="text-lg font-semibold mb-4">APIエンドポイント</h2>
    <select data-playground-target="endpoint" data-action="change->playground#selectEndpoint"
            class="w-full border rounded px-3 py-2">
      <option value="">-- APIを選択 --</option>
      <% @endpoints.each_with_index do |endpoint, index| %>
        <option value="<%= index %>"
                data-path="<%= endpoint[:path] %>"
                data-method="<%= endpoint[:method] %>"
                data-parameters="<%= endpoint[:parameters].to_json %>"
                data-request-body="<%= endpoint[:requestBody].to_json %>">
          [<%= endpoint[:method] %>] <%= endpoint[:path] %> - <%= endpoint[:summary] %>
        </option>
      <% end %>
    </select>
  </div>

  <!-- パラメータ入力 -->
  <div data-playground-target="paramsSection" class="bg-white shadow rounded-lg p-6 mb-6 hidden">
    <h2 class="text-lg font-semibold mb-4">パラメータ</h2>
    <div data-playground-target="paramsContainer" class="space-y-4"></div>
  </div>

  <!-- リクエストボディ -->
  <div data-playground-target="bodySection" class="bg-white shadow rounded-lg p-6 mb-6 hidden">
    <h2 class="text-lg font-semibold mb-4">リクエストボディ</h2>
    <textarea data-playground-target="requestBody" rows="10"
              class="w-full border rounded px-3 py-2 font-mono text-sm"></textarea>
  </div>

  <!-- 実行ボタン -->
  <div class="mb-6">
    <button data-action="click->playground#execute"
            class="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600">
      実行
    </button>
  </div>

  <!-- レスポンス表示 -->
  <div class="bg-white shadow rounded-lg p-6">
    <h2 class="text-lg font-semibold mb-4">レスポンス</h2>
    <div data-playground-target="statusBadge" class="mb-4"></div>
    <pre data-playground-target="response"
         class="bg-gray-100 p-4 rounded overflow-x-auto text-sm font-mono"></pre>
  </div>
</div>
```

#### Stimulus コントローラ

`app/javascript/controllers/playground_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = [
    "email", "password", "tokenDisplay", "endpoint",
    "paramsSection", "paramsContainer", "bodySection", "requestBody",
    "statusBadge", "response"
  ]

  token = null
  selectedEndpoint = null

  async login() {
    const email = this.emailTarget.value
    const password = this.passwordTarget.value

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (response.ok) {
        this.token = data.token
        this.tokenDisplayTarget.innerHTML = `
          <span class="text-green-600">✓ ログイン成功</span>
          <code class="ml-2 bg-gray-100 px-2 py-1 rounded text-xs">${this.token.substring(0, 20)}...</code>
        `
      } else {
        this.tokenDisplayTarget.innerHTML = `<span class="text-red-600">✗ ${data.error}</span>`
      }
    } catch (error) {
      this.tokenDisplayTarget.innerHTML = `<span class="text-red-600">✗ ${error.message}</span>`
    }
  }

  selectEndpoint() {
    const option = this.endpointTarget.selectedOptions[0]
    if (!option.value) {
      this.paramsSectionTarget.classList.add('hidden')
      this.bodySectionTarget.classList.add('hidden')
      return
    }

    const path = option.dataset.path
    const method = option.dataset.method
    const parameters = JSON.parse(option.dataset.parameters || '[]')
    const requestBody = JSON.parse(option.dataset.requestBody || 'null')

    this.selectedEndpoint = { path, method, parameters, requestBody }

    // パラメータフォームを生成
    if (parameters.length > 0) {
      this.paramsContainerTarget.innerHTML = parameters.map(param => `
        <div>
          <label class="block text-sm font-medium text-gray-700">
            ${param.name} ${param.required ? '<span class="text-red-500">*</span>' : ''}
            <span class="text-gray-400">(${param.in})</span>
          </label>
          <input type="text" name="${param.name}" data-in="${param.in}"
                 placeholder="${param.schema?.type || 'string'}"
                 class="mt-1 w-full border rounded px-3 py-2">
          ${param.description ? `<p class="text-xs text-gray-500 mt-1">${param.description}</p>` : ''}
        </div>
      `).join('')
      this.paramsSectionTarget.classList.remove('hidden')
    } else {
      this.paramsSectionTarget.classList.add('hidden')
    }

    // リクエストボディ
    if (requestBody && ['POST', 'PATCH', 'PUT'].includes(method)) {
      const schema = requestBody.content?.['application/json']?.schema
      if (schema) {
        const example = this.generateExample(schema)
        this.requestBodyTarget.value = JSON.stringify(example, null, 2)
      }
      this.bodySectionTarget.classList.remove('hidden')
    } else {
      this.bodySectionTarget.classList.add('hidden')
    }
  }

  generateExample(schema) {
    if (schema.example) return schema.example
    if (schema.properties) {
      const obj = {}
      for (const [key, prop] of Object.entries(schema.properties)) {
        obj[key] = prop.example || this.getDefaultValue(prop.type)
      }
      return obj
    }
    return {}
  }

  getDefaultValue(type) {
    switch (type) {
      case 'string': return ''
      case 'integer': return 0
      case 'number': return 0.0
      case 'boolean': return false
      case 'array': return []
      default: return null
    }
  }

  async execute() {
    if (!this.selectedEndpoint) {
      alert('APIを選択してください')
      return
    }

    let { path, method } = this.selectedEndpoint

    // パスパラメータを置換
    const inputs = this.paramsContainerTarget.querySelectorAll('input')
    inputs.forEach(input => {
      if (input.dataset.in === 'path') {
        path = path.replace(`{${input.name}}`, input.value)
      }
    })

    // クエリパラメータを追加
    const queryParams = []
    inputs.forEach(input => {
      if (input.dataset.in === 'query' && input.value) {
        queryParams.push(`${input.name}=${encodeURIComponent(input.value)}`)
      }
    })
    if (queryParams.length > 0) {
      path += '?' + queryParams.join('&')
    }

    const headers = { 'Content-Type': 'application/json' }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const options = { method, headers }
    if (['POST', 'PATCH', 'PUT'].includes(method) && this.requestBodyTarget.value) {
      options.body = this.requestBodyTarget.value
    }

    try {
      const response = await fetch(path, options)
      const data = await response.json()

      this.statusBadgeTarget.innerHTML = `
        <span class="px-3 py-1 rounded text-white ${response.ok ? 'bg-green-500' : 'bg-red-500'}">
          ${response.status} ${response.statusText}
        </span>
      `
      this.responseTarget.textContent = JSON.stringify(data, null, 2)
    } catch (error) {
      this.statusBadgeTarget.innerHTML = `
        <span class="px-3 py-1 rounded text-white bg-red-500">Error</span>
      `
      this.responseTarget.textContent = error.message
    }
  }
}
```

#### ルーティングを追加

```ruby
# config/routes.rb
Rails.application.routes.draw do
  # API Playground
  get '/playground', to: 'playground#index'
  post '/playground/execute', to: 'playground#execute'

  # ...
end
```

### 14.7 動作確認

```bash
# サーバーを起動
docker compose up -d

# Swagger UIにアクセス
open http://localhost:3000/api-docs

# カスタムPlaygroundにアクセス
open http://localhost:3000/playground
```

### 14.8 本番環境での注意事項

```ruby
# config/environments/production.rb

# Playgroundは開発環境のみで有効化
if Rails.env.development?
  config.middleware.use Rswag::Ui::Middleware
end

# または、特定のIPからのみアクセス可能に
# app/controllers/playground_controller.rb
before_action :restrict_access

def restrict_access
  unless Rails.env.development? || request.remote_ip == '127.0.0.1'
    head :forbidden
  end
end
```

## 出力

- Swagger UI（`/api-docs`）でAPIを対話的にテストできる
- JWT認証が統合され、認証が必要なエンドポイントもテスト可能
- OpenAPI定義と実装が一致していることを確認できる
