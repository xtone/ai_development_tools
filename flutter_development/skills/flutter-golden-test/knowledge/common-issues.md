# よくある問題と解決方法

## 1. フォントが正しく表示されない

### 症状

Goldenファイルでテキストが「□」や空白で表示される。

### 原因

テスト環境でフォントがロードされていない。

### 解決策

`test/flutter_test_config.dart` でフォントをロードする:

```dart
Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  TestWidgetsFlutterBinding.ensureInitialized();

  // フォントをロード
  final fontLoader = FontLoader('Noto Sans JP')
    ..addFont(_loadFontData('assets/fonts/NotoSansJP-Regular.ttf'));
  await fontLoader.load();

  await testMain();
}

Future<ByteData> _loadFontData(String path) async {
  final file = File(path);
  final bytes = await file.readAsBytes();
  return ByteData.view(bytes.buffer);
}
```

## 2. CI環境とローカル環境でGoldenが一致しない

### 症状

ローカルでは成功するがCIで失敗する。または逆。

### 原因

- OS間でのフォントレンダリングの違い
- devicePixelRatioの違い
- 画面サイズの違い

### 解決策

1. **devicePixelRatioを固定**:
```dart
view.devicePixelRatio = 1.0;
```

2. **画面サイズを明示的に設定**:
```dart
await binding.setSurfaceSize(const Size(400, 100));
view.physicalSize = const Size(400, 100);
```

3. **CI環境でGoldenを生成**:
```bash
# CI環境でのみGoldenを更新
flutter test --update-goldens
```

4. **Docker/Containerを使用**:
ローカルでもCIと同じ環境でテストを実行。

## 3. Goldenファイルの更新を忘れる

### 症状

UIを変更したのにGoldenファイルを更新せず、テストが失敗し続ける。

### 解決策

1. **CIでGolden更新を禁止**:
CI環境では `--update-goldens` を使用しない。

2. **PR時にGoldenファイルの差分を確認**:
画像の差分を視覚的に確認できるツールを導入。

3. **チェックリストに追加**:
UI変更時にGolden更新をチェックリストに含める。

## 4. テストが遅い

### 症状

Golden Testの実行に時間がかかる。

### 原因

- 画像の比較に時間がかかる
- ウィジェットのビルドに時間がかかる

### 解決策

1. **必要な状態のみテスト**:
すべての状態をテストするのではなく、重要な状態のみをテスト。

2. **並列実行**:
```bash
flutter test --concurrency=4
```

3. **適切なサイズを使用**:
コンポーネントには小さいサイズを使用。

## 5. 画面サイズが正しく設定されない

### 症状

設定したサイズと異なるGoldenファイルが生成される。

### 解決策

`setSurfaceSize` と `physicalSize` の両方を設定:

```dart
await binding.setSurfaceSize(surfaceSize);
view.physicalSize = surfaceSize;
view.devicePixelRatio = 1.0;
```

テスト後にクリーンアップ:
```dart
await binding.setSurfaceSize(null);
```

## 6. アニメーションが途中で止まる

### 症状

アニメーションが完了していない状態でGoldenが取得される。

### 解決策

1. **アニメーションを完了させる**:
```dart
await tester.pumpAndSettle();
```

2. **特定のフレームでキャプチャ**:
```dart
await tester.pump(const Duration(milliseconds: 500));
```

## 7. debugShowCheckedModeBannerが表示される

### 症状

Goldenファイルに「DEBUG」バナーが表示される。

### 解決策

MaterialAppで無効化:
```dart
MaterialApp(
  debugShowCheckedModeBanner: false,
  // ...
)
```

## 8. 非同期処理の結果が反映されない

### 症状

APIからのデータ取得後の状態がテストできない。

### 解決策

1. **モックを使用**:
```dart
await tester.pumpGoldenWidgetWithRiverpod(
  const MyScreen(),
  overrides: [
    dataProvider.overrideWith((ref) => AsyncData(mockData)),
  ],
);
```

2. **適切な待機**:
```dart
await tester.pumpAndSettle();
```

## 9. OverflowErrorが発生する

### 症状

RenderFlexが「overflowed」というエラーを出す。

### 解決策

テストサイズを大きくする:
```dart
await tester.pumpGoldenWidget(
  widget,
  surfaceSize: const Size(400, 200), // 高さを増やす
);
```

## 10. 画像が表示されない

### 症状

`Image.asset()` や `Image.network()` が表示されない。

### 解決策

1. **アセット画像の場合**:
アセットがテスト環境で読み込めることを確認。

2. **ネットワーク画像の場合**:
モックを使用:
```dart
// HttpClientをモック
```

3. **プレースホルダーを使用**:
テスト用にプレースホルダー画像を表示。

## トラブルシューティングチェックリスト

1. [ ] `flutter_test_config.dart` でフォントをロードしているか
2. [ ] `devicePixelRatio = 1.0` を設定しているか
3. [ ] `debugShowCheckedModeBanner = false` を設定しているか
4. [ ] テスト後に `cleanUpGoldenTest()` を呼んでいるか
5. [ ] 適切なサイズを設定しているか
6. [ ] CIとローカルで同じ環境を使用しているか
