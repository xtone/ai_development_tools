# ステップ1: アプリケーション仕様を確認する

## 目次

- [目的](#目的)
- [手順](#手順)
  - [1.1 JSON仕様ファイルを読み込む](#11-json仕様ファイルを読み込む)
  - [1.2 プロジェクト情報を確認する](#12-プロジェクト情報を確認する)
  - [1.3 モデル構造を把握する](#13-モデル構造を把握する)
  - [1.4 フィールド定義を確認する](#14-フィールド定義を確認する)
  - [1.5 リレーションを確認する](#15-リレーションを確認する)
  - [1.6 カスタム型を確認する](#16-カスタム型を確認する)
  - [1.7 アクターとユースケースを確認する](#17-アクターとユースケースを確認する)
- [出力](#出力)
- [注意点](#注意点)

---

## 目的

JSON仕様ファイルを読み込み、実装に必要な情報を正確に把握する。

## 手順

### 1.1 JSON仕様ファイルを読み込む

ユーザーから提供されたJSON仕様ファイルを読み込む。
仕様の形式は @references/01_json_specification.md を参照。

### 1.2 プロジェクト情報を確認する

```json
{
  "projectName": "プロジェクト名",
  "version": "バージョン",
  "roles": ["public", "admin", "user"]
}
```

### 1.3 モデル構造を把握する

各モデルについて以下を確認：

- `name`: モデル名（テーブル名として使用）
- `displayName`: 表示名（管理画面で使用）
- `description`: モデルの説明
- `fields`: フィールド定義のリスト
- `accessControl`: アクセス制御設定

### 1.4 フィールド定義を確認する

各フィールドについて以下を確認：

| プロパティ | 確認内容 |
|-----------|----------|
| `name` | フィールド名（カラム名） |
| `displayName` | 表示名 |
| `type` | データ型 |
| `isPrimary` | プライマリキーか |
| `isIndex` | インデックスが必要か |
| `validation` | バリデーションルール |
| `relationTo` | リレーション先モデル |
| `apiOptions` | API公開オプション（後述） |
| `relationOptions` | リレーション設定（後述） |

#### apiOptions の確認

`apiOptions`が設定されているフィールドを抽出し、API動作を把握する：

| プロパティ | 意味 | 後続ステップでの活用 |
|-----------|------|---------------------|
| `filterable: true` | フィルタリング可能 | ステップ3, 4, 6, 11 |
| `sortable: true` | ソート可能 | ステップ3, 4, 6, 11 |
| `searchable: true` | 全文検索対象 | ステップ3, 4, 6, 11 |

```json
{
  "name": "title",
  "type": "string",
  "apiOptions": {
    "filterable": true,
    "sortable": true,
    "searchable": true
  }
}
```

#### relationOptions の確認

`type: "relation"`のフィールドで`relationOptions`が設定されている場合を確認：

| プロパティ | 意味 | 後続ステップでの活用 |
|-----------|------|---------------------|
| `expandable: true` | API応答で展開可能 | ステップ3, 4, 11 |
| `defaultExpand: true` | デフォルトで展開 | ステップ11 |
| `onDelete` | 削除時動作 | ステップ5, 8, 9 |

```json
{
  "name": "author",
  "type": "relation",
  "relationTo": "User",
  "relationOptions": {
    "expandable": true,
    "defaultExpand": false,
    "onDelete": "nullify"
  }
}
```

### 1.5 リレーションを確認する

`type: "relation"` のフィールドを抽出し、モデル間の関係を把握する。

#### リレーションの種類

- 1対1
- 1対多
- 多対多（中間テーブルが必要）

#### 削除時動作（onDelete）

| 値 | 動作 | Railsでの実装 |
|----|------|--------------|
| `cascade` | 連動削除 | `dependent: :destroy` |
| `nullify` | NULLに設定 | `dependent: :nullify` |
| `restrict` | 削除禁止（デフォルト） | `dependent: :restrict_with_error` |

### 1.6 カスタム型を確認する

`customTypes` が定義されている場合、その構造を把握する。
カスタム型は複数のフィールドをまとめた再利用可能な型定義。

```json
{
  "customTypes": [
    {
      "name": "SEO",
      "fields": [
        { "name": "title", "type": "string" },
        { "name": "description", "type": "text" }
      ]
    }
  ]
}
```

### 1.7 アクターとユースケースを確認する

#### アクター（Actor）の確認

システムを利用するユーザーや外部システムの役割を把握：

```json
{
  "actors": [
    {
      "id": "actor-1",
      "name": "Customer",
      "description": "一般顧客"
    }
  ]
}
```

#### ユースケース（UseCase）の確認

各ユースケースについて以下を確認：

| プロパティ | 説明 |
|-----------|------|
| `id` | ユースケースの一意なID |
| `name` | ユースケース名 |
| `description` | 説明 |
| `actorIds` | 実行可能なアクターのIDリスト |
| `preconditions` | 事前条件（自然言語のリスト） |
| `postconditions` | 事後条件（自然言語のリスト） |
| `modelInteractions` | モデルとのインタラクション |
| `notes` | 備考・補足説明 |

#### モデルインタラクション（ModelInteraction）の確認

各ユースケースがどのモデルに対してどのような操作を行うかを把握：

```json
{
  "modelInteractions": [
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
  ]
}
```

| hint値 | 意味 |
|--------|------|
| `read` | 読み取り操作 |
| `write` | 作成・更新操作 |
| `delete` | 削除操作 |
| `search` | 検索操作 |
| `aggregate` | 集計操作 |
| `other` | その他 |

## 出力

確認した内容を以下の形式でまとめる：

```markdown
## 仕様確認結果

### プロジェクト情報
- プロジェクト名: xxx
- バージョン: x.x.x
- ロール: public, admin, user

### モデル一覧
1. モデル名A - 説明
2. モデル名B - 説明

### リレーション
| 元モデル | フィールド | 先モデル | 関係 | 削除時動作 |
|---------|-----------|---------|------|-----------|
| Post | author | User | 多対1 | nullify |
| Post | category | Category | 多対1 | restrict |

### API公開設定サマリ

#### フィルタ可能フィールド（filterable: true）
| モデル | フィールド | 型 |
|--------|-----------|-----|
| Post | status | enum |
| Post | category_id | relation |

#### ソート可能フィールド（sortable: true）
| モデル | フィールド | 型 |
|--------|-----------|-----|
| Post | created_at | date |
| Post | title | string |

#### 全文検索対象フィールド（searchable: true）
| モデル | フィールド | 型 |
|--------|-----------|-----|
| Post | title | string |
| Post | content | richText |

#### 展開可能リレーション（expandable: true）
| モデル | フィールド | 先モデル | デフォルト展開 |
|--------|-----------|---------|---------------|
| Post | author | User | false |
| Post | category | Category | true |

### カスタム型
- SEO: title, description

### アクター一覧
| ID | 名前 | 説明 |
|----|------|------|
| actor-1 | Customer | 一般顧客 |
| actor-2 | Admin | 管理者 |

### ユースケース一覧
| ID | 名前 | アクター | 関連モデル |
|----|------|---------|-----------|
| uc-1 | Purchase Product | Customer | Product, Order, OrderItem |
| uc-2 | Manage Products | Admin | Product, Category |

### ユースケース詳細

#### uc-1: Purchase Product
- **説明**: 商品を購入する
- **アクター**: Customer
- **事前条件**:
  - 顧客がログイン済みであること
  - カートに1つ以上の商品が入っていること
- **事後条件**:
  - 注文レコードが作成される
  - 在庫数が減少する
- **モデルインタラクション**:
  | モデル | 操作 | 説明 |
  |--------|------|------|
  | Product | read | 在庫数を確認し、購入可能かどうかを判定する |
  | Order | write | 注文レコードを作成する |
  | Product | write | 在庫数を減らす |
- **備考**: 決済処理は外部サービスを利用
```

## 注意点

- この段階では認証設定（authConfig）は確認のみ。実装は後のフェーズで行う。
- accessControl、webhooks の設定も確認のみに留める。
- `apiOptions`と`relationOptions`は後続ステップで重要な情報源となるため、漏れなく抽出する。
- `modelInteractions`の`description`は自然言語で記述されており、LLMが実装時に参照する重要な情報。
