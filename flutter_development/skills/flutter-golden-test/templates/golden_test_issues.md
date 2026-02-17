# golden_test_issues.md テンプレート

## 概要

`test/golden_test_issues.md` に配置する問題解決ログファイル。
Golden Testで発生した問題とその解決方法を記録し、プロジェクト固有のナレッジとして蓄積する。

## 目的

- 同じ問題が発生した際に素早く対応できる
- プロジェクト固有の注意点を明文化する
- チームメンバー間で知見を共有する

## テンプレート

```markdown
# Golden Test 問題解決ログ

このファイルはGolden Testで発生した問題と解決方法を記録します。
同じ問題が発生した場合は、このファイルを参照してください。

---

## 問題一覧

| 日付 | 問題 | 原因 | 対応済み |
|-----|------|------|---------|
| | | | |

---

## 詳細記録

<!-- 問題が発生したら、以下のテンプレートをコピーして追記 -->

<!--
## YYYY-MM-DD: 問題の概要

### 問題
問題の詳細な説明

### 原因
原因の説明

### 解決方法
1. 手順1
2. 手順2
3. 手順3

### 今後の注意点
- 注意点1
- 注意点2

### 関連ファイル
- path/to/file.dart
-->
```

## 記録例

```markdown
## 2024-01-15: 日本語テキストが文字化けする

### 問題
PrimaryButtonのGolden Testで、日本語テキスト「保存する」が□□□と表示される。

### 原因
flutter_test_config.dartでNoto Sans JPフォントをロードしていなかった。
プロジェクトはRobotoをデフォルトフォントとして使用しており、
実機ではOSがフォールバックするが、テスト環境ではフォールバックが機能しない。

### 解決方法
1. assets/fonts/にNoto Sans JPフォントを追加
2. pubspec.yamlにフォントを登録
3. flutter_test_config.dartでフォントをロード

```dart
final notoSansJp = FontLoader('Noto Sans JP')
  ..addFont(_loadFontData('assets/fonts/NotoSansJP-Regular.ttf'));
await notoSansJp.load();
```

### 今後の注意点
- 日本語を含むウィジェットのテストでは、必ず日本語対応フォントを設定する
- 新しいフォントを追加した場合は、flutter_test_config.dartも更新する

### 関連ファイル
- test/flutter_test_config.dart
- pubspec.yaml
```

## 使用方法

1. **問題発生時**: 問題の内容をAIアシスタントに伝える
2. **解決後**: AIアシスタントがこのファイルに記録を追加
3. **参照時**: 同様の問題が発生したら、このファイルを検索

## 注意事項

- 解決方法は具体的に、再現できるように記録する
- コード例がある場合は必ず含める
- 関連ファイルへのパスを明記する
- 機密情報（APIキーなど）は絶対に記録しない
