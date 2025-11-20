# Android Test Runner

Android テスト実行を自動化し、テスト失敗を分析し、実行可能な修正提案を提供する Claude Code スキルです。

**Version**: v1.0 (汎用版)

---

## 🎯 機能

- **テスト実行の自動化**: Unit test、Instrumentation test を Claude Code から直接実行
- **インテリジェントな失敗分析**: テスト失敗の根本原因を自動的に特定
- **修正提案**: コード例付きの具体的で実行可能な修正提案を提供
- **Multi-Variant対応**: 複数のビルドバリアントを持つ複雑なAndroidプロジェクトに対応
- **パターン認識**: 19以上の一般的なテスト失敗パターンに対応

---

## 📦 インストール

### Claude Code での使用

1. このスキルをプロジェクトにコピー:
   ```bash
   cp -r android-test-runner /path/to/your-project/.claude/skills/
   ```

2. またはパーソナルスキルディレクトリにリンク:
   ```bash
   ln -s /path/to/android-test-runner ~/.claude/skills/android-test-runner
   ```

3. Claude Code を再起動（既に実行中の場合）

---

## 🚀 使い方

自然言語でテスト実行をリクエストするだけです:

```
すべてのunit testを実行して
```

```
BrowsingHistoryTestを実行して結果を分析して
```

```
UserRepositoryのテストを実行して
```

このスキルは自動的に:
1. プロジェクト構造を検出（ビルドバリアント、テストタスク）
2. 適切な Gradle コマンドを実行
3. テスト結果を分析
4. 失敗に対する修正提案を提供

---

## 📚 サポートされているパターン

### テスト実行
- 標準的な unit test (`./gradlew test`)
- Multi-variant プロジェクト（バリアント固有のタスク）
- Instrumentation test (`connectedAndroidTest`)
- 特定のテストクラス/メソッド

### 失敗分析
- Pattern 1-10: 一般的なテスト失敗（NullPointer, MockK, Assertions等）
- Pattern 11-16: Multi-variant プロジェクト固有の問題
- Pattern 17-19: 高度なパターン（Compose UI, BuildType, Flow）

詳細は `knowledge/test-failure-patterns.md` を参照してください。

---

## 🔧 設定

### 前提条件

- JBR（Java Runtime）を含むAndroid Studio
- テストタスクを持つGradleプロジェクト
- Claude Code がインストール済み

### 環境セットアップ

このスキルは以下を自動的に処理します:
- `JAVA_HOME` 設定
- ビルドバリアント検出
- テストタスク選択

---

## 📖 ドキュメント

- `SKILL.md`: 完全なスキル実装ガイド
- `knowledge/test-failure-patterns.md`: 19の失敗パターンと修正方法
- `knowledge/project-template.md`: プロジェクトに合わせてカスタマイズ
- `templates/fix-suggestions.md`: 修正提案テンプレート

---

## 🎨 カスタマイズ

### プロジェクト固有版の作成

最大の精度を得るために、プロジェクト固有版を作成してください:

1. このスキルをプロジェクトルートにコピー:
   ```bash
   cp -r android-test-runner your-project/.claude/skills/
   ```

2. `knowledge/project-template.md` をカスタマイズ:
   - ビルドバリアントを追加
   - テストライブラリを文書化（Truth, Turbine等）
   - プロジェクト固有のパターンを追加

**理由**: プロジェクト固有の情報により精度が約80%から98%に向上します。

詳細は `~/.config/claude-code/AI_DEVELOPMENT_GUIDELINES.md` を参照してください。

---

## 🤝 コントリビューション

これは android-test-runner の汎用版です。プロジェクト固有の改善は:

1. プロジェクト固有版で開発
2. 公開用に汎用化
3. このリポジトリにPRとして送信

---

## 📊 成功指標

- ✅ 失敗の根本原因を70%以上の精度で特定
- ✅ デバッグ時間を30%以上削減
- ✅ 具体的で実行可能な修正提案を提供

---

## 📝 バージョン履歴

### v1.0 (2025-11-20) - 汎用版リリース
- Pattern 1-19 を実装
- Multi-variant サポート
- JAVA_HOME 自動設定
- Quick Reference 追加
- すべての説明を日本語で記述（視認性・メンテナンス性向上）

---

## 📄 License

MIT License

---

**Maintainer**: 石原正也
**Repository**: https://github.com/xtone/ai_development_tools
