# flutter_test_config.dart テンプレート

## 概要

`test/flutter_test_config.dart` に配置するグローバルテスト設定ファイル。
全てのテストの前に自動的に実行され、フォントのロードなどを行う。

## プレースホルダー

| プレースホルダー | 説明 | 例 |
|-----------------|------|-----|
| `{FONT_FAMILY}` | フォントファミリー名 | `Noto Sans JP` |
| `{FONT_LOADERS}` | フォントローダーの列挙 | 下記参照 |

### FONT_LOADERS の例

```dart
..addFont(_loadFontData('assets/fonts/NotoSansJP-Regular.ttf'))
..addFont(_loadFontData('assets/fonts/NotoSansJP-Medium.ttf'))
..addFont(_loadFontData('assets/fonts/NotoSansJP-Bold.ttf'))
```

## テンプレート

```dart
import 'dart:async';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// グローバルテスト設定
/// このファイルはtestディレクトリ直下に配置することで、
/// 全てのテストの前に自動的に実行されます。
Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  TestWidgetsFlutterBinding.ensureInitialized();

  // フォントをロード
  await _loadFonts();

  // テスト実行
  await testMain();
}

/// {FONT_FAMILY}フォントをロードする
Future<void> _loadFonts() async {
  final fontLoader = FontLoader('{FONT_FAMILY}')
    {FONT_LOADERS};
  await fontLoader.load();
}

/// フォントファイルをByteDataとして読み込む
Future<ByteData> _loadFontData(String path) async {
  final file = File(path);
  final bytes = await file.readAsBytes();
  return ByteData.view(bytes.buffer);
}
```

## フォント設定不要の場合

フォント設定が不要な場合は、シンプルな設定を使用：

```dart
import 'dart:async';

import 'package:flutter_test/flutter_test.dart';

/// グローバルテスト設定
Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  TestWidgetsFlutterBinding.ensureInitialized();
  await testMain();
}
```

## 複数フォントファミリーの場合

複数のフォントファミリーを使用する場合：

```dart
Future<void> _loadFonts() async {
  // 日本語フォント
  final notoSansJp = FontLoader('Noto Sans JP')
    ..addFont(_loadFontData('assets/fonts/NotoSansJP-Regular.ttf'))
    ..addFont(_loadFontData('assets/fonts/NotoSansJP-Bold.ttf'));

  // アイコンフォント
  final materialIcons = FontLoader('MaterialIcons')
    ..addFont(_loadFontData('assets/fonts/MaterialIcons-Regular.ttf'));

  await Future.wait([
    notoSansJp.load(),
    materialIcons.load(),
  ]);
}
```

## 注意事項

- このファイルは必ず `test/` ディレクトリ直下に配置する
- ファイル名は必ず `flutter_test_config.dart` にする
- `testExecutable` 関数名は変更しない（Flutterが自動的に呼び出す）
