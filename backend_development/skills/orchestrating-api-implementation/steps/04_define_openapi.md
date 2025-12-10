# ステップ4: OpenAPI定義を作成する

## 目次

- [目的](#目的)
- [手順](#手順)
  - [4.1 OpenAPIドキュメントの基本構造を作成する](#41-openapiドキュメントの基本構造を作成する)
  - [4.2 認証スキームを定義する](#42-認証スキームを定義する)
  - [4.3 共通コンポーネントを定義する](#43-共通コンポーネントを定義する)
  - [4.4 モデルスキーマを定義する](#44-モデルスキーマを定義する)
  - [4.5 apiOptionsからパラメータを自動生成する](#45-apioptionsからパラメータを自動生成する)
  - [4.6 relationOptionsから展開パラメータを自動生成する](#46-relationoptionsから展開パラメータを自動生成する)
  - [4.7 エンドポイントを定義する](#47-エンドポイントを定義する)
  - [4.8 アクセス制御をOpenAPIに反映する](#48-アクセス制御をopenapiに反映する)
  - [4.9 ユースケースとエンドポイントの対応表を作成する](#49-ユースケースとエンドポイントの対応表を作成する)
  - [4.10 OpenAPIファイルを出力する](#410-openapiファイルを出力する)
- [出力](#出力)
- [検証](#検証)
- [次のステップ](#次のステップ)

---

## 目的

ユースケースとモデル定義に基づいて、APIの仕様をOpenAPI 3.1形式で定義する。
`apiOptions`と`relationOptions`から自動導出できる情報を活用し、一貫性のあるAPI仕様を生成する。

## 手順

### 4.1 OpenAPIドキュメントの基本構造を作成する

```yaml
openapi: 3.1.0
info:
  title: {projectName} API
  version: {version}
  description: |
    {projectName}のREST API仕様
servers:
  - url: http://localhost:3000/api/v1
    description: 開発環境
  - url: https://api.example.com/v1
    description: 本番環境
```

### 4.2 認証スキームを定義する

JSON仕様の `authConfig` に基づいて認証方式を定義：

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT認証トークン

security:
  - bearerAuth: []
```

### 4.3 共通コンポーネントを定義する

#### エラーレスポンス

```yaml
components:
  schemas:
    Error:
      type: object
      properties:
        error:
          type: string
          description: エラーメッセージ
        details:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string

  responses:
    BadRequest:
      description: リクエストが不正です
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Unauthorized:
      description: 認証が必要です
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Forbidden:
      description: アクセスが拒否されました
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    NotFound:
      description: リソースが見つかりません
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    UnprocessableEntity:
      description: バリデーションエラー
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

#### ページネーション

```yaml
components:
  schemas:
    PaginationMeta:
      type: object
      properties:
        total_count:
          type: integer
          description: 総件数
        total_pages:
          type: integer
          description: 総ページ数
        current_page:
          type: integer
          description: 現在のページ
        per_page:
          type: integer
          description: 1ページあたりの件数

  parameters:
    PageParam:
      name: page
      in: query
      schema:
        type: integer
        default: 1
        minimum: 1
      description: ページ番号
    PerPageParam:
      name: per_page
      in: query
      schema:
        type: integer
        default: 20
        minimum: 1
        maximum: 100
      description: 1ページあたりの件数
```

### 4.4 モデルスキーマを定義する

JSON仕様の各モデルをOpenAPIスキーマに変換する。

#### 型マッピング

| JSON仕様の型 | OpenAPI型 | format |
|-------------|----------|--------|
| `string` | `string` | - |
| `text` | `string` | - |
| `richText` | `string` | html |
| `number` | `number` | double |
| `integer` | `integer` | int64 |
| `boolean` | `boolean` | - |
| `date` | `string` | date-time |
| `uuid` | `string` | uuid |
| `image` | `string` | uri |
| `enum` | `string` | enum値を列挙 |
| `relation` | `object` または `string` | 関連モデルの$refまたはID |
| `custom` | `object` | カスタム型の$ref |
| `role` | `string` | rolesの値を列挙 |

#### スキーマ例

```yaml
components:
  schemas:
    Product:
      type: object
      required:
        - id
        - name
        - price
      properties:
        id:
          type: string
          format: uuid
          description: 商品ID
          readOnly: true
        name:
          type: string
          minLength: 1
          maxLength: 255
          description: 商品名
        description:
          type: string
          format: html
          description: 商品説明（リッチテキスト）
        price:
          type: integer
          format: int64
          minimum: 0
          description: 価格
        status:
          type: string
          enum: [draft, published, archived]
          description: 公開状態
        category:
          $ref: '#/components/schemas/Category'
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true

    ProductInput:
      type: object
      required:
        - name
        - price
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
        description:
          type: string
        price:
          type: integer
          minimum: 0
        status:
          type: string
          enum: [draft, published, archived]
        category_id:
          type: string
          format: uuid
```

### 4.5 apiOptionsからパラメータを自動生成する

JSON仕様の`apiOptions`に基づいて、クエリパラメータを自動生成する。

#### フィルタパラメータの自動生成

`apiOptions.filterable: true` のフィールドに対してフィルタパラメータを生成：

```yaml
# 各モデルに対して、filterable: true のフィールドからパラメータを生成
components:
  parameters:
    # enum型のフィルタ
    ProductStatusFilter:
      name: status
      in: query
      schema:
        type: string
        enum: [draft, published, archived]
      description: ステータスでフィルタ（filterable: true から自動生成）

    # relation型のフィルタ
    ProductCategoryIdFilter:
      name: category_id
      in: query
      schema:
        type: string
        format: uuid
      description: カテゴリIDでフィルタ（filterable: true から自動生成）

    # date型のフィルタ（範囲指定）
    ProductCreatedAtFromFilter:
      name: created_at_from
      in: query
      schema:
        type: string
        format: date-time
      description: 作成日時（開始）でフィルタ（filterable: true から自動生成）
    ProductCreatedAtToFilter:
      name: created_at_to
      in: query
      schema:
        type: string
        format: date-time
      description: 作成日時（終了）でフィルタ（filterable: true から自動生成）

    # integer/number型のフィルタ（範囲指定）
    ProductPriceMinFilter:
      name: price_min
      in: query
      schema:
        type: integer
      description: 価格（最小）でフィルタ（filterable: true から自動生成）
    ProductPriceMaxFilter:
      name: price_max
      in: query
      schema:
        type: integer
      description: 価格（最大）でフィルタ（filterable: true から自動生成）
```

#### ソートパラメータの自動生成

`apiOptions.sortable: true` のフィールドからソートオプションを生成：

```yaml
components:
  parameters:
    ProductSortParam:
      name: sort
      in: query
      schema:
        type: string
        # sortable: true のフィールドをenumに列挙
        enum: [created_at, updated_at, name, price, stock]
        default: created_at
      description: ソート項目（sortable: true のフィールドから自動生成）

    SortOrderParam:
      name: order
      in: query
      schema:
        type: string
        enum: [asc, desc]
        default: desc
      description: ソート順
```

#### 全文検索パラメータの自動生成

`apiOptions.searchable: true` のフィールドが1つ以上ある場合、検索パラメータを追加：

```yaml
components:
  parameters:
    SearchQueryParam:
      name: q
      in: query
      schema:
        type: string
      description: |
        全文検索クエリ（searchable: true のフィールドから自動生成）
        検索対象: title, content, name, description
```

### 4.6 relationOptionsから展開パラメータを自動生成する

`relationOptions.expandable: true` のリレーションから`include`パラメータを生成。

```yaml
components:
  parameters:
    ProductIncludeParam:
      name: include
      in: query
      schema:
        type: string
      description: |
        展開するリレーション（カンマ区切り）
        利用可能な値（expandable: true から自動生成）:
        - category (デフォルト展開: true)
        - created_by (デフォルト展開: false)
      example: category,created_by
```

#### デフォルト展開の説明追加

```yaml
paths:
  /products:
    get:
      description: |
        商品の一覧をページネーション付きで取得します。

        **デフォルトで展開されるリレーション:**
        - category (relationOptions.defaultExpand: true)

        **明示的に指定が必要なリレーション:**
        - created_by (?include=created_by)
```

### 4.7 エンドポイントを定義する

ユースケースで定義した各エンドポイントをOpenAPIのpathsに変換する。

#### 一覧取得 (GET /resources)

```yaml
paths:
  /products:
    get:
      summary: 商品一覧を取得
      description: |
        商品の一覧をページネーション付きで取得します。

        **フィルタ可能なフィールド（apiOptions.filterable: true）:**
        - status, category_id, created_at, price

        **ソート可能なフィールド（apiOptions.sortable: true）:**
        - created_at, updated_at, name, price, stock

        **全文検索対象（apiOptions.searchable: true）:**
        - name, description
      operationId: listProducts
      tags:
        - Products
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PerPageParam'
        # apiOptions.filterable: true から自動生成
        - $ref: '#/components/parameters/ProductStatusFilter'
        - $ref: '#/components/parameters/ProductCategoryIdFilter'
        - $ref: '#/components/parameters/ProductPriceMinFilter'
        - $ref: '#/components/parameters/ProductPriceMaxFilter'
        # apiOptions.sortable: true から自動生成
        - $ref: '#/components/parameters/ProductSortParam'
        - $ref: '#/components/parameters/SortOrderParam'
        # apiOptions.searchable: true から自動生成
        - $ref: '#/components/parameters/SearchQueryParam'
        # relationOptions.expandable: true から自動生成
        - $ref: '#/components/parameters/ProductIncludeParam'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Product'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'
        '401':
          $ref: '#/components/responses/Unauthorized'
```

#### 単体取得 (GET /resources/:id)

```yaml
paths:
  /products/{id}:
    get:
      summary: 商品詳細を取得
      operationId: getProduct
      tags:
        - Products
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/ProductIncludeParam'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'
        '404':
          $ref: '#/components/responses/NotFound'
```

#### 作成 (POST /resources)

```yaml
    post:
      summary: 商品を作成
      operationId: createProduct
      tags:
        - Products
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProductInput'
      responses:
        '201':
          description: 作成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
```

#### 更新 (PATCH /resources/:id)

```yaml
    patch:
      summary: 商品を更新
      operationId: updateProduct
      tags:
        - Products
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProductInput'
      responses:
        '200':
          description: 更新成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
```

#### 削除 (DELETE /resources/:id)

```yaml
    delete:
      summary: 商品を削除
      operationId: deleteProduct
      tags:
        - Products
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: 削除成功
        '404':
          $ref: '#/components/responses/NotFound'
```

### 4.8 アクセス制御をOpenAPIに反映する

#### ロールベースのセキュリティ

JSON仕様の `accessControl` と `roles` に基づいて、エンドポイントごとにセキュリティ要件を設定：

```yaml
paths:
  /admin/products:
    get:
      summary: 商品一覧（管理者用）
      security:
        - bearerAuth: []
      x-roles: [admin]  # カスタム拡張で必要ロールを明示
```

#### 行レベルセキュリティの説明

```yaml
paths:
  /my/orders:
    get:
      summary: 自分の注文一覧を取得
      description: |
        現在認証されているユーザーの注文のみを取得します。
        行レベルアクセス制御により、他ユーザーの注文は参照できません。
```

### 4.9 ユースケースとエンドポイントの対応表を作成する

ユースケースの`modelInteractions`から、エンドポイントとの対応を記録する。

```yaml
# OpenAPIのx-拡張を使用してユースケースとの対応を記録
paths:
  /products:
    get:
      x-use-cases:
        - id: uc-1
          name: Browse Products
          interaction: "商品一覧を閲覧し、在庫を確認する"
      x-actors:
        - actor-1  # Customer
        - actor-2  # Admin

  /orders:
    post:
      x-use-cases:
        - id: uc-1
          name: Purchase Product
          interaction: "注文レコードを作成し、カート内の商品を注文明細として登録する"
      x-actors:
        - actor-1  # Customer
      x-preconditions:
        - "顧客がログイン済みであること"
        - "カートに1つ以上の商品が入っていること"
      x-postconditions:
        - "注文レコードが作成される"
        - "在庫数が減少する"
```

### 4.10 OpenAPIファイルを出力する

以下の構成でファイルを出力：

```
docs/
└── api/
    ├── openapi.yaml          # メインファイル
    └── schemas/
        ├── common.yaml       # 共通スキーマ
        ├── products.yaml     # 商品関連
        ├── orders.yaml       # 注文関連
        └── users.yaml        # ユーザー関連
```

#### ファイル分割の例

```yaml
# openapi.yaml
openapi: 3.1.0
info:
  title: E-commerce API
  version: 1.0.0

paths:
  /products:
    $ref: './paths/products.yaml#/products'
  /products/{id}:
    $ref: './paths/products.yaml#/products~1{id}'

components:
  schemas:
    Product:
      $ref: './schemas/products.yaml#/Product'
    ProductInput:
      $ref: './schemas/products.yaml#/ProductInput'
```

## 出力

- `docs/api/openapi.yaml` - OpenAPI 3.1定義ファイル
- 分割されたスキーマファイル（必要に応じて）

### 自動生成されたパラメータの記録

```markdown
## 自動生成パラメータ一覧

### フィルタパラメータ（apiOptions.filterable: true から生成）
| モデル | フィールド | パラメータ名 | 型 |
|--------|-----------|-------------|-----|
| Product | status | status | enum |
| Product | category_id | category_id | uuid |
| Product | price | price_min, price_max | integer |
| Product | created_at | created_at_from, created_at_to | date-time |

### ソートパラメータ（apiOptions.sortable: true から生成）
| モデル | 利用可能なソートフィールド |
|--------|-------------------------|
| Product | created_at, updated_at, name, price, stock |
| Post | created_at, updated_at, title |

### 全文検索（apiOptions.searchable: true から生成）
| モデル | 検索対象フィールド |
|--------|-------------------|
| Product | name, description |
| Post | title, content |

### 展開パラメータ（relationOptions.expandable: true から生成）
| モデル | リレーション | デフォルト展開 |
|--------|-------------|---------------|
| Product | category | true |
| Product | created_by | false |
| Post | author | false |
| Post | category | true |
```

## 検証

作成したOpenAPI定義を以下のツールで検証：

```bash
# OpenAPI仕様の検証
npx @redocly/cli lint docs/api/openapi.yaml

# ドキュメント生成（確認用）
npx @redocly/cli preview-docs docs/api/openapi.yaml
```

## 次のステップ

作成したOpenAPI定義は以下のステップで活用：
- **ステップ5（DBスキーマ設計）**: スキーマ定義の参照
- **ステップ11（APIエンドポイント実装）**: エンドポイント実装のガイド
- **ステップ12（API動作確認）**: テスト仕様として使用
