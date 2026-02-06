# Android Data Layer Skill

## 概要

AndroidプロジェクトのData Layer実装を支援するClaude Code Skillです。Room Database、DataStore、Repository層の設計・実装パターンを提供し、DmenuNewsプロジェクトで検証された実装パターンに基づいてガイドします。

## 機能

### 1. Room Database実装支援

- **Entity定義**: 単一主キー、複合主キー、シンプルEntityの3パターン
- **DAO設計**: Flow、suspend、Transaction、Upsert、キープ数制限の5パターン
- **Migration実装**: バージョン管理、スキーマ変更、データ移行
- **Transactionable**: トランザクション処理の抽象化

### 2. DataStore実装支援

- **Preferences DataStore**: 型安全なキー定義（sealed class）
- **マイグレーション**: SharedPreferencesからの段階的移行
- **Repository統合**: DataStore + Room の統合パターン

### 3. Repository層設計支援

- **データソース統合**: Remote + Local のパターン
- **キャッシュ戦略**: キャッシュファースト、ネットワークファーストなど
- **エラーハンドリング**: Result型を活用した明示的なエラー処理

### 4. テストパターン提供

- **Repository Unit Test**: mockk を使ったモックテスト
- **Room In-Memory Test**: 実際のRoomを使った統合テスト
- **DataStore Test**: Preferences の読み書き検証

## 使い方

### 基本的な使い方

```bash
# プロジェクトルートで実行
claude-code

# スキルを呼び出し
> /android-data-layer
```

### 実装例

#### 1. お気に入り機能の実装

```
ユーザー: お気に入り機能を実装したい

スキル:
1. 実装したい機能は何ですか？
   → お気に入り記事の保存・削除・一覧表示
2. どのようなデータを扱いますか？
   → 記事ID、タイトル、URL、サムネイル、保存日時
3. 既存の実装状況を教えてください
   → 新規実装、Room Databaseは既存プロジェクトで使用中（version 5）

→ Entity、DAO、Repository、Testコードを生成
```

#### 2. ユーザー設定の実装

```
ユーザー: ユーザー設定（フォントサイズ、テーマ）をDataStoreで実装したい

スキル:
1. 実装したい機能は何ですか？
   → フォントサイズ（小・中・大）、テーマ（ライト・ダーク）の保存
2. どのようなデータを扱いますか？
   → Int（フォントサイズ）、String（テーマ）
3. 既存の実装状況を教えてください
   → SharedPreferencesから移行したい

→ DataStoreKey、Repository、Migrationコードを生成
```

## ディレクトリ構成

```
skills/android-data-layer/
├── SKILL.md              # スキル定義（Agent Skills形式）
├── README.md             # このファイル
└── artifacts/
    └── dmenu-interview-result.md  # DmenuNewsの実装パターン（892行）
```

## 知識ベース

このスキルは、DmenuNewsプロジェクトで実証済みの以下のパターンを含んでいます：

### Room Database

- **8つのEntity**: UserTab、ProcessedTab、SearchNewsHistory、AlreadyReadNews、PushDataId、KeywordRecommend、FavoriteArticle、BrowsingHistory
- **DAO実装**: Flow返却、suspend関数、Transaction、Upsert、古いデータ削除
- **Migration**: MIGRATION_3_4（タブ追加）、MIGRATION_4_5（テーブル追加）

### DataStore

- **60以上のキー定義**: 型安全なsealed class パターン
- **マイグレーション**: SharedPreferencesから段階的移行
- **Repository実装**: マイリスト設定、カウンター管理

### Repository層

- **データソース統合**: Room + DataStore、API + Room + Paging
- **エラーハンドリング**: Result型、runCatching、getOrElse/getOrThrow
- **キャッシュ戦略**: キャッシュファースト、有効期限管理

### よくあるミス

- メインスレッドでのDB操作
- Migration漏れ
- キャッシュ戦略の不備
- メモリリーク（Flow collect、lifecycle-aware）

## 開発履歴

- **v1.0** (2026-01-20): 初版リリース
  - DmenuNewsプロジェクトへのインタビューをもとに作成
  - Room、DataStore、Repository層の実装パターンを提供
  - テストパターン、DI設定を含む

## 関連スキル

- **android-architecture**: アーキテクチャ設計支援（MVVM、Clean Architecture）
- **android-test-runner**: テスト実行・失敗分析
- **android-test-generator**: テストコード自動生成

## ライセンス

このスキルは、Xtone社のAI開発ツールプロジェクトの一部です。

## 貢献

改善提案やバグ報告は、GitHub Issueでお願いします：
https://github.com/xtone/ai_development_tools/issues

## 作成者

- 石原正也 (Masaya Ishihara)
- Androidチームリード、Xtone
