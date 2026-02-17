# Flutter Golden Test スキル

Flutter初心者でもGolden Test（Visual Regression Test）環境をセットアップし、コンポーネントや画面のGolden Testを作成・実行できるようにする対話型スキル。

## 使用方法

以下のいずれかのリクエストでスキルが起動します：

- 「Golden Testを導入したい」
- 「ゴールデンテストをセットアップ」
- 「スクリーンショットテストを作りたい」
- 「コンポーネントのGolden Testを書いて」
- 「Golden Testを実行」

## 機能

### 1. 初期セットアップモード

Golden Test環境がないプロジェクトに以下を自動生成：

- `test/flutter_test_config.dart` - グローバルテスト設定
- `test/helpers/golden_test_helper.dart` - テストヘルパー
- `test/golden_test_issues.md` - 問題解決ログ
- CLAUDE.mdへの設定追記

対話で以下を確認：
- Golden Testの説明（初心者向け）
- 使用フォント
- Riverpod使用有無
- テーマ設定
- 画面サイズプリセット
- 画像アセット使用有無
- テスト作成粒度（コンポーネント/画面/都度確認）

### 2. テスト生成モード

既存のウィジェットに対してGolden Testを生成：

- コンポーネントテスト（ボタン、カード、入力フィールドなど）
- 画面テスト（Screen、Page）
- 各状態のテストケース自動生成
- 全状態比較テスト（all_states）
- ネットワーク画像の検出と対応案内
- 日本語フォントフォールバック問題の警告

### 3. テスト実行・更新モード

テストの実行方法を案内：

```bash
# Goldenファイルを生成/更新
flutter test --update-goldens path/to/test.dart

# テストを実行（検証）
flutter test path/to/test.dart
```

### 4. トラブルシューティングモード

テスト画像がうまく生成されない場合の対応：

- 問題の特定と原因分析
- 解決策の提案
- `test/golden_test_issues.md` への記録
- CLAUDE.mdへの注意点追記（プロジェクト固有の知見として蓄積）

## ファイル構造

```
flutter-golden-test/
├── SKILL.md                 # スキル定義
├── README.md                # このファイル
├── knowledge/
│   ├── golden-test-concepts.md    # 基礎知識
│   ├── common-issues.md           # よくある問題
│   └── best-practices.md          # ベストプラクティス
└── templates/
    ├── flutter_test_config.dart.md       # テスト設定
    ├── golden_test_helper.dart.md        # ヘルパー
    ├── golden_test_helper_riverpod.dart.md  # Riverpod対応
    ├── component_golden_test.dart.md     # コンポーネントテスト
    ├── screen_golden_test.dart.md        # 画面テスト
    └── golden_test_issues.md             # 問題解決ログ
```

## 生成されるファイル例

### プロジェクト構造

```
test/
├── flutter_test_config.dart
├── helpers/
│   ├── helpers.dart
│   └── golden_test_helper.dart
└── ui/
    └── components/
        ├── primary_button_golden_test.dart
        └── goldens/
            └── components/
                └── primary_button/
                    ├── enabled.png
                    ├── disabled.png
                    └── all_states.png
```

### テストコード例

```dart
testWidgets('有効状態', (tester) async {
  await tester.pumpGoldenWidget(
    PrimaryButton(onPressed: () {}, text: '保存'),
  );

  await expectLater(
    find.byType(PrimaryButton),
    matchesGoldenFile(
      GoldenFilePath.component('primary_button', 'enabled'),
    ),
  );

  await tester.cleanUpGoldenTest();
});
```

## 対応機能

- [x] 日本語フォント対応
- [x] Riverpod対応（ProviderScopeラップ）
- [x] カスタムテーマ対応
- [x] コンポーネントテスト
- [x] 画面テスト
- [x] レスポンシブテスト（複数画面サイズ）
- [x] 全状態比較テスト
- [x] 画像・アイコンのプリロード設定
- [x] ネットワーク画像の検出と対応案内
- [x] フォントフォールバック問題の警告
- [x] 問題解決ログの自動記録
- [x] テスト作成粒度の設定

## 参考情報

- [knowledge/golden-test-concepts.md](knowledge/golden-test-concepts.md) - Golden Testの基礎
- [knowledge/common-issues.md](knowledge/common-issues.md) - よくある問題と解決方法
- [knowledge/best-practices.md](knowledge/best-practices.md) - ベストプラクティス
