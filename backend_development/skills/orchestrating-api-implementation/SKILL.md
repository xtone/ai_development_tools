---
name: orchestrating-api-implementations
description: JSONで定義されたAPI仕様を元にRuby on RailsでAPIと管理画面を実装するスキル。全体のオーケストレーションを行い、各ステップの詳細ガイドラインに従って実装を進めます。
---

## 概要

JSONで定義されたAPI仕様に基づいて、Ruby on Rails + PostgreSQLでAPIと管理画面を実装します。

## 技術スタック

| 項目 | 技術 |
|------|------|
| 言語 | Ruby 3.4 |
| フレームワーク | Ruby on Rails 8.1 |
| データベース | PostgreSQL 18 |
| ORM | Active Record |

## ステップ

各ステップの詳細は `steps/` ディレクトリ内のファイルを参照。

### 1. アプリケーション仕様を確認する
詳細: @steps/01_check_specification.md

JSON仕様ファイルを読み込み、モデル構造・フィールド定義・リレーションを把握する。
仕様形式: @references/01_json_specification.md

### 2. 技術スタックを決定する
詳細: @steps/02_select_tech_stack.md

環境確認と管理画面の方式（ActiveAdmin / Administrate / Hotwire）を決定する。

### 3. ユースケースを洗い出す
詳細: @steps/03_define_usecases.md

各モデルのCRUD操作、ページネーション、フィルタリング、ソート、リレーション取得方法を定義する。

### 4. DBスキーマを設計する
詳細: @steps/04_design_db_schema.md

JSON仕様の型をPostgreSQLの型にマッピングし、テーブル設計を行う。

### 5. SQLとインデックスを定義する
詳細: @steps/05_define_sql_and_indexes.md

ユースケースで実行されるSQLを洗い出し、通常インデックスと全文検索インデックス（GIN + tsvector）を定義する。

### 6. プロジェクトを初期化する
詳細: @steps/06_initialize_project.md

Rails 8.1プロジェクトを作成し、必要なGemと設定をセットアップする。

### 7. DBマイグレーションを実装する
詳細: @steps/07_implement_migration.md

設計に基づいてマイグレーションファイルを作成・実行する。

### 8. ORマッピングを実装する
詳細: @steps/08_implement_orm.md

Active Recordモデルにリレーション、スコープ、クエリメソッドを実装する。

### 9. バリデーションを実装する
詳細: @steps/09_implement_validation.md

JSON仕様のvalidation設定に基づいてActive Recordバリデーションを実装する。

### 10. APIエンドポイントを実装する
詳細: @steps/10_implement_api_endpoints.md

RESTful APIエンドポイント（CRUD、ページネーション、フィルタリング、ソート）を実装する。

### 11. APIの動作確認を行う
詳細: @steps/11_verify_api.md

curlとRSpecでAPIの動作を検証し、N+1問題がないことを確認する。

### 12. 管理画面を実装する
詳細: @steps/12_implement_admin_ui.md

選択した方式（ActiveAdmin / Administrate / Hotwire）で管理画面を実装する。

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
    ├── 04_design_db_schema.md
    ├── 05_define_sql_and_indexes.md
    ├── 06_initialize_project.md
    ├── 07_implement_migration.md
    ├── 08_implement_orm.md
    ├── 09_implement_validation.md
    ├── 10_implement_api_endpoints.md
    ├── 11_verify_api.md
    └── 12_implement_admin_ui.md
```
