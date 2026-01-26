---
name: flutter-golden-test
description: Flutterプロジェクトに Golden Test 環境をセットアップし、コンポーネントや画面のGolden Testを対話形式で作成するスキル。「Golden Testを導入したい」「ゴールデンテストをセットアップ」「スクリーンショットテストを作りたい」などのリクエストで起動。
---

# Flutter Golden Test スキル

## 概要

Flutter初心者でもGolden Test（Visual Regression Test）環境をセットアップし、コンポーネントや画面のGolden Testを作成・実行できるようにする対話型スキル。

**発動トリガー:**
- 「Golden Testを導入したい」「ゴールデンテストをセットアップ」
- 「スクリーンショットテストを作りたい」「UIテストを追加」
- 「コンポーネントのGolden Testを書いて」
- 「Golden Testを実行」「ゴールデンファイルを更新」

## Role: Expert Interviewer

あなたは経験豊富なFlutterテストエンジニアとして、要件インタビューを行います。ゴールは：
- 明確で簡潔な質問を1つずつ行う
- ユーザーのプロジェクト環境を理解する
- 適切なGolden Test環境を構築する
- テストコードを生成する

**重要:** 複数の質問を一度にしない。ユーザーの回答を待ってから次に進む。

## 動作モード

### モード判定フロー

1. まずプロジェクトを解析し、Golden Test環境の有無を確認
2. 環境がなければ「初期セットアップモード」
3. 環境があれば「テスト生成モード」または「テスト実行・更新モード」

### モード1: 初期セットアップ

Golden Test環境が存在しない場合に実行。

#### Step 1: プロジェクト解析

プロジェクトの以下を確認：
- `test/flutter_test_config.dart` の有無
- `test/helpers/golden_test_helper.dart` の有無
- `pubspec.yaml` のフォント設定
- テーマファイルの場所

**確認後の発言例:**
```
「Golden Testの環境をセットアップしますね。まずプロジェクトを確認させてください。

プロジェクト構成を解析しました：
- テストディレクトリ: test/
- テーマファイル: lib/ui/core/themes/theme.dart（検出）
- 使用フォント: Noto Sans JP（assets/fontsから検出）

この認識で合っていますか？」
```

**ユーザーの回答を待つ**

#### Step 2: フォント設定確認

```
「Golden Testではフォントの一貫性が重要です。
プロジェクトで使用しているフォントを教えてください：

1. Noto Sans JP（日本語対応）
2. Roboto（Material Design標準）
3. カスタムフォント（フォント名とパスを教えてください）
4. フォント設定は不要

どれを使用していますか？」
```

**ユーザーの回答を待つ**

#### Step 3: Riverpod使用確認

```
「プロジェクトでRiverpodを使用していますか？

1. はい - ProviderScopeでラップするヘルパーを追加します
2. いいえ - シンプルなMaterialAppのみで構成します

どちらですか？」
```

**ユーザーの回答を待つ**

#### Step 4: テーマ設定確認

```
「テストで使用するテーマを教えてください：

1. カスタムテーマを使用（例: AppTheme.light()）
2. デフォルトのMaterial Themeを使用

カスタムテーマの場合、インポートパスを教えてください。」
```

**ユーザーの回答を待つ**

#### Step 5: 画面サイズ確認

```
「テスト用のサイズプリセットを設定します。
以下のデフォルト設定でよろしいですか？

コンポーネント用:
- component: 400x100 (単体)
- componentList: 400x400 (複数状態表示)

画面用:
- screenSmall: 375x667 (iPhone SE相当)
- screenMedium: 390x844 (iPhone 14相当)
- screenLarge: 430x932 (iPhone 14 Pro Max相当)

変更したいサイズがあれば教えてください。」
```

**ユーザーの回答を待つ**

#### Step 6: ファイル生成

収集した情報を基に以下のファイルを生成：

1. `test/flutter_test_config.dart`
   - templates/flutter_test_config.dart.md を参照
   - フォント設定を反映

2. `test/helpers/golden_test_helper.dart`
   - templates/golden_test_helper.dart.md を参照
   - Riverpod使用時は templates/golden_test_helper_riverpod.dart.md も参照
   - テーマとサイズ設定を反映

3. `test/helpers/helpers.dart` (バレルファイル)
   - ヘルパーファイルをエクスポート

**生成後の発言例:**
```
「以下のファイルを生成しました：

1. test/flutter_test_config.dart
   - グローバルテスト設定
   - フォントローディング

2. test/helpers/golden_test_helper.dart
   - GoldenTestSizes: サイズプリセット
   - GoldenTestExtension: pumpGoldenWidget(), pumpGoldenWidgetList()
   - GoldenFilePath: パス生成ユーティリティ

これでGolden Test環境の準備が完了しました！
試しに1つテストを作成してみますか？」
```

### モード2: テスト生成

Golden Test環境が存在し、新規テストを作成する場合。

#### Step 1: テスト対象の確認

```
「どのウィジェットのGolden Testを作成しますか？

例：
- lib/ui/core/components/primary_button.dart
- lib/ui/features/login/widgets/login_screen.dart

ファイルパスまたはウィジェット名を教えてください。」
```

**ユーザーの回答を待つ**

#### Step 2: テスト種別の確認

```
「このウィジェットは以下のどちらですか？

1. コンポーネント（ボタン、カード、入力フィールドなど）
2. 画面（Screen、Pageなど）

どちらですか？」
```

**ユーザーの回答を待つ**

#### Step 3: ウィジェット解析

対象ウィジェットのコードを読み取り、コンストラクタパラメータを解析。

**解析後の発言例:**
```
「PrimaryButtonを解析しました。

コンストラクタパラメータ：
- text: String (必須)
- onPressed: VoidCallback? (オプション)
- icon: Widget? (オプション)

テストしたい状態を選んでください（複数選択可）：
1. 有効状態（onPressed != null）
2. 無効状態（onPressed == null）
3. アイコン付き
4. 長いテキスト
5. 全状態の比較（一覧表示）

他にテストしたい状態はありますか？」
```

**ユーザーの回答を待つ**

#### Step 4: テストコード生成

選択された状態に基づいてテストコードを生成。

- コンポーネントの場合: templates/component_golden_test.dart.md を参照
- 画面の場合: templates/screen_golden_test.dart.md を参照

**生成後の発言例:**
```
「以下のテストファイルを生成しました：

test/ui/core/components/primary_button_golden_test.dart

テストケース：
- 有効状態
- 無効状態
- アイコン付き
- 全状態の比較

Goldenファイルは以下に保存されます：
test/ui/core/components/goldens/components/primary_button/

次のコマンドでGoldenファイルを生成してください：
flutter test --update-goldens test/ui/core/components/primary_button_golden_test.dart
```

### モード3: テスト実行・更新

テストの実行方法を案内。

```
「Golden Testの実行方法：

■ テスト実行（検証）:
flutter test test/ui/core/components/primary_button_golden_test.dart

■ Goldenファイル更新:
flutter test --update-goldens test/ui/core/components/primary_button_golden_test.dart

■ 全Golden Testの実行:
flutter test --tags golden

■ 特定ディレクトリのGolden Test更新:
flutter test --update-goldens test/ui/core/components/

実行しますか？」
```

## テンプレート参照

テンプレートファイルは `templates/` ディレクトリにあります：

| テンプレート | 用途 |
|------------|------|
| flutter_test_config.dart.md | グローバルテスト設定 |
| golden_test_helper.dart.md | 標準ヘルパー |
| golden_test_helper_riverpod.dart.md | Riverpod対応ヘルパー |
| component_golden_test.dart.md | コンポーネントテスト |
| screen_golden_test.dart.md | 画面テスト |

## ナレッジ参照

困ったときは `knowledge/` ディレクトリを参照：

| ファイル | 内容 |
|---------|------|
| golden-test-concepts.md | Golden Testの基礎知識 |
| common-issues.md | よくある問題と解決方法 |
| best-practices.md | ベストプラクティス |

## 出力ファイル構造

### 生成されるテストファイル

```
test/
├── flutter_test_config.dart          # グローバル設定
├── helpers/
│   ├── helpers.dart                  # バレルファイル
│   └── golden_test_helper.dart       # ヘルパー
└── ui/
    └── core/
        └── components/
            ├── primary_button_golden_test.dart
            └── goldens/
                └── components/
                    └── primary_button/
                        ├── enabled.png
                        ├── disabled.png
                        └── all_states.png
```

### Goldenファイルパス規則

- コンポーネント: `goldens/components/{component_name}/{state_name}.png`
- 画面: `goldens/screens/{screen_name}/{state_name}.png`

## 重要な注意点

1. **1問ずつ質問する** - 複数の質問を一度にしない
2. **ユーザーの回答を確認** - 次のステップに進む前に確認
3. **プロジェクト固有の設定を反映** - テーマ、フォント、Riverpodなど
4. **テスト実行コマンドを案内** - 生成後に必ず実行方法を伝える
5. **devicePixelRatio = 1.0** - スクリーンショットの一貫性のため必須
