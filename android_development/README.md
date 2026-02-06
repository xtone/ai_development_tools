# Android Development Skills

Android/Jetpack Compose開発用のClaude Codeスキル集。

## インストール

```bash
# マーケットプレイスを追加
/plugin marketplace add xtone/ai_development_tools

# プラグインをインストール
/plugin install android-development@xtone-ai-development-tools
```

## スキル一覧

| スキル | 説明 |
|--------|------|
| **android-architecture** | MVI/MVVM/シンプルComposeから最適なアーキテクチャを提案 |
| **android-api-client** | Retrofit + OkHttpによるAPIクライアント実装ガイド |
| **android-ui-guidelines** | Jetpack ComposeのUI実装コーディングガイドライン |
| **android-data-layer** | Room/DataStore/Repositoryパターンの実装ガイド |
| **android-test-runner** | テスト実行と失敗分析の自動化 |
| **android-test-generator** | 実装コードからテストコードを自動生成 |
| **figma-to-compose** | FigmaデザインからJetpack Composeコードを生成 |

## ディレクトリ構造

```
android_development/
├── .claude-plugin/
│   ├── marketplace.json    # マーケットプレイス設定
│   └── plugin.json         # プラグイン基本情報
├── .claude/
│   └── skills/
│       ├── android-architecture/
│       ├── android-api-client/
│       ├── android-ui-guidelines/
│       ├── android-data-layer/
│       ├── android-test-runner/
│       ├── android-test-generator/
│       └── figma-to-compose/
└── README.md
```

## 関連リンク

- [Claude Code Plugins - 公式ドキュメント](https://docs.claude.com/en/docs/claude-code/plugins)
- [ai_development_tools リポジトリ](https://github.com/xtone/ai_development_tools)
