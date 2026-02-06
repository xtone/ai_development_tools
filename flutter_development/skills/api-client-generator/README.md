# Flutter API Client Generator

OpenAPI/Swagger仕様からFlutter用APIクライアントコードを自動生成するスキルです。

## 機能

- **型安全なモデル生成**: Freezedベースのイミュータブルモデル
- **APIサービス生成**: Retrofitアノテーション付きAPIクライアント
- **リポジトリパターン**: Either型によるエラーハンドリング（dartz）
- **状態管理統合**: Riverpodプロバイダの自動生成

## 使用技術

| ライブラリ | 用途 |
|-----------|------|
| dio | HTTP通信 |
| retrofit | 型安全なAPI定義 |
| freezed | イミュータブルモデル |
| riverpod | 状態管理・依存注入 |
| dartz | Either型エラーハンドリング |

## クイックスタート

```bash
# OpenAPI仕様ファイルを指定してスキルを実行
/api-client-generator path/to/openapi.yaml

# コード生成
flutter pub run build_runner build --delete-conflicting-outputs
```

## 生成されるコード構造

```
lib/
├── core/error/          # Failure型定義
├── core/network/        # Dioクライアント設定
├── data/api/            # Retrofit APIサービス
├── data/repositories/   # リポジトリ実装
├── domain/models/       # Freezedモデル
├── domain/repositories/ # リポジトリインターフェース
└── presentation/providers/ # Riverpodプロバイダ
```

## ドキュメント

- [SKILL.md](./SKILL.md) - 詳細な仕様とワークフロー
- [examples/](./examples/) - 入出力の完全な例
- [steps/](./steps/) - 各ステップの詳細ガイドライン
- [references/](./references/) - OpenAPI型マッピング、コードテンプレート
