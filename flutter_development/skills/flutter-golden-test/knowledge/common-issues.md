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
モックを使用（詳細は「11. ネットワーク画像の対応」を参照）

3. **プレースホルダーを使用**:
テスト用にプレースホルダー画像を表示。

## 11. ネットワーク画像の対応

### 症状

`Image.network()` や `CachedNetworkImage` を使用しているウィジェットで、画像が表示されない、またはエラーになる。

### 原因

Golden Testはネットワーク通信を行わないため、ネットワーク画像は取得できない。

### 解決策

#### 方法1: ダミー画像ウィジェットで置き換え（推奨）

テスト用のラッパーウィジェットを作成し、テスト時はダミー画像を表示:

```dart
// lib/ui/core/widgets/network_image_wrapper.dart
import 'package:flutter/material.dart';

class NetworkImageWrapper extends StatelessWidget {
  final String imageUrl;
  final double? width;
  final double? height;
  final BoxFit? fit;

  const NetworkImageWrapper({
    super.key,
    required this.imageUrl,
    this.width,
    this.height,
    this.fit,
  });

  @override
  Widget build(BuildContext context) {
    return Image.network(
      imageUrl,
      width: width,
      height: height,
      fit: fit,
      // エラー時のフォールバック
      errorBuilder: (context, error, stackTrace) {
        return _buildPlaceholder();
      },
      // ロード中の表示
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) return child;
        return _buildPlaceholder();
      },
    );
  }

  Widget _buildPlaceholder() {
    return Container(
      width: width,
      height: height,
      color: Colors.grey[300],
      child: const Icon(Icons.image, color: Colors.grey),
    );
  }
}
```

#### 方法2: mocktail/mockitoでHttpClientをモック

```dart
// test/mocks/mock_http_client.dart
import 'dart:io';
import 'package:mocktail/mocktail.dart';

class MockHttpClient extends Mock implements HttpClient {}
class MockHttpClientRequest extends Mock implements HttpClientRequest {}
class MockHttpClientResponse extends Mock implements HttpClientResponse {}

// テストで使用
void main() {
  setUpAll(() {
    // HttpClientをモック
    HttpOverrides.global = MockHttpOverrides();
  });
}

class MockHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return MockHttpClient();
  }
}
```

#### 方法3: CachedNetworkImageの場合

`cached_network_image` パッケージを使用している場合:

```dart
// テスト用のモックプロバイダー
testWidgets('画像表示テスト', (tester) async {
  await tester.pumpGoldenWidgetWithRiverpod(
    MyWidget(),
    overrides: [
      // 画像URLをローカルアセットに置き換え
      imageUrlProvider.overrideWithValue('assets/test/dummy_image.png'),
    ],
  );
});
```

### ベストプラクティス

1. **本番コードの変更を最小限に**: テスト用のモックを使用し、本番コードには影響を与えない
2. **プレースホルダーの一貫性**: ダミー画像は常に同じ見た目にする（Goldenの安定性のため）
3. **サイズを固定**: 画像のサイズは明示的に指定する

## 12. 日本語フォントの問題（フォールバック）

### 症状

- 日本語テキストが「□□□」や空白で表示される
- 実機では正しく表示されるが、Golden Testでは文字化けする

### 原因

プロジェクトのデフォルトフォント（例: Roboto）が日本語に対応していない場合、
実機ではOSが自動的に日本語フォントにフォールバックするが、
テスト環境ではこのフォールバックが機能しない。

### 解決策

#### Step 1: 日本語対応フォントを追加

```yaml
# pubspec.yaml
flutter:
  fonts:
    - family: NotoSansJP
      fonts:
        - asset: assets/fonts/NotoSansJP-Regular.ttf
        - asset: assets/fonts/NotoSansJP-Medium.ttf
          weight: 500
        - asset: assets/fonts/NotoSansJP-Bold.ttf
          weight: 700
```

#### Step 2: flutter_test_config.dartでフォントをロード

```dart
Future<void> _loadFonts() async {
  final notoSansJp = FontLoader('NotoSansJP')
    ..addFont(_loadFontData('assets/fonts/NotoSansJP-Regular.ttf'))
    ..addFont(_loadFontData('assets/fonts/NotoSansJP-Medium.ttf'))
    ..addFont(_loadFontData('assets/fonts/NotoSansJP-Bold.ttf'));
  await notoSansJp.load();
}
```

#### Step 3: テーマでフォントを指定

```dart
// テスト用のテーマ
ThemeData testTheme = ThemeData(
  fontFamily: 'NotoSansJP',
  // ...
);

// golden_test_helper.dart で使用
await tester.pumpGoldenWidget(
  widget,
  theme: testTheme,
);
```

### 日本語非対応フォントの例

以下のフォントは日本語に対応していないため注意:

| フォント | 対応言語 | 備考 |
|---------|---------|------|
| Roboto | ラテン文字 | Material Designデフォルト |
| Open Sans | ラテン文字 | |
| Lato | ラテン文字 | |
| Montserrat | ラテン文字 | |

### 日本語対応フォントの例

| フォント | 特徴 | 推奨用途 |
|---------|------|---------|
| Noto Sans JP | Google製、可読性高い | 一般的なUI |
| BIZ UDGothic | 視認性重視 | 業務アプリ |
| M PLUS 1p | モダンなデザイン | デザイン重視 |
| Kosugi Maru | 丸ゴシック | カジュアルなアプリ |

### フォント設定のチェック方法

テスト実行前に、フォント設定が正しいか確認:

```dart
// デバッグ用: 現在ロードされているフォントを確認
debugPrint('Loaded fonts: ${fontLoader.fontFamily}');
```

## トラブルシューティングチェックリスト

1. [ ] `flutter_test_config.dart` でフォントをロードしているか
2. [ ] `devicePixelRatio = 1.0` を設定しているか
3. [ ] `debugShowCheckedModeBanner = false` を設定しているか
4. [ ] テスト後に `cleanUpGoldenTest()` を呼んでいるか
5. [ ] 適切なサイズを設定しているか
6. [ ] CIとローカルで同じ環境を使用しているか
7. [ ] 日本語テキストに対応したフォントを使用しているか
8. [ ] ネットワーク画像をモックまたはダミーに置き換えているか
9. [ ] 問題が発生したら `test/golden_test_issues.md` に記録しているか
