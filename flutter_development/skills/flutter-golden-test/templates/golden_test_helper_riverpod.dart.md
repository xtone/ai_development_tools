# golden_test_helper_riverpod.dart テンプレート

## 概要

Riverpodを使用するプロジェクト向けのGolden Testヘルパー。
`ProviderScope` でラップし、モックプロバイダーのオーバーライドをサポート。

## 標準ヘルパーからの追加点

- `pumpGoldenWidgetWithRiverpod` メソッド
- `pumpGoldenScreenWithRiverpod` メソッド
- `overrides` パラメータでモックプロバイダーを注入可能

## テンプレート（Riverpod対応追加部分）

以下を `golden_test_helper.dart` に追加するか、別ファイルとして作成：

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
{THEME_IMPORT}

/// Golden Test用のWidgetTester拡張（Riverpod対応）
extension GoldenTestRiverpodExtension on WidgetTester {
  /// Riverpod対応のGolden Testウィジェットセットアップ
  ///
  /// [widget] テスト対象のウィジェット
  /// [overrides] プロバイダーのオーバーライド（モック用）
  /// [surfaceSize] テスト画面サイズ
  /// [theme] 使用するテーマ
  Future<void> pumpGoldenWidgetWithRiverpod(
    Widget widget, {
    List<Override> overrides = const [],
    Size surfaceSize = GoldenTestSizes.component,
    ThemeData? theme,
  }) async {
    await binding.setSurfaceSize(surfaceSize);
    view.physicalSize = surfaceSize;
    view.devicePixelRatio = 1.0;

    await pumpWidget(
      ProviderScope(
        overrides: overrides,
        child: MaterialApp(
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
      ),
    );

    await pump();
  }

  /// Riverpod対応の画面Golden Testセットアップ
  ///
  /// 画面全体をテストする場合に使用
  Future<void> pumpGoldenScreenWithRiverpod(
    Widget screen, {
    List<Override> overrides = const [],
    Size surfaceSize = GoldenTestSizes.screenMedium,
    ThemeData? theme,
  }) async {
    await binding.setSurfaceSize(surfaceSize);
    view.physicalSize = surfaceSize;
    view.devicePixelRatio = 1.0;

    await pumpWidget(
      ProviderScope(
        overrides: overrides,
        child: MaterialApp(
          theme: theme ?? {DEFAULT_THEME},
          debugShowCheckedModeBanner: false,
          home: screen,
        ),
      ),
    );

    await pump();
  }

  /// Riverpod対応のウィジェットリストセットアップ
  Future<void> pumpGoldenWidgetListWithRiverpod(
    List<Widget> widgets, {
    List<Override> overrides = const [],
    Size surfaceSize = GoldenTestSizes.componentList,
    ThemeData? theme,
  }) async {
    await binding.setSurfaceSize(surfaceSize);
    view.physicalSize = surfaceSize;
    view.devicePixelRatio = 1.0;

    await pumpWidget(
      ProviderScope(
        overrides: overrides,
        child: MaterialApp(
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
      ),
    );

    await pump();
  }
}
```

## 使用例

### 基本的な使用

```dart
testWidgets('ログイン画面の表示', (tester) async {
  await tester.pumpGoldenScreenWithRiverpod(
    const LoginScreen(),
    surfaceSize: GoldenTestSizes.screenMedium,
  );

  await expectLater(
    find.byType(LoginScreen),
    matchesGoldenFile(GoldenFilePath.screen('login_screen', 'initial')),
  );

  await tester.cleanUpGoldenTest();
});
```

### モックプロバイダーを使用

```dart
testWidgets('ログイン済み状態の表示', (tester) async {
  await tester.pumpGoldenScreenWithRiverpod(
    const HomeScreen(),
    overrides: [
      // ユーザー認証状態をモック
      authStateProvider.overrideWith(
        (ref) => AuthState.authenticated(
          user: User(name: 'テストユーザー'),
        ),
      ),
    ],
    surfaceSize: GoldenTestSizes.screenMedium,
  );

  await expectLater(
    find.byType(HomeScreen),
    matchesGoldenFile(GoldenFilePath.screen('home_screen', 'authenticated')),
  );

  await tester.cleanUpGoldenTest();
});
```

### 複数の状態をテスト

```dart
testWidgets('ユーザーカード全状態', (tester) async {
  await tester.pumpGoldenWidgetListWithRiverpod(
    [
      const UserCard(user: User(name: 'ユーザーA', isPremium: false)),
      const UserCard(user: User(name: 'ユーザーB', isPremium: true)),
      const UserCard(user: null), // 未ログイン状態
    ],
    overrides: [
      // 必要に応じてプロバイダーをオーバーライド
    ],
  );

  await expectLater(
    find.byType(MaterialApp),
    matchesGoldenFile(GoldenFilePath.component('user_card', 'all_states')),
  );

  await tester.cleanUpGoldenTest();
});
```

## 統合版テンプレート

標準ヘルパーとRiverpod対応を1ファイルにまとめる場合：

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
{THEME_IMPORT}

/// Golden Test用の画面サイズ定義
class GoldenTestSizes {
  GoldenTestSizes._();

  static const Size component = Size(400, 100);
  static const Size componentList = Size(400, 400);
  static const Size screenSmall = Size(375, 667);
  static const Size screenMedium = Size(390, 844);
  static const Size screenLarge = Size(430, 932);
}

/// Golden Test用のWidgetTester拡張
extension GoldenTestExtension on WidgetTester {
  // 標準メソッド（Riverpodなし）
  Future<void> pumpGoldenWidget(
    Widget widget, {
    Size surfaceSize = GoldenTestSizes.component,
    ThemeData? theme,
  }) async {
    // ... 標準実装 ...
  }

  // Riverpod対応メソッド
  Future<void> pumpGoldenWidgetWithRiverpod(
    Widget widget, {
    List<Override> overrides = const [],
    Size surfaceSize = GoldenTestSizes.component,
    ThemeData? theme,
  }) async {
    // ... Riverpod実装 ...
  }

  Future<void> cleanUpGoldenTest() async {
    await binding.setSurfaceSize(null);
  }
}

/// Golden Testのファイルパスを生成するユーティリティ
class GoldenFilePath {
  GoldenFilePath._();

  static String component(String componentName, String stateName) {
    return 'goldens/components/$componentName/$stateName.png';
  }

  static String screen(String screenName, String stateName) {
    return 'goldens/screens/$screenName/$stateName.png';
  }
}
```

## 注意事項

- `flutter_riverpod` パッケージが `dev_dependencies` に必要
- `Override` 型は `flutter_riverpod` から提供される
- テスト用のモックプロバイダーは別ファイルで定義することを推奨
