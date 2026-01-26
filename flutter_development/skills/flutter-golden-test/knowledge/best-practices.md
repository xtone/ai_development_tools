# Golden Test ベストプラクティス

## 1. 環境設定

### devicePixelRatio = 1.0 を設定する理由

```dart
view.devicePixelRatio = 1.0;
```

**理由:**
- 異なるデバイスやCI環境でも一貫した結果を得るため
- 高DPIディスプレイ（Retinaなど）の影響を排除
- ファイルサイズを抑制（2x、3xの画像を生成しない）

### debugShowCheckedModeBanner = false の重要性

```dart
MaterialApp(
  debugShowCheckedModeBanner: false,
  // ...
)
```

**理由:**
- DEBUGバナーがGoldenに含まれると、リリースビルドとの比較が困難
- バナーの位置やサイズが環境で異なる可能性

## 2. 命名規則

### ファイル名（snake_case）

```
test/
└── ui/
    └── components/
        └── primary_button_golden_test.dart  ✅
        └── PrimaryButton_golden_test.dart   ❌
```

### 状態名（snake_case）

```dart
// 良い例
GoldenFilePath.component('primary_button', 'enabled')
GoldenFilePath.component('primary_button', 'with_icon')
GoldenFilePath.component('primary_button', 'long_text')

// 悪い例
GoldenFilePath.component('primary_button', 'Enabled')
GoldenFilePath.component('primary_button', 'withIcon')
```

### 一般的な状態名

| 状態 | 命名 |
|-----|------|
| 有効状態 | `enabled` |
| 無効状態 | `disabled` |
| 選択状態 | `selected` |
| 未選択状態 | `unselected` |
| フォーカス状態 | `focused` |
| エラー状態 | `error` |
| ローディング | `loading` |
| 空状態 | `empty` |
| 全状態比較 | `all_states` |
| アイコン付き | `with_icon` |
| 長いテキスト | `long_text` |

## 3. テスト状態の設計

### 重要な状態を特定する

すべての状態をテストするのではなく、重要な状態を選ぶ:

1. **デフォルト状態**: 最も一般的な使用方法
2. **エッジケース**: 長いテキスト、空の入力など
3. **インタラクション状態**: 有効/無効、フォーカスなど
4. **エラー状態**: バリデーションエラーなど

### all_states テストの活用

複数の状態を一覧で比較することで、変更の影響を俯瞰できる:

```dart
testWidgets('全状態の比較', (tester) async {
  await tester.pumpGoldenWidgetList([
    // 各状態を列挙
  ]);

  await expectLater(
    find.byType(MaterialApp),
    matchesGoldenFile(GoldenFilePath.component('button', 'all_states')),
  );
});
```

## 4. ディレクトリ構造

### 推奨構造

```
test/
├── flutter_test_config.dart          # グローバル設定
├── helpers/
│   ├── helpers.dart                  # バレルファイル
│   └── golden_test_helper.dart       # ヘルパー
├── mocks/                            # モック定義
│   └── mock_providers.dart
└── ui/
    ├── core/
    │   └── components/
    │       ├── primary_button_golden_test.dart
    │       └── goldens/
    │           └── components/
    │               └── primary_button/
    │                   ├── enabled.png
    │                   └── disabled.png
    └── features/
        └── login/
            ├── login_screen_golden_test.dart
            └── goldens/
                └── screens/
                    └── login_screen/
                        ├── initial.png
                        └── loading.png
```

### Goldenファイルをテストファイルの近くに配置

- 関連するテストとGoldenが近くにあると管理しやすい
- PRレビュー時に変更の影響を把握しやすい

## 5. テストの書き方

### 1テストケース1状態

```dart
// 良い例: 1テストケースで1状態をテスト
testWidgets('有効状態', (tester) async {
  await tester.pumpGoldenWidget(Button(enabled: true));
  // ...
});

testWidgets('無効状態', (tester) async {
  await tester.pumpGoldenWidget(Button(enabled: false));
  // ...
});

// 悪い例: 複数の状態を1テストで検証
testWidgets('有効/無効状態', (tester) async {
  await tester.pumpGoldenWidget(Button(enabled: true));
  await expectLater(...);

  await tester.pumpGoldenWidget(Button(enabled: false));
  await expectLater(...);
});
```

### クリーンアップを忘れない

```dart
testWidgets('状態テスト', (tester) async {
  await tester.pumpGoldenWidget(widget);
  await expectLater(...);

  await tester.cleanUpGoldenTest();  // 必須！
});
```

## 6. CI/CD統合

### Goldenファイルの更新フロー

1. **ローカルで変更を確認**
2. **CI環境でGoldenを更新**（環境差異を避けるため）
3. **PRでGoldenファイルの差分をレビュー**
4. **マージ後に自動テスト**

### CIでの実行コマンド

```bash
# テスト実行（検証のみ）
flutter test

# Goldenファイル更新（特定のブランチのみ）
flutter test --update-goldens
```

## 7. パフォーマンス

### テスト速度の最適化

1. **並列実行**:
```bash
flutter test --concurrency=4
```

2. **適切なサイズ**:
コンポーネントには小さいサイズを使用。

3. **必要なテストのみ**:
すべてのバリエーションをテストしない。

### テストの分類

Goldenテストにタグを付けて、必要に応じて実行:

```dart
@Tags(['golden'])
void main() {
  // ...
}
```

```bash
# Goldenテストのみ実行
flutter test --tags golden

# Goldenテストを除外
flutter test --exclude-tags golden
```

## 8. レビューのポイント

### Goldenファイル変更時の確認事項

1. **意図した変更か**: UIの変更が期待通りか
2. **影響範囲**: 他のGoldenに影響がないか
3. **一貫性**: 他のコンポーネントとの整合性
4. **アクセシビリティ**: コントラスト、サイズは適切か

### PRでのGolden差分の可視化

GitHubやGitLabでは画像の差分を表示できる。
差分を視覚的に確認してレビュー。

## 9. メンテナンス

### 不要なGoldenの削除

コンポーネントを削除した場合、Goldenファイルも削除:

```bash
# 未使用のGoldenを検出（手動確認）
find test -name "*.png" | while read f; do
  grep -q "$(basename $f .png)" test/**/*_test.dart || echo "$f"
done
```

### 定期的な見直し

- 四半期ごとにGoldenテストを見直し
- 不要なテストを削除
- 新しいコンポーネントにテストを追加

## 10. アンチパターン

### 避けるべきこと

1. **すべての状態をテストする**: 重要な状態のみに絞る
2. **実装詳細をテストする**: 見た目の変更のみを検証
3. **CIと異なる環境でGoldenを更新**: 環境差異で失敗する
4. **テスト後のクリーンアップを忘れる**: 次のテストに影響
5. **アニメーション途中でキャプチャ**: 不安定なテストになる
