# ステップ3: ユースケースを洗い出す

## 目次

- [目的](#目的)
- [手順](#手順)
  - [3.1 JSON仕様からアクターとユースケースを抽出する](#31-json仕様からアクターとユースケースを抽出する)
  - [3.2 ユースケースの詳細を確認する](#32-ユースケースの詳細を確認する)
  - [3.3 各モデルの基本CRUD操作を定義する](#33-各モデルの基本crud操作を定義する)
  - [3.4 apiOptionsからAPI設定を自動導出する](#34-apioptionsからapi設定を自動導出する)
  - [3.5 relationOptionsから展開設定を自動導出する](#35-relationoptionsから展開設定を自動導出する)
  - [3.6 アクセス制御とユースケースの関連付け](#36-アクセス制御とユースケースの関連付け)
  - [3.7 ユースケース実装計画を作成する](#37-ユースケース実装計画を作成する)
- [出力](#出力)

---

## 目的

JSON仕様で定義されたアクターとユースケースを確認し、`apiOptions`と`relationOptions`から自動導出できる情報と組み合わせて、各モデルに対するAPI操作とエンドポイントを定義する。

## 手順

### 3.1 JSON仕様からアクターとユースケースを抽出する

JSON仕様の `actors` と `useCases` プロパティを確認し、システムの利用者と提供機能を把握する。

#### アクター (Actor) の確認

```json
"actors": [
  {
    "id": "actor-1",
    "name": "Customer",
    "description": "一般顧客"
  },
  {
    "id": "actor-2",
    "name": "Admin",
    "description": "管理者"
  }
]
```

### 3.2 ユースケースの詳細を確認する

各ユースケースの詳細プロパティを確認する：

```json
{
  "id": "uc-1",
  "name": "Purchase Product",
  "description": "商品を購入する",
  "actorIds": ["actor-1"],
  "preconditions": [
    "顧客がログイン済みであること",
    "カートに1つ以上の商品が入っていること"
  ],
  "postconditions": [
    "注文レコードが作成される",
    "在庫数が減少する",
    "確認メールが送信される"
  ],
  "modelInteractions": [
    {
      "model": "Cart",
      "description": "現在のユーザーのカート情報を取得する",
      "hint": "read"
    },
    {
      "model": "Product",
      "description": "在庫数を確認し、購入可能かどうかを判定する",
      "hint": "read"
    },
    {
      "model": "Order",
      "description": "注文レコードを作成し、カート内の商品を注文明細として登録する",
      "hint": "write"
    }
  ],
  "notes": "決済処理は外部決済サービス（Stripe）を利用"
}
```

#### ユースケースプロパティの活用方法

| プロパティ | 活用方法 |
|-----------|----------|
| `preconditions` | バリデーション、認可チェックの実装に活用 |
| `postconditions` | テストケースの期待結果として活用 |
| `modelInteractions` | 必要なエンドポイント・サービス層の設計に活用 |
| `notes` | 実装時の補足情報、非機能要件の把握に活用 |

### 3.3 各モデルの基本CRUD操作を定義する

JSON仕様の各モデルに対して、以下の基本操作を定義：

| 操作 | HTTPメソッド | エンドポイント例 | 説明 |
|------|-------------|-----------------|------|
| 一覧取得 | GET | `/api/v1/posts` | ページネーション、フィルタ、ソート対応 |
| 単体取得 | GET | `/api/v1/posts/:id` | 関連データの展開オプション |
| 作成 | POST | `/api/v1/posts` | バリデーション実行 |
| 更新 | PATCH/PUT | `/api/v1/posts/:id` | 部分更新対応 |
| 削除 | DELETE | `/api/v1/posts/:id` | 論理削除 or 物理削除 |

### 3.4 apiOptionsからAPI設定を自動導出する

JSON仕様の各フィールドの`apiOptions`から、API動作設定を自動導出する。

#### フィルタ可能フィールドの抽出

`apiOptions.filterable: true` のフィールドを抽出：

```markdown
## フィルタ可能フィールド（自動導出）

| モデル | フィールド | 型 | クエリパラメータ例 |
|--------|-----------|-----|-------------------|
| Post | status | enum | `?status=published` |
| Post | category_id | relation | `?category_id=uuid` |
| Post | created_at | date | `?created_at_from=2024-01-01&created_at_to=2024-12-31` |
| Product | price | integer | `?price_min=1000&price_max=5000` |
```

#### ソート可能フィールドの抽出

`apiOptions.sortable: true` のフィールドを抽出：

```markdown
## ソート可能フィールド（自動導出）

| モデル | フィールド | 型 |
|--------|-----------|-----|
| Post | created_at | date |
| Post | updated_at | date |
| Post | title | string |
| Product | price | integer |
| Product | stock | integer |
```

#### 全文検索対象フィールドの抽出

`apiOptions.searchable: true` のフィールドを抽出：

```markdown
## 全文検索対象フィールド（自動導出）

| モデル | フィールド | 型 |
|--------|-----------|-----|
| Post | title | string |
| Post | content | richText |
| Product | name | string |
| Product | description | text |
```

全文検索が有効なモデルには `?q=検索キーワード` パラメータを追加。

### 3.5 relationOptionsから展開設定を自動導出する

`relationOptions` から展開可能なリレーションを自動導出する。

#### 展開可能リレーションの抽出

`relationOptions.expandable: true` のフィールドを抽出：

```markdown
## 展開可能リレーション（自動導出）

| モデル | フィールド | 先モデル | デフォルト展開 | includeパラメータ |
|--------|-----------|---------|---------------|------------------|
| Post | author | User | false | `?include=author` |
| Post | category | Category | true | 自動展開 |
| Post | tags | Tag | false | `?include=tags` |
| Order | customer | User | false | `?include=customer` |
| Order | items | OrderItem | true | 自動展開 |
```

#### デフォルト展開の扱い

- `defaultExpand: true` のリレーションは、明示的な指定なしで常に展開
- `defaultExpand: false` の場合は `?include=xxx` で明示的に指定

### 3.6 アクセス制御とユースケースの関連付け

JSON仕様の `roles` と `accessControl` を確認し、各ユースケースの権限を整理する。

```markdown
## アクセス制御マトリクス

| ユースケース | アクター | 必要なロール | 行レベル制御 |
|-------------|---------|-------------|-------------|
| Purchase Product | Customer | user | - |
| Manage Products | Admin | admin | - |
| View Own Orders | Customer | user | ownerField: customerId |
```

### 3.7 ユースケース実装計画を作成する

各ユースケースの`modelInteractions`から、実装に必要な要素を整理する。

#### ユースケースからエンドポイントへの変換

`modelInteractions`の`hint`に基づいて、必要なエンドポイントを導出：

| hint | 導出されるエンドポイント |
|------|------------------------|
| `read` (単体) | `GET /api/v1/{model}/{id}` |
| `read` (一覧) | `GET /api/v1/{model}` |
| `write` (作成) | `POST /api/v1/{model}` |
| `write` (更新) | `PATCH /api/v1/{model}/{id}` |
| `delete` | `DELETE /api/v1/{model}/{id}` |
| `search` | `GET /api/v1/{model}?q=xxx` |
| `aggregate` | カスタムエンドポイントまたはサービス層で実装 |

#### 実装計画の例

```markdown
## ユースケース実装計画: uc-1 Purchase Product

### 必要なエンドポイント

| エンドポイント | 由来 | 説明 |
|---------------|------|------|
| GET /api/v1/carts/current | Cart (read) | 現在のユーザーのカートを取得 |
| GET /api/v1/products/:id | Product (read) | 商品の在庫確認 |
| POST /api/v1/orders | Order (write) | 注文を作成 |
| PATCH /api/v1/products/:id | Product (write) | 在庫を減らす |
| DELETE /api/v1/cart_items | CartItem (delete) | カートをクリア |

### バリデーション（preconditionsから導出）

- ユーザー認証チェック
- カート内商品の存在チェック
- 在庫数の確認

### テスト期待結果（postconditionsから導出）

- [ ] 注文レコードが作成されること
- [ ] 在庫数が購入数量分減少すること
- [ ] カートが空になること
- [ ] 確認メールが送信されること

### 補足（notesから）

- 決済処理はStripe APIを利用
- 決済失敗時のロールバック処理が必要
```

## 出力

### 自動導出された設定

```markdown
## API設定サマリ（JSON仕様から自動導出）

### フィルタ可能フィールド
[apiOptions.filterable: true のフィールド一覧]

### ソート可能フィールド
[apiOptions.sortable: true のフィールド一覧]

### 全文検索対象フィールド
[apiOptions.searchable: true のフィールド一覧]

### 展開可能リレーション
[relationOptions.expandable: true のフィールド一覧]
```

### ユースケース実装計画

```markdown
## ユースケース一覧

| ID | 名前 | アクター | 関連モデル | エンドポイント数 |
|----|------|---------|-----------|----------------|
| uc-1 | Purchase Product | Customer | Cart, Product, Order, CartItem | 5 |
| uc-2 | Manage Products | Admin | Product, Category | 8 |

## 各ユースケースの実装計画

### uc-1: Purchase Product

[modelInteractionsから導出した実装計画]

### uc-2: Manage Products

[modelInteractionsから導出した実装計画]
```

### モデルごとのエンドポイント一覧

```markdown
## Posts モデル

### エンドポイント一覧

| メソッド | パス | 説明 | 関連ユースケース |
|---------|------|------|-----------------|
| GET | /api/v1/posts | 記事一覧取得 | View Posts |
| GET | /api/v1/posts/:id | 記事詳細取得 | View Posts |
| POST | /api/v1/posts | 記事作成 | Create Post |
| PATCH | /api/v1/posts/:id | 記事更新 | Edit Post |
| DELETE | /api/v1/posts/:id | 記事削除 | Delete Post |

### フィルタ可能なフィールド（自動導出）
- status (enum) - `apiOptions.filterable: true`
- category_id (relation) - `apiOptions.filterable: true`
- created_at (date range) - `apiOptions.filterable: true`

### ソート可能なフィールド（自動導出）
- created_at - `apiOptions.sortable: true`
- updated_at - `apiOptions.sortable: true`
- title - `apiOptions.sortable: true`

### 全文検索（自動導出）
- 検索対象: title, content
- クエリパラメータ: `?q=検索キーワード`

### 展開可能なリレーション（自動導出）
- author (User) - `relationOptions.expandable: true`, defaultExpand: false
- category (Category) - `relationOptions.expandable: true`, defaultExpand: true
- tags (Tag[]) - `relationOptions.expandable: true`, defaultExpand: false
```

これらを次のステップで使用する。
