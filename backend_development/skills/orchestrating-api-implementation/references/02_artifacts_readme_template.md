# .artifacts/README.md テンプレート

このファイルは、プロジェクトの `.artifacts/` ディレクトリに配置する README のテンプレートです。

---

```markdown
# 設計成果物

このディレクトリには、`orchestrating-api-implementation` スキルで生成された設計成果物が保存されています。

## ファイル一覧

| ファイル | ステップ | 説明 |
|---------|---------|------|
| `01_specification.json` | 1. 仕様確認 | JSON仕様の解析結果 |
| `02_tech_stack.json` | 2. 技術スタック | Ruby/Rails/管理画面の設定 |
| `03_usecases.json` | 3. ユースケース | アクター、ユースケース、エンドポイント定義 |
| `04_openapi.yaml` | 4. OpenAPI定義 | API仕様（OpenAPI 3.1形式） |
| `05_db_schema.json` | 5. DBスキーマ | テーブル・カラム定義 |
| `06_indexes.json` | 6. インデックス | 通常/全文検索インデックス定義 |

## 依存関係図

```
app.json (入力)
    │
    ▼
┌─────────────────────────────┐
│ 01_specification.json       │ ← ステップ1
└─────────────────────────────┘
    │
    ├──────────────┬──────────────┬──────────────┐
    ▼              ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ 02_tech │  │ 03_use  │  │ 05_db_  │  │(モデル) │
│ stack   │  │ cases   │  │ schema  │  │(バリデ) │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
    │              │              │
    │              │              ▼
    │              │        ┌─────────┐
    │              ├───────▶│ 06_idx  │
    │              │        └─────────┘
    │              │              │
    │              ▼              ▼
    │        ┌─────────┐    ┌─────────┐
    │        │ 04_open │    │(マイグ) │
    │        │ api     │    └─────────┘
    │        └─────────┘
    │              │
    ▼              ▼
┌─────────┐  ┌─────────┐
│(Rails   │  │(API実装)│
│プロジェ │  │(テスト) │
│クト)    │  └─────────┘
└─────────┘
```

## 使用方法

### サブエージェントでの読み込み

各ステップのサブエージェントは、依存する成果物ファイルを読み込んで処理を行います：

```
# 例：ステップ8（マイグレーション実装）
入力: .artifacts/05_db_schema.json, .artifacts/06_indexes.json
出力: db/migrate/*
```

### 手動での確認

JSON ファイルは `jq` コマンドで整形して確認できます：

```bash
cat .artifacts/01_specification.json | jq '.data.models'
cat .artifacts/03_usecases.json | jq '.data.endpoints'
```

### OpenAPI定義の検証

```bash
npx @redocly/cli lint .artifacts/04_openapi.yaml
npx @redocly/cli preview-docs .artifacts/04_openapi.yaml
```

## バージョン管理

これらの成果物は Git で管理することを推奨します。
設計変更があった場合、差分を追跡できます。

```gitignore
# .gitignore に追加しない
# .artifacts/
```

## 生成日時

各ファイルには `generatedAt` タイムスタンプが含まれています：

```json
{
  "version": "1.0",
  "generatedAt": "2025-01-01T00:00:00Z",
  "step": "01_specification",
  "data": { ... }
}
```

## 再生成

特定のステップを再実行する場合、そのステップの出力ファイルを削除してから
サブエージェントを起動してください。

依存する後続ステップも再実行が必要になる場合があります。
```
