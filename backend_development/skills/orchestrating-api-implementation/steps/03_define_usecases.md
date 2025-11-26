# ステップ3: ユースケースを洗い出す

## 目的

各モデルに対する基本的なCRUD操作と、APIとして提供するエンドポイントを定義する。

## 手順

### 3.1 各モデルの基本ユースケースを定義する

JSON仕様の各モデルに対して、以下の基本操作を定義：

| 操作 | HTTPメソッド | エンドポイント例 | 説明 |
|------|-------------|-----------------|------|
| 一覧取得 | GET | `/api/v1/posts` | ページネーション、フィルタ、ソート対応 |
| 単体取得 | GET | `/api/v1/posts/:id` | 関連データの展開オプション |
| 作成 | POST | `/api/v1/posts` | バリデーション実行 |
| 更新 | PATCH/PUT | `/api/v1/posts/:id` | 部分更新対応 |
| 削除 | DELETE | `/api/v1/posts/:id` | 論理削除 or 物理削除 |

### 3.2 一覧取得のオプションを定義する

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

### 3.3 リレーションの取得方法を定義する

#### 関連データの展開（Eager Loading）

```
GET /api/v1/posts?include=author,category
```

N+1問題を回避するため、`includes`で事前読み込み。

### 3.4 ユースケース一覧を作成する

各モデルごとに以下の形式でまとめる：

```markdown
## Posts モデル

### エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/v1/posts | 記事一覧取得 |
| GET | /api/v1/posts/:id | 記事詳細取得 |
| POST | /api/v1/posts | 記事作成 |
| PATCH | /api/v1/posts/:id | 記事更新 |
| DELETE | /api/v1/posts/:id | 記事削除 |

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

全モデルのユースケース一覧を作成し、次のステップで使用する。
