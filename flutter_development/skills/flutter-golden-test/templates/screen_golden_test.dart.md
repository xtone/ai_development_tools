# screen_golden_test.dart テンプレート

## 概要

画面（Screen、Page）のGolden Testテンプレート。
複数の画面サイズと状態でテストし、レスポンシブ対応も検証。

## プレースホルダー

| プレースホルダー | 説明 | 例 |
|-----------------|------|-----|
| `{SCREEN_IMPORT}` | 画面のインポートパス | `package:your_app/ui/screens/login_screen.dart` |
| `{HELPER_IMPORT}` | ヘルパーのインポートパス | `../../helpers/golden_test_helper.dart` |
| `{SCREEN_NAME}` | 画面名（表示用） | `LoginScreen` |
| `{SCREEN_SNAKE_CASE}` | 画面名（snake_case） | `login_screen` |
| `{TEST_CASES}` | 各状態のテストケース | 下記参照 |
| `{USE_RIVERPOD}` | Riverpod使用有無 | `true` / `false` |

## 標準テンプレート（Riverpodなし）

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '{SCREEN_IMPORT}';

import '{HELPER_IMPORT}';

void main() {
  group('{SCREEN_NAME} Golden Tests', () {
    {TEST_CASES}

    group('レスポンシブ対応', () {
      testWidgets('iPhone SE（小画面）', (tester) async {
        await tester.pumpGoldenWidget(
          const {SCREEN_NAME}(),
          surfaceSize: GoldenTestSizes.screenSmall,
        );

        await expectLater(
          find.byType({SCREEN_NAME}),
          matchesGoldenFile(
            GoldenFilePath.screen('{SCREEN_SNAKE_CASE}', 'screen_small'),
          ),
        );

        await tester.cleanUpGoldenTest();
      });

      testWidgets('iPhone 14（中画面）', (tester) async {
        await tester.pumpGoldenWidget(
          const {SCREEN_NAME}(),
          surfaceSize: GoldenTestSizes.screenMedium,
        );

        await expectLater(
          find.byType({SCREEN_NAME}),
          matchesGoldenFile(
            GoldenFilePath.screen('{SCREEN_SNAKE_CASE}', 'screen_medium'),
          ),
        );

        await tester.cleanUpGoldenTest();
      });

      testWidgets('iPhone 14 Pro Max（大画面）', (tester) async {
        await tester.pumpGoldenWidget(
          const {SCREEN_NAME}(),
          surfaceSize: GoldenTestSizes.screenLarge,
        );

        await expectLater(
          find.byType({SCREEN_NAME}),
          matchesGoldenFile(
            GoldenFilePath.screen('{SCREEN_SNAKE_CASE}', 'screen_large'),
          ),
        );

        await tester.cleanUpGoldenTest();
      });
    });
  });
}
```

## Riverpod対応テンプレート

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import '{SCREEN_IMPORT}';
// モックプロバイダーがある場合
// import '../mocks/mock_providers.dart';

import '{HELPER_IMPORT}';

void main() {
  group('{SCREEN_NAME} Golden Tests', () {
    {TEST_CASES}

    group('レスポンシブ対応', () {
      testWidgets('iPhone SE（小画面）', (tester) async {
        await tester.pumpGoldenScreenWithRiverpod(
          const {SCREEN_NAME}(),
          overrides: [
            // 必要に応じてプロバイダーをオーバーライド
          ],
          surfaceSize: GoldenTestSizes.screenSmall,
        );

        await expectLater(
          find.byType({SCREEN_NAME}),
          matchesGoldenFile(
            GoldenFilePath.screen('{SCREEN_SNAKE_CASE}', 'screen_small'),
          ),
        );

        await tester.cleanUpGoldenTest();
      });

      testWidgets('iPhone 14（中画面）', (tester) async {
        await tester.pumpGoldenScreenWithRiverpod(
          const {SCREEN_NAME}(),
          overrides: [],
          surfaceSize: GoldenTestSizes.screenMedium,
        );

        await expectLater(
          find.byType({SCREEN_NAME}),
          matchesGoldenFile(
            GoldenFilePath.screen('{SCREEN_SNAKE_CASE}', 'screen_medium'),
          ),
        );

        await tester.cleanUpGoldenTest();
      });

      testWidgets('iPhone 14 Pro Max（大画面）', (tester) async {
        await tester.pumpGoldenScreenWithRiverpod(
          const {SCREEN_NAME}(),
          overrides: [],
          surfaceSize: GoldenTestSizes.screenLarge,
        );

        await expectLater(
          find.byType({SCREEN_NAME}),
          matchesGoldenFile(
            GoldenFilePath.screen('{SCREEN_SNAKE_CASE}', 'screen_large'),
          ),
        );

        await tester.cleanUpGoldenTest();
      });
    });
  });
}
```

## TEST_CASES の例

### ログイン画面の場合

```dart
    testWidgets('初期表示', (tester) async {
      await tester.pumpGoldenScreenWithRiverpod(
        const LoginScreen(),
        surfaceSize: GoldenTestSizes.screenMedium,
      );

      await expectLater(
        find.byType(LoginScreen),
        matchesGoldenFile(
          GoldenFilePath.screen('login_screen', 'initial'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('入力中', (tester) async {
      await tester.pumpGoldenScreenWithRiverpod(
        const LoginScreen(),
        surfaceSize: GoldenTestSizes.screenMedium,
      );

      // メールアドレス入力
      await tester.enterText(
        find.byKey(const Key('email_field')),
        'test@example.com',
      );
      await tester.pump();

      await expectLater(
        find.byType(LoginScreen),
        matchesGoldenFile(
          GoldenFilePath.screen('login_screen', 'with_email'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('バリデーションエラー', (tester) async {
      await tester.pumpGoldenScreenWithRiverpod(
        const LoginScreen(),
        overrides: [
          // エラー状態をモック
          loginFormStateProvider.overrideWith(
            (ref) => LoginFormState(
              emailError: 'メールアドレスを入力してください',
              passwordError: 'パスワードを入力してください',
            ),
          ),
        ],
        surfaceSize: GoldenTestSizes.screenMedium,
      );

      await expectLater(
        find.byType(LoginScreen),
        matchesGoldenFile(
          GoldenFilePath.screen('login_screen', 'validation_error'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('ローディング中', (tester) async {
      await tester.pumpGoldenScreenWithRiverpod(
        const LoginScreen(),
        overrides: [
          loginStateProvider.overrideWith(
            (ref) => const AsyncLoading(),
          ),
        ],
        surfaceSize: GoldenTestSizes.screenMedium,
      );

      await expectLater(
        find.byType(LoginScreen),
        matchesGoldenFile(
          GoldenFilePath.screen('login_screen', 'loading'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });
```

### 一覧画面の場合

```dart
    testWidgets('データなし', (tester) async {
      await tester.pumpGoldenScreenWithRiverpod(
        const ItemListScreen(),
        overrides: [
          itemListProvider.overrideWith((ref) => const AsyncData([])),
        ],
        surfaceSize: GoldenTestSizes.screenMedium,
      );

      await expectLater(
        find.byType(ItemListScreen),
        matchesGoldenFile(
          GoldenFilePath.screen('item_list_screen', 'empty'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('データあり', (tester) async {
      await tester.pumpGoldenScreenWithRiverpod(
        const ItemListScreen(),
        overrides: [
          itemListProvider.overrideWith(
            (ref) => AsyncData([
              Item(id: '1', name: 'アイテム1'),
              Item(id: '2', name: 'アイテム2'),
              Item(id: '3', name: 'アイテム3'),
            ]),
          ),
        ],
        surfaceSize: GoldenTestSizes.screenMedium,
      );

      await expectLater(
        find.byType(ItemListScreen),
        matchesGoldenFile(
          GoldenFilePath.screen('item_list_screen', 'with_items'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('エラー', (tester) async {
      await tester.pumpGoldenScreenWithRiverpod(
        const ItemListScreen(),
        overrides: [
          itemListProvider.overrideWith(
            (ref) => AsyncError(Exception('データの取得に失敗しました'), StackTrace.current),
          ),
        ],
        surfaceSize: GoldenTestSizes.screenMedium,
      );

      await expectLater(
        find.byType(ItemListScreen),
        matchesGoldenFile(
          GoldenFilePath.screen('item_list_screen', 'error'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });
```

## 生成されるGoldenファイル構造

```
test/ui/screens/login/goldens/
└── screens/
    └── login_screen/
        ├── initial.png
        ├── with_email.png
        ├── validation_error.png
        ├── loading.png
        ├── screen_small.png
        ├── screen_medium.png
        └── screen_large.png
```

## テスト実行コマンド

```bash
# Goldenファイルを生成/更新
flutter test --update-goldens test/ui/screens/login/login_screen_golden_test.dart

# テストを実行（検証）
flutter test test/ui/screens/login/login_screen_golden_test.dart

# 全画面のGoldenテストを更新
flutter test --update-goldens test/ui/screens/
```

## 注意事項

- 画面テストでは `surfaceSize` にスクリーンサイズを使用する
- 非同期状態（ローディング、エラー）もテストする
- レスポンシブ対応の場合は複数サイズでテストする
- Riverpod使用時は適切なモックプロバイダーを準備する
