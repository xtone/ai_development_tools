# ステップ3: ユースケースを洗い出す

## サブエージェント実行情報

| 項目 | 値 |
|------|-----|
| **入力ファイル** | `.artifacts/01_specification.json` |
| **出力ファイル** | `.artifacts/03_usecases.json` |
| **依存ステップ** | ステップ1 |

### 出力ファイル形式

```json
{
  "version": "1.0",
  "generatedAt": "2025-01-01T00:00:00Z",
  "step": "03_usecases",
  "data": {
    "actors": [
      {
        "id": "actor-1",
        "name": "Customer",
        "description": "一般顧客"
      }
    ],
    "useCases": [
      {
        "id": "uc-1",
        "name": "Browse Products",
        "description": "商品を閲覧する",
        "actorIds": ["actor-1"]
      }
    ],
    "endpoints": [
      {
        "model": "Post",
        "basePath": "/api/v1/posts",
        "actions": ["index", "show", "create", "update", "destroy"],
        "filters": ["status", "author_id", "category_id"],
        "sorts": ["created_at", "updated_at", "title"],
        "includes": ["author", "category", "tags"],
        "search": {
          "enabled": true,
          "fields": ["title", "content"]
        }
      }
    ],
    "accessControl": [
      {
        "useCase": "uc-1",
        "actor": "actor-1",
        "roles": ["user"],
        "rowLevelSecurity": null
      }
    ]
  }
}
```

### 完了報告に含める情報

- アクター数
- ユースケース数
- エンドポイント数
- 出力ファイルパス

---

## 目次

- [目的](#目的)
- [手順](#手順)
  - [3.1 JSON仕様からアクターとユースケースを抽出する](#31-json仕様からアクターとユースケースを抽出する)
  - [3.2 各モデルの基本CRUD操作を定義する](#32-各モデルの基本crud操作を定義する)
  - [3.3 ユースケースとCRUD操作をマッピングする](#33-ユースケースとcrud操作をマッピングする)
  - [3.4 一覧取得のオプションを定義する](#34-一覧取得のオプションを定義する)
  - [3.5 リレーションの取得方法を定義する](#35-リレーションの取得方法を定義する)
  - [3.6 アクセス制御とユースケースの関連付け](#36-アクセス制御とユースケースの関連付け)
  - [3.7 ユースケース一覧を作成する](#37-ユースケース一覧を作成する)
- [出力](#出力)

---

## 目的

JSON仕様で定義されたアクターとユースケースを確認し、各モデルに対するAPI操作とエンドポイントを定義する。

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

| プロパティ | 説明 |
|-----------|------|
| `id` | アクターの一意なID |
| `name` | アクター名 |
| `description` | アクターの役割説明 |

#### ユースケース (UseCase) の確認

```json
"useCases": [
  {
    "id": "uc-1",
    "name": "Purchase Product",
    "description": "商品を購入する",
    "actorIds": ["actor-1"]
  }
]
```

| プロパティ | 説明 |
|-----------|------|
| `id` | ユースケースの一意なID |
| `name` | ユースケース名 |
| `description` | ユースケースの詳細説明 |
| `actorIds` | このユースケースを実行できるアクターのIDリスト |

### 3.2 各モデルの基本CRUD操作を定義する

JSON仕様の各モデルに対して、以下の基本操作を定義：

| 操作 | HTTPメソッド | エンドポイント例 | 説明 |
|------|-------------|-----------------|------|
| 一覧取得 | GET | `/api/v1/posts` | ページネーション、フィルタ、ソート対応 |
| 単体取得 | GET | `/api/v1/posts/:id` | 関連データの展開オプション |
| 作成 | POST | `/api/v1/posts` | バリデーション実行 |
| 更新 | PATCH/PUT | `/api/v1/posts/:id` | 部分更新対応 |
| 削除 | DELETE | `/api/v1/posts/:id` | 論理削除 or 物理削除 |

### 3.3 ユースケースとCRUD操作をマッピングする

JSON仕様で定義されたユースケースを、具体的なAPI操作にマッピングする。

```markdown
## ユースケース: Purchase Product (uc-1)

### 実行可能なアクター
- Customer (actor-1)

### 関連するAPI操作
1. GET /api/v1/products - 商品一覧を閲覧
2. GET /api/v1/products/:id - 商品詳細を確認
3. POST /api/v1/orders - 注文を作成
4. POST /api/v1/payments - 支払いを実行
```

### 3.4 一覧取得のオプションを定義する

#### ページネーション

```
GET /api/v1/posts?page=1&per_page=20
```

レスポンスヘッダまたはメタ情報に含める：
- `total_count`: 総件数
- `total_pages`: 総ページ数
- `current_page`: 現在のページ
- `per_page`: 1ページあたりの件数

#### フィルタリング

```
GET /api/v1/posts?status=published&category_id=1
```

JSON仕様のフィールドに基づいてフィルタ可能な項目を定義。

#### ソート

```
GET /api/v1/posts?sort=created_at&order=desc
```

### 3.5 リレーションの取得方法を定義する

#### 関連データの展開（Eager Loading）

```
GET /api/v1/posts?include=author,category
```

N+1問題を回避するため、`includes`で事前読み込み。

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

### 3.7 ユースケース一覧を作成する

各ユースケースとモデルを統合した形式でまとめる：

```markdown
## アクター一覧

| ID | 名前 | 説明 |
|----|------|------|
| actor-1 | Customer | 一般顧客 |
| actor-2 | Admin | 管理者 |

## ユースケース一覧

| ID | 名前 | 説明 | アクター |
|----|------|------|---------|
| uc-1 | Purchase Product | 商品を購入する | Customer |
| uc-2 | Manage Products | 商品を管理する | Admin |

## Posts モデル

### エンドポイント一覧

| メソッド | パス | 説明 | 関連ユースケース |
|---------|------|------|-----------------|
| GET | /api/v1/posts | 記事一覧取得 | View Posts |
| GET | /api/v1/posts/:id | 記事詳細取得 | View Posts |
| POST | /api/v1/posts | 記事作成 | Create Post |
| PATCH | /api/v1/posts/:id | 記事更新 | Edit Post |
| DELETE | /api/v1/posts/:id | 記事削除 | Delete Post |

### フィルタ可能なフィールド
- status (enum)
- category_id (relation)
- created_at (date range)

### ソート可能なフィールド
- created_at
- updated_at
- title

### 展開可能なリレーション
- author (User)
- category (Category)
- tags (Tag[])
```

## 出力

- アクター一覧
- ユースケース一覧（アクターとのマッピング含む）
- 全モデルのエンドポイント一覧（ユースケースとのマッピング含む）
- アクセス制御マトリクス

これらを次のステップで使用する。
