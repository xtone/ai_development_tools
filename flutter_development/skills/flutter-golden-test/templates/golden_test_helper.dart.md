# golden_test_helper.dart テンプレート

## 概要

`test/helpers/golden_test_helper.dart` に配置するGolden Test用ヘルパー。
画面サイズ定義、WidgetTester拡張、ファイルパスユーティリティを提供。

## プレースホルダー

| プレースホルダー | 説明 | デフォルト値 |
|-----------------|------|-------------|
| `{THEME_IMPORT}` | テーマのインポート文 | 空（デフォルトテーマ使用時） |
| `{DEFAULT_THEME}` | デフォルトテーマ | `ThemeData.light()` |
| `{COMPONENT_WIDTH}` | コンポーネントサイズ幅 | `400` |
| `{COMPONENT_HEIGHT}` | コンポーネントサイズ高さ | `100` |
| `{COMPONENT_LIST_WIDTH}` | コンポーネントリスト幅 | `400` |
| `{COMPONENT_LIST_HEIGHT}` | コンポーネントリスト高さ | `400` |
| `{SCREEN_SMALL_WIDTH}` | 小画面幅 | `375` |
| `{SCREEN_SMALL_HEIGHT}` | 小画面高さ | `667` |
| `{SCREEN_MEDIUM_WIDTH}` | 中画面幅 | `390` |
| `{SCREEN_MEDIUM_HEIGHT}` | 中画面高さ | `844` |
| `{SCREEN_LARGE_WIDTH}` | 大画面幅 | `430` |
| `{SCREEN_LARGE_HEIGHT}` | 大画面高さ | `932` |

## テンプレート

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
{THEME_IMPORT}

/// Golden Test用の画面サイズ定義
class GoldenTestSizes {
  GoldenTestSizes._();

  /// コンポーネント単体テスト用の小さなサイズ
  static const Size component = Size({COMPONENT_WIDTH}, {COMPONENT_HEIGHT});

  /// コンポーネントをリスト表示するテスト用のサイズ
  static const Size componentList = Size({COMPONENT_LIST_WIDTH}, {COMPONENT_LIST_HEIGHT});

  /// 画面全体のテスト用サイズ（iPhone SE相当）
  static const Size screenSmall = Size({SCREEN_SMALL_WIDTH}, {SCREEN_SMALL_HEIGHT});

  /// 画面全体のテスト用サイズ（iPhone 14相当）
  static const Size screenMedium = Size({SCREEN_MEDIUM_WIDTH}, {SCREEN_MEDIUM_HEIGHT});

  /// 画面全体のテスト用サイズ（iPhone 14 Pro Max相当）
  static const Size screenLarge = Size({SCREEN_LARGE_WIDTH}, {SCREEN_LARGE_HEIGHT});
}

/// Golden Test用のWidgetTester拡張
extension GoldenTestExtension on WidgetTester {
  /// Golden Test用のウィジェットをセットアップ
  ///
  /// [widget] テスト対象のウィジェット
  /// [surfaceSize] テスト画面サイズ（デフォルト: コンポーネントサイズ）
  /// [theme] 使用するテーマ（デフォルト: ライトテーマ）
  Future<void> pumpGoldenWidget(
    Widget widget, {
    Size surfaceSize = GoldenTestSizes.component,
    ThemeData? theme,
  }) async {
    await binding.setSurfaceSize(surfaceSize);
    view.physicalSize = surfaceSize;
    view.devicePixelRatio = 1.0;

    await pumpWidget(
      MaterialApp(
        theme: theme ?? {DEFAULT_THEME},
        debugShowCheckedModeBanner: false,
        home: Scaffold(
          body: Center(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: widget,
            ),
          ),
        ),
      ),
    );

    await pump();
  }

  /// Golden Test用のウィジェットリストをセットアップ
  ///
  /// 複数の状態を一度にキャプチャする場合に使用
  Future<void> pumpGoldenWidgetList(
    List<Widget> widgets, {
    Size surfaceSize = GoldenTestSizes.componentList,
    ThemeData? theme,
  }) async {
    await binding.setSurfaceSize(surfaceSize);
    view.physicalSize = surfaceSize;
    view.devicePixelRatio = 1.0;

    await pumpWidget(
      MaterialApp(
        theme: theme ?? {DEFAULT_THEME},
        debugShowCheckedModeBanner: false,
        home: Scaffold(
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: widgets
                  .map(
                    (w) => Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: w,
                    ),
                  )
                  .toList(),
            ),
          ),
        ),
      ),
    );

    await pump();
  }

  /// テスト後のクリーンアップ
  Future<void> cleanUpGoldenTest() async {
    await binding.setSurfaceSize(null);
  }
}

/// Golden Testのファイルパスを生成するユーティリティ
class GoldenFilePath {
  GoldenFilePath._();

  /// コンポーネントのGoldenファイルパスを生成
  ///
  /// 例: `goldens/components/custom_text_form_field/normal.png`
  static String component(String componentName, String stateName) {
    return 'goldens/components/$componentName/$stateName.png';
  }

  /// 画面のGoldenファイルパスを生成
  ///
  /// 例: `goldens/screens/login_screen/initial.png`
  static String screen(String screenName, String stateName) {
    return 'goldens/screens/$screenName/$stateName.png';
  }
}
```

## カスタムテーマ使用時の例

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/ui/core/themes/theme.dart';

// ... 上記テンプレートと同様 ...
// {DEFAULT_THEME} を AppTheme.light() に置換
```

## 注意事項

- `devicePixelRatio = 1.0` は必須（異なる環境でのスクリーンショット一貫性のため）
- `debugShowCheckedModeBanner = false` でデバッグバナーを非表示
- テスト後は必ず `cleanUpGoldenTest()` を呼び出す
