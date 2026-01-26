# component_golden_test.dart テンプレート

## 概要

コンポーネント（ボタン、カード、入力フィールドなど）のGolden Testテンプレート。
各状態を個別にテストし、最後に全状態を一覧表示するパターン。

## プレースホルダー

| プレースホルダー | 説明 | 例 |
|-----------------|------|-----|
| `{COMPONENT_IMPORT}` | コンポーネントのインポートパス | `package:your_app/ui/components/primary_button.dart` |
| `{HELPER_IMPORT}` | ヘルパーのインポートパス | `../../helpers/golden_test_helper.dart` |
| `{COMPONENT_NAME}` | コンポーネント名（表示用） | `PrimaryButton` |
| `{COMPONENT_SNAKE_CASE}` | コンポーネント名（snake_case） | `primary_button` |
| `{TEST_CASES}` | 各状態のテストケース | 下記参照 |
| `{ALL_STATES_WIDGETS}` | 全状態のウィジェット一覧 | 下記参照 |
| `{LIST_WIDTH}` | リスト表示時の幅 | `400` |
| `{LIST_HEIGHT}` | リスト表示時の高さ | `400` |

## テンプレート

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '{COMPONENT_IMPORT}';

import '{HELPER_IMPORT}';

void main() {
  group('{COMPONENT_NAME} Golden Tests', () {
    {TEST_CASES}

    testWidgets('全状態の比較', (tester) async {
      await tester.pumpGoldenWidgetList(
        [
          {ALL_STATES_WIDGETS}
        ],
        surfaceSize: const Size({LIST_WIDTH}, {LIST_HEIGHT}),
      );

      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile(
          GoldenFilePath.component('{COMPONENT_SNAKE_CASE}', 'all_states'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });
  });
}
```

## TEST_CASES の例

### ボタンコンポーネントの場合

```dart
    testWidgets('有効状態', (tester) async {
      await tester.pumpGoldenWidget(
        PrimaryButton(
          onPressed: () {},
          text: '保存する',
        ),
      );

      await expectLater(
        find.byType(PrimaryButton),
        matchesGoldenFile(
          GoldenFilePath.component('primary_button', 'enabled'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('無効状態', (tester) async {
      await tester.pumpGoldenWidget(
        const PrimaryButton(
          onPressed: null,
          text: '保存する',
        ),
      );

      await expectLater(
        find.byType(PrimaryButton),
        matchesGoldenFile(
          GoldenFilePath.component('primary_button', 'disabled'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('アイコン付き', (tester) async {
      await tester.pumpGoldenWidget(
        PrimaryButton(
          onPressed: () {},
          text: '保存する',
          icon: const Icon(Icons.save),
        ),
      );

      await expectLater(
        find.byType(PrimaryButton),
        matchesGoldenFile(
          GoldenFilePath.component('primary_button', 'with_icon'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('長いテキスト', (tester) async {
      await tester.pumpGoldenWidget(
        PrimaryButton(
          onPressed: () {},
          text: 'これは非常に長いテキストのボタンです',
        ),
      );

      await expectLater(
        find.byType(PrimaryButton),
        matchesGoldenFile(
          GoldenFilePath.component('primary_button', 'long_text'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });
```

### 入力フィールドの場合

```dart
    testWidgets('通常状態', (tester) async {
      await tester.pumpGoldenWidget(
        const CustomTextFormField(
          labelText: 'メールアドレス',
        ),
      );

      await expectLater(
        find.byType(CustomTextFormField),
        matchesGoldenFile(
          GoldenFilePath.component('custom_text_form_field', 'normal'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('エラー状態', (tester) async {
      await tester.pumpGoldenWidget(
        const CustomTextFormField(
          labelText: 'メールアドレス',
          errorText: '正しいメールアドレスを入力してください',
        ),
      );

      await expectLater(
        find.byType(CustomTextFormField),
        matchesGoldenFile(
          GoldenFilePath.component('custom_text_form_field', 'error'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('無効状態', (tester) async {
      await tester.pumpGoldenWidget(
        const CustomTextFormField(
          labelText: 'メールアドレス',
          enabled: false,
        ),
      );

      await expectLater(
        find.byType(CustomTextFormField),
        matchesGoldenFile(
          GoldenFilePath.component('custom_text_form_field', 'disabled'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });
```

## ALL_STATES_WIDGETS の例

```dart
          // 有効状態
          PrimaryButton(
            onPressed: () {},
            text: '有効',
          ),
          // 無効状態
          const PrimaryButton(
            onPressed: null,
            text: '無効',
          ),
          // アイコン付き
          PrimaryButton(
            onPressed: () {},
            text: 'アイコン付き',
            icon: const Icon(Icons.save),
          ),
```

## 完成例

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/ui/components/primary_button.dart';

import '../../helpers/golden_test_helper.dart';

void main() {
  group('PrimaryButton Golden Tests', () {
    testWidgets('有効状態', (tester) async {
      await tester.pumpGoldenWidget(
        PrimaryButton(
          onPressed: () {},
          text: '保存する',
        ),
      );

      await expectLater(
        find.byType(PrimaryButton),
        matchesGoldenFile(
          GoldenFilePath.component('primary_button', 'enabled'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('無効状態', (tester) async {
      await tester.pumpGoldenWidget(
        const PrimaryButton(
          onPressed: null,
          text: '保存する',
        ),
      );

      await expectLater(
        find.byType(PrimaryButton),
        matchesGoldenFile(
          GoldenFilePath.component('primary_button', 'disabled'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });

    testWidgets('全状態の比較', (tester) async {
      await tester.pumpGoldenWidgetList(
        [
          PrimaryButton(
            onPressed: () {},
            text: '有効',
          ),
          const PrimaryButton(
            onPressed: null,
            text: '無効',
          ),
        ],
        surfaceSize: const Size(400, 200),
      );

      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile(
          GoldenFilePath.component('primary_button', 'all_states'),
        ),
      );

      await tester.cleanUpGoldenTest();
    });
  });
}
```

## テスト実行コマンド

```bash
# Goldenファイルを生成/更新
flutter test --update-goldens test/ui/components/primary_button_golden_test.dart

# テストを実行（検証）
flutter test test/ui/components/primary_button_golden_test.dart
```

## 注意事項

- 各テストケースの最後に必ず `cleanUpGoldenTest()` を呼び出す
- 状態名は snake_case で統一（例: `enabled`, `disabled`, `with_icon`）
- `all_states` テストの高さは状態数 × 各コンポーネント高さ + パディングで計算
