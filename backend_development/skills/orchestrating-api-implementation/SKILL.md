---
name: orchestrating-api-implementation
description: JSONで定義されたAPI仕様を元にRuby on RailsでAPIと管理画面を実装するスキル。全体のオーケストレーションを行い、各ステップの詳細ガイドラインに従って実装を進めます。
---

## 概要

このスキルは、JSONで定義されたAPI仕様に基づいて、Ruby on Rails + PostgreSQLでAPIと管理画面を実装します。

**サブエージェント対応**: 各ステップはサブエージェント（Taskツール）で実行可能です。コンテキストが大きくなる場合は、ステップごとにサブエージェントを起動してください。

## このスキルを使用するタイミング

Claudeは以下の状況でこのスキルを使用します：

- ユーザーがJSON形式のAPI仕様を提供し、Rails APIの実装を依頼した場合
- microCMSなどのHeadless CMSの仕様からRails APIを生成する場合
- 既存のJSON仕様ファイル（app.jsonなど）を参照してAPI実装を依頼された場合
- 「APIを実装して」「管理画面を作成して」といったリクエストでJSON仕様が存在する場合

## 技術スタック

| 項目 | 技術 |
|------|------|
| 言語 | Ruby 3.4 |
| フレームワーク | Ruby on Rails 8.1 |
| データベース | PostgreSQL 18 |
| ORM | Active Record |

---

## 実行モード

### モード1: 単一エージェント実行（小規模プロジェクト向け）

コンテキストに余裕がある場合は、このスキルを読み込んだ単一エージェントで全ステップを順に実行します。

### モード2: サブエージェント実行（推奨）

大規模プロジェクトや複雑な実装では、各ステップをサブエージェントで実行します。

```
┌─────────────────────────────────────────────────────────────┐
│ オーケストレータ（メインエージェント）                        │
│                                                             │
│  ステップ1 → ステップ2 → ... → ステップ14                    │
│  (Task)      (Task)           (Task)                        │
│     ↓           ↓                ↓                          │
│  成果物1     成果物2          成果物14                       │
│  (JSON/MD)   (JSON/MD)        (実装コード)                   │
└─────────────────────────────────────────────────────────────┘
```

**メリット**:
- 各ステップが独立したコンテキストを持つ
- コンテキスト圧縮による情報喪失を回避
- 並列実行が可能（依存関係がないステップ）

---

## 成果物ディレクトリ構造

プロジェクトルートに以下のディレクトリを作成し、各ステップの成果物を保存します：

```
{project_root}/
├── .artifacts/                    # 設計成果物（Git管理推奨）
│   ├── 01_specification.json      # ステップ1: 仕様確認結果
│   ├── 02_tech_stack.json         # ステップ2: 技術スタック
│   ├── 03_usecases.json           # ステップ3: ユースケース定義
│   ├── 04_openapi.yaml            # ステップ4: OpenAPI定義
│   ├── 05_db_schema.json          # ステップ5: DBスキーマ設計
│   ├── 06_indexes.json            # ステップ6: インデックス定義
│   └── README.md                  # 成果物の説明
├── app/                           # Rails実装コード
├── config/
├── db/
├── docs/
│   └── api/
│       └── openapi.yaml           # 本番用OpenAPI（ステップ4で生成）
└── spec/
```

---

## ステップ一覧

各ステップの詳細は `steps/` ディレクトリ内のファイルを参照してください。

### フェーズ1: 設計（ステップ1-6）

| ステップ | 説明 | 入力 | 出力 |
|---------|------|------|------|
| 1. 仕様確認 | JSON仕様を解析 | `app.json` | `.artifacts/01_specification.json` |
| 2. 技術スタック | 環境・方式を決定 | ステップ1の出力 | `.artifacts/02_tech_stack.json` |
| 3. ユースケース | CRUD操作を定義 | ステップ1の出力 | `.artifacts/03_usecases.json` |
| 4. OpenAPI定義 | API仕様を作成 | ステップ1,3の出力 | `.artifacts/04_openapi.yaml` |
| 5. DBスキーマ | テーブル設計 | ステップ1の出力 | `.artifacts/05_db_schema.json` |
| 6. インデックス | SQL/索引定義 | ステップ3,5の出力 | `.artifacts/06_indexes.json` |

### フェーズ2: 実装（ステップ7-14）

| ステップ | 説明 | 入力 | 出力 |
|---------|------|------|------|
| 7. プロジェクト初期化 | Rails new | ステップ2の出力 | Railsプロジェクト |
| 8. マイグレーション | DB構築 | ステップ5,6の出力 | `db/migrate/*` |
| 9. ORマッピング | モデル実装 | ステップ1,5の出力 | `app/models/*` |
| 10. バリデーション | 検証ロジック | ステップ1の出力 | `app/models/*` |
| 11. APIエンドポイント | コントローラ | ステップ3,4の出力 | `app/controllers/*` |
| 12. 動作確認 | テスト | 全ステップの出力 | `spec/*` |
| 13. 管理画面 | Admin実装 | ステップ2の出力 | 管理画面コード |
| 14. Playground | API試験環境 | ステップ4の出力 | Swagger UI |

---

## ステップ詳細

### 1. アプリケーション仕様を確認する

詳細: @steps/01_check_specification.md

**入力**:
- `app.json` または同等のJSON仕様ファイル

**出力**:
- `.artifacts/01_specification.json`

**サブエージェントプロンプト例**:
```
@steps/01_check_specification.md の手順に従って、
{spec_file_path} を解析し、結果を .artifacts/01_specification.json に保存してください。

仕様形式: @references/01_json_specification.md

完了したら、以下を報告してください：
- モデル数
- リレーション数
- カスタム型の有無
- 出力ファイルパス
```

---

### 2. 技術スタックを決定する

詳細: @steps/02_select_tech_stack.md

**入力**:
- `.artifacts/01_specification.json`

**出力**:
- `.artifacts/02_tech_stack.json`

**サブエージェントプロンプト例**:
```
@steps/02_select_tech_stack.md の手順に従って、
.artifacts/01_specification.json を読み込み、技術スタックを決定してください。

管理画面の方式について、ユーザーに確認が必要な場合は AskUserQuestion ツールを使用してください。

結果は .artifacts/02_tech_stack.json に保存してください。
```

---

### 3. ユースケースを洗い出す

詳細: @steps/03_define_usecases.md

**入力**:
- `.artifacts/01_specification.json`

**出力**:
- `.artifacts/03_usecases.json`

**サブエージェントプロンプト例**:
```
@steps/03_define_usecases.md の手順に従って、
.artifacts/01_specification.json を読み込み、ユースケースを洗い出してください。

各モデルのCRUD操作、ページネーション、フィルタリング、ソート、リレーション取得方法を定義し、
結果は .artifacts/03_usecases.json に保存してください。
```

---

### 4. OpenAPI定義を作成する

詳細: @steps/04_define_openapi.md

**入力**:
- `.artifacts/01_specification.json`
- `.artifacts/03_usecases.json`

**出力**:
- `.artifacts/04_openapi.yaml`
- `docs/api/openapi.yaml`（本番用コピー）

**サブエージェントプロンプト例**:
```
@steps/04_define_openapi.md の手順に従って、
.artifacts/01_specification.json と .artifacts/03_usecases.json を読み込み、
OpenAPI 3.1定義を作成してください。

結果は以下に保存してください：
- .artifacts/04_openapi.yaml
- docs/api/openapi.yaml
```

---

### 5. DBスキーマを設計する

詳細: @steps/05_design_db_schema.md

**入力**:
- `.artifacts/01_specification.json`

**出力**:
- `.artifacts/05_db_schema.json`

**サブエージェントプロンプト例**:
```
@steps/05_design_db_schema.md の手順に従って、
.artifacts/01_specification.json を読み込み、DBスキーマを設計してください。

JSON仕様の型をPostgreSQLの型にマッピングし、テーブル設計を行ってください。
結果は .artifacts/05_db_schema.json に保存してください。
```

---

### 6. SQLとインデックスを定義する

詳細: @steps/06_define_sql_and_indexes.md

**入力**:
- `.artifacts/03_usecases.json`
- `.artifacts/05_db_schema.json`

**出力**:
- `.artifacts/06_indexes.json`

**サブエージェントプロンプト例**:
```
@steps/06_define_sql_and_indexes.md の手順に従って、
.artifacts/03_usecases.json と .artifacts/05_db_schema.json を読み込み、
必要なインデックスを定義してください。

結果は .artifacts/06_indexes.json に保存してください。
```

---

### 7. プロジェクトを初期化する

詳細: @steps/07_initialize_project.md

**入力**:
- `.artifacts/02_tech_stack.json`

**出力**:
- Railsプロジェクト（Gemfile, 基本設定など）

**サブエージェントプロンプト例**:
```
@steps/07_initialize_project.md の手順に従って、
.artifacts/02_tech_stack.json を読み込み、Railsプロジェクトを初期化してください。

Docker環境のセットアップ、Gem追加、基本設定を行ってください。
完了したら `rails server` で起動確認してください。
```

---

### 8. DBマイグレーションを実装する

詳細: @steps/08_implement_migration.md

**入力**:
- `.artifacts/05_db_schema.json`
- `.artifacts/06_indexes.json`

**出力**:
- `db/migrate/*` マイグレーションファイル

**サブエージェントプロンプト例**:
```
@steps/08_implement_migration.md の手順に従って、
.artifacts/05_db_schema.json と .artifacts/06_indexes.json を読み込み、
マイグレーションファイルを作成・実行してください。

完了したら `rails db:migrate:status` の結果を報告してください。
```

---

### 9. ORマッピングを実装する

詳細: @steps/09_implement_orm.md

**入力**:
- `.artifacts/01_specification.json`
- `.artifacts/05_db_schema.json`

**出力**:
- `app/models/*` モデルファイル

**サブエージェントプロンプト例**:
```
@steps/09_implement_orm.md の手順に従って、
.artifacts/01_specification.json と .artifacts/05_db_schema.json を読み込み、
Active Recordモデルを実装してください。

リレーション、スコープ、Ransack設定を含めてください。
```

---

### 10. バリデーションを実装する

詳細: @steps/10_implement_validation.md

**入力**:
- `.artifacts/01_specification.json`

**出力**:
- `app/models/*` にバリデーション追加

**サブエージェントプロンプト例**:
```
@steps/10_implement_validation.md の手順に従って、
.artifacts/01_specification.json を読み込み、
JSON仕様のvalidation設定に基づいてActive Recordバリデーションを実装してください。
```

---

### 11. APIエンドポイントを実装する

詳細: @steps/11_implement_api_endpoints.md

**入力**:
- `.artifacts/03_usecases.json`
- `.artifacts/04_openapi.yaml`

**出力**:
- `app/controllers/api/v1/*`
- `app/serializers/*`
- `config/routes.rb`

**サブエージェントプロンプト例**:
```
@steps/11_implement_api_endpoints.md の手順に従って、
.artifacts/03_usecases.json と .artifacts/04_openapi.yaml を読み込み、
RESTful APIエンドポイントを実装してください。

コントローラ、シリアライザ、ルーティングを含めてください。
```

---

### 12. APIの動作確認を行う

詳細: @steps/12_verify_api.md

**入力**:
- 実装済みのAPIコード

**出力**:
- `spec/requests/*` テストファイル
- `spec/factories/*` ファクトリファイル

**サブエージェントプロンプト例**:
```
@steps/12_verify_api.md の手順に従って、
実装したAPIの動作確認を行ってください。

curlでの手動テストと、RSpecでのインテグレーションテストを実装してください。
N+1問題がないことも確認してください。
```

---

### 13. 管理画面を実装する

方式に応じて以下のファイルを参照：

- ActiveAdmin: @steps/13a_admin_activeadmin.md
- Administrate: @steps/13b_admin_administrate.md
- Hotwire: @steps/13c_admin_hotwire.md
- 共通設定: @steps/13d_admin_common.md

**入力**:
- `.artifacts/02_tech_stack.json`（選択した方式）
- `.artifacts/01_specification.json`

**出力**:
- 管理画面コード

**サブエージェントプロンプト例**:
```
.artifacts/02_tech_stack.json を読み込み、選択された管理画面方式を確認してください。

方式に応じて以下のガイドラインに従って管理画面を実装してください：
- ActiveAdmin: @steps/13a_admin_activeadmin.md
- Administrate: @steps/13b_admin_administrate.md
- Hotwire: @steps/13c_admin_hotwire.md
```

---

### 14. API Playgroundを実装する（オプション）

詳細: @steps/14_implement_api_playground.md

**入力**:
- `.artifacts/04_openapi.yaml`

**出力**:
- Swagger UI または カスタムPlayground

**サブエージェントプロンプト例**:
```
@steps/14_implement_api_playground.md の手順に従って、
.artifacts/04_openapi.yaml を使用してAPI Playgroundを実装してください。
```

---

## 成果物ファイル形式

### JSON成果物の共通構造

```json
{
  "version": "1.0",
  "generatedAt": "2025-01-01T00:00:00Z",
  "step": "01_specification",
  "data": {
    // ステップ固有のデータ
  }
}
```

### 01_specification.json

```json
{
  "version": "1.0",
  "generatedAt": "...",
  "step": "01_specification",
  "data": {
    "projectName": "プロジェクト名",
    "models": [
      {
        "name": "Post",
        "displayName": "記事",
        "fields": [...],
        "relations": [...]
      }
    ],
    "customTypes": [...],
    "actors": [...],
    "useCases": [...]
  }
}
```

### 02_tech_stack.json

```json
{
  "version": "1.0",
  "generatedAt": "...",
  "step": "02_tech_stack",
  "data": {
    "ruby": "3.4",
    "rails": "8.1",
    "database": "postgresql",
    "adminPanel": "activeadmin",
    "gems": ["alba", "kaminari", "ransack", "rack-cors"],
    "docker": true
  }
}
```

### 03_usecases.json

```json
{
  "version": "1.0",
  "generatedAt": "...",
  "step": "03_usecases",
  "data": {
    "actors": [...],
    "useCases": [...],
    "endpoints": [
      {
        "model": "Post",
        "actions": ["index", "show", "create", "update", "destroy"],
        "filters": ["status", "author_id"],
        "sorts": ["created_at", "updated_at"],
        "includes": ["author", "category", "tags"]
      }
    ]
  }
}
```

### 05_db_schema.json

```json
{
  "version": "1.0",
  "generatedAt": "...",
  "step": "05_db_schema",
  "data": {
    "tables": [
      {
        "name": "posts",
        "primaryKey": { "name": "id", "type": "uuid" },
        "columns": [
          { "name": "title", "type": "string", "null": false },
          { "name": "content", "type": "text", "null": true },
          { "name": "status", "type": "string", "null": false, "default": "draft" },
          { "name": "author_id", "type": "uuid", "null": false, "foreignKey": "users" }
        ],
        "timestamps": true
      }
    ]
  }
}
```

### 06_indexes.json

```json
{
  "version": "1.0",
  "generatedAt": "...",
  "step": "06_indexes",
  "data": {
    "indexes": [
      {
        "table": "posts",
        "columns": ["status"],
        "type": "btree",
        "unique": false
      },
      {
        "table": "posts",
        "columns": ["searchable"],
        "type": "gin",
        "unique": false
      }
    ],
    "fullTextSearch": [
      {
        "table": "posts",
        "column": "searchable",
        "sources": ["title", "content"],
        "weights": { "title": "A", "content": "B" }
      }
    ]
  }
}
```

---

## ファイル構成

```
orchestrating-api-implementation/
├── SKILL.md                 # このファイル
├── references/
│   └── 01_json_specification.md  # JSON仕様の定義
└── steps/
    ├── 01_check_specification.md
    ├── 02_select_tech_stack.md
    ├── 03_define_usecases.md
    ├── 04_define_openapi.md
    ├── 05_design_db_schema.md
    ├── 06_define_sql_and_indexes.md
    ├── 07_initialize_project.md
    ├── 08_implement_migration.md
    ├── 09_implement_orm.md
    ├── 10_implement_validation.md
    ├── 11_implement_api_endpoints.md
    ├── 12_verify_api.md
    ├── 13a_admin_activeadmin.md
    ├── 13b_admin_administrate.md
    ├── 13c_admin_hotwire.md
    ├── 13d_admin_common.md
    └── 14_implement_api_playground.md
```
