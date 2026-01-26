# Golden Testの基礎知識

## Golden Testとは

Golden Test（ゴールデンテスト）は、UIの視覚的な変更を検出するためのテスト手法です。
「Golden」は「正解」「基準」を意味し、事前に保存した正解画像（Goldenファイル）と現在の表示を比較します。

別名:
- Visual Regression Test（視覚的回帰テスト）
- Snapshot Test（スナップショットテスト）
- Screenshot Test（スクリーンショットテスト）

## なぜGolden Testが必要か

### 1. 意図しないUI変更の検出

コードの変更が予期しないUIの変化を引き起こすことがあります：
- スタイルの変更（パディング、マージン、色など）
- レイアウトの崩れ
- フォントサイズの変更
- アイコンの変更

Golden Testは、これらの変更を自動的に検出します。

### 2. リファクタリングの安全性

コンポーネントのリファクタリング時に、見た目が変わっていないことを保証できます。

### 3. デザインシステムの一貫性

複数の開発者が同じコンポーネントを使用する際、一貫した見た目を維持できます。

### 4. ドキュメントとしての役割

Goldenファイルは、コンポーネントの各状態を視覚的に記録します。
新しいチームメンバーがUIの期待される見た目を理解するのに役立ちます。

## FlutterでのGolden Testの仕組み

### 基本的な流れ

1. **ウィジェットのレンダリング**: `tester.pumpWidget()` でウィジェットを描画
2. **スクリーンショットの取得**: `matchesGoldenFile()` で画像を取得
3. **比較**: 既存のGoldenファイルと比較（なければ新規作成）
4. **結果**: 一致すればパス、不一致ならフェイル

### 主要なAPI

```dart
// Goldenファイルと比較
await expectLater(
  find.byType(MyWidget),
  matchesGoldenFile('path/to/golden.png'),
);
```

### Goldenファイルの管理

- **生成/更新**: `flutter test --update-goldens`
- **検証**: `flutter test`

## Goldenファイルの保存場所

Flutterでは、Goldenファイルは **テストファイルからの相対パス** で保存されます。

```
test/
├── widgets/
│   ├── my_button_test.dart
│   └── goldens/
│       └── components/
│           └── my_button/
│               ├── enabled.png
│               └── disabled.png
```

テストコード内での指定:
```dart
matchesGoldenFile('goldens/components/my_button/enabled.png')
```

## Golden Testの種類

### 1. コンポーネントテスト

個々のウィジェット（ボタン、カード、入力フィールドなど）をテスト。
- 小さいサイズ（400x100程度）
- 各状態を個別にテスト

### 2. 画面テスト

画面全体をテスト。
- 実際のデバイスサイズ（iPhone SE、iPhone 14など）
- ローディング、エラー、データ表示などの状態をテスト

### 3. レスポンシブテスト

複数のデバイスサイズで画面をテスト。
- 小画面、中画面、大画面
- レイアウトの崩れを検出

## Golden Test vs ユニットテスト vs ウィジェットテスト

| 種類 | 対象 | 速度 | 目的 |
|-----|------|------|------|
| ユニットテスト | ロジック | 高速 | 関数の動作検証 |
| ウィジェットテスト | ウィジェット | 中速 | インタラクション検証 |
| Golden Test | 見た目 | 低速 | 視覚的変更検出 |

Golden Testは他のテストを **補完** するものであり、置き換えるものではありません。

## CI/CD環境での考慮事項

### 環境差異の問題

異なるOS（macOS、Linux、Windows）では、フォントレンダリングが異なる場合があります。
これにより、同じコードでもGoldenファイルが一致しないことがあります。

### 解決策

1. **CIと同じ環境でGoldenファイルを生成**: CI環境でのみGoldenを更新
2. **フォントの固定**: プロジェクトにフォントを含め、`flutter_test_config.dart` でロード
3. **devicePixelRatioの固定**: `1.0` に固定して一貫性を確保

## 参考リンク

- [Flutter公式ドキュメント - Testing](https://docs.flutter.dev/testing)
- [matchesGoldenFile API](https://api.flutter.dev/flutter/flutter_test/matchesGoldenFile.html)
