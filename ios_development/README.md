# iOS Development Skills

iOS/SwiftUI開発用のClaude Codeスキル集。

## Claude Codeマーケットプレイスとしての使用方法

このディレクトリはClaude Codeのマーケットプレイスとして利用できます。

### ローカルマーケットプレイスの追加

```bash
/plugin marketplace add /Users/okubo/Projects/ai_development_tools/ios_development
```

または、相対パスで：

```bash
/plugin marketplace add ./ios_development
```

### プラグインのインストール

マーケットプレイスを追加した後、以下のコマンドでプラグインをインストールできます：

```bash
# 個別にインストール
/plugin install swift-ios-migration@ios-development-skills
/plugin install swiftui-accessibility@ios-development-skills
/plugin install swiftui-code-review-checklist@ios-development-skills
/plugin install swiftui-coding-guidelines@ios-development-skills
/plugin install swiftui-components@ios-development-skills
/plugin install swiftui-ssot@ios-development-skills

# または、利用可能なプラグインを対話的に参照
/plugin
```

### マーケットプレイスの確認

```bash
# 追加されたマーケットプレイスをリスト表示
/plugin marketplace list

# マーケットプレイスのメタデータを更新
/plugin marketplace update ios-development-skills
```

## スキル一覧

- **swift-ios-migration**: Swift/iOSマイグレーションガイド
- **swiftui-accessibility**: アクセシビリティ実装ガイド
- **swiftui-code-review-checklist**: コードレビューチェックリスト
- **swiftui-coding-guidelines**: コーディングガイドライン
- **swiftui-components**: UIコンポーネントカタログ
- **swiftui-ssot**: 状態管理（SSOT）ガイド

