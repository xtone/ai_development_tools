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

**重要: 以下の全ステップを順番に実行すること（スキップ禁止）**

| Step | 内容 | 必須 |
|------|------|------|
| 0 | Golden Testの説明 | ○ |
| 1 | プロジェクト解析 | ○ |
| 2 | フォント設定確認 | ○ |
| 3 | Riverpod使用確認 | ○ |
| 4 | テーマ設定確認 | ○ |
| 5 | 画面サイズ確認 | ○ |
| 6 | 画像アセット使用確認 | ○ |
| 7 | テスト作成粒度の確認 | ○ |
| 8 | ファイル生成 | ○ |

#### Step 0: Golden Testの説明 [0/8]

**最初に以下を伝える:**
```
「Golden Test（ゴールデンテスト）の環境をセットアップしますね。【Step 0/8】

■ Golden Testとは？
ウィジェットのスクリーンショットを保存し、以降の変更で見た目が意図せず変わっていないかを自動検証するテストです。UIの品質を保ちながら安心してリファクタリングできるようになります。

■ このスキルでできること
対話形式で環境構築からテスト作成までサポートします。テスト画像がうまく生成されない場合も、会話しながら一緒に解決していきますので、お気軽にご質問ください。

■ 具体例：こんなテストが作れます
例えば、以下のようなボタンウィジェットがあるとします：」
```

**続けて、以下の具体例を提示する:**

````
「▼ 対象ウィジェット（例）
```dart
class PrimaryButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;

  const PrimaryButton({required this.text, this.onPressed});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(onPressed: onPressed, child: Text(text));
  }
}
```

▼ 生成されるテストコード
```dart
testWidgets('有効状態', (tester) async {
  await tester.pumpGoldenWidget(
    PrimaryButton(onPressed: () {}, text: '保存する'),
  );
  await expectLater(
    find.byType(PrimaryButton),
    matchesGoldenFile(
      GoldenFilePath.component('primary_button', 'enabled'),
    ),
  );
});
```

▼ 生成されるファイル
test/ui/components/
├── primary_button_golden_test.dart   ← テストコード
└── goldens/components/primary_button/
    ├── enabled.png                   ← 有効状態のスクリーンショット
    ├── disabled.png                  ← 無効状態のスクリーンショット
    └── all_states.png                ← 全状態の一覧比較

▼ テスト実行コマンド
# 初回：Goldenファイル（正解画像）を生成
flutter test --update-goldens test/ui/components/primary_button_golden_test.dart

# 以降：画像に差分がないか検証（CIでも実行可能）
flutter test test/ui/components/primary_button_golden_test.dart

セットアップ完了後、対話形式でこのようなテストを自動生成していきます。
何か事前に質問があれば、今のうちにどうぞ。なければ、セットアップを始めましょう。」
````

**ユーザーの回答を待つ → 回答後、Step 1へ進む**

#### Step 1: プロジェクト解析 [1/8]

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

**ユーザーの回答を待つ → 回答後、Step 2へ進む**

#### Step 2: フォント設定確認 [2/8]

```
「【Step 2/8】Golden Testではフォントの一貫性が重要です。
プロジェクトで使用しているフォントを教えてください：

1. Noto Sans JP（日本語対応）
2. Roboto（Material Design標準）
3. カスタムフォント（フォント名とパスを教えてください）
4. フォント設定は不要

どれを使用していますか？」
```

**ユーザーの回答を待つ → 回答後、Step 3へ進む**

#### Step 3: Riverpod使用確認 [3/8]

**Step 1のプロジェクト解析結果に基づいて、以下のA/B/Cいずれかのパターンで質問する。**

**A) Riverpodを使用していない（pubspec.yamlにriverpod関連パッケージがない）場合:**

```
「【Step 3/8】プロジェクトでRiverpodを使用していますか？

1. はい - ProviderScopeでラップするヘルパーを追加します
2. いいえ - シンプルなMaterialAppのみで構成します

どちらですか？」
```

**B) Riverpodを使用しており、既存のテストヘルパー（例: `test/helpers/pump_app.dart`）が存在する場合:**

**必ず各選択肢のメリット・デメリットを明記し、推奨を示すこと。**

```
「【Step 3/8】プロジェクトでRiverpodを使用していることを確認しました。
既存のテストヘルパー（{検出したファイルパス}）も検出しました。

Golden TestのProviderScope設定について、2つの方針があります：

1. 既存のヘルパーを活用する（推奨）
   ✅ メリット: 既存テストと設定が統一され、Providerのoverrideなどが一箇所で管理できる
   ⚠️ デメリット: 既存ヘルパーの変更がGolden Testにも影響する
   → 既にテストが整備されているプロジェクトにおすすめ

2. Golden Test専用に独立した設定にする
   ✅ メリット: Golden Test固有の設定を自由にカスタマイズでき、他のテストに影響しない
   ⚠️ デメリット: 設定が二重管理になり、変更時に両方を更新する必要がある
   → Golden Test特有のカスタマイズが多い場合におすすめ

迷ったら 1（推奨）を選んでください。どちらにしますか？」
```

**C) Riverpodを使用しているが、既存のテストヘルパーが存在しない場合:**

```
「【Step 3/8】プロジェクトでRiverpodを使用していることを確認しました。
ProviderScopeでラップするGolden Test用ヘルパーを新規作成します。

この方針でよろしいですか？」
```

**ユーザーの回答を待つ → 回答後、Step 4へ進む**

#### Step 4: テーマ設定確認 [4/8]

```
「【Step 4/8】テストで使用するテーマを教えてください：

1. カスタムテーマを使用（例: AppTheme.light()）
2. デフォルトのMaterial Themeを使用

カスタムテーマの場合、インポートパスを教えてください。」
```

**ユーザーの回答を待つ → 回答後、Step 5へ進む**

#### Step 5: 画面サイズ確認 [5/8]

```
「【Step 5/8】テスト用のサイズプリセットを設定します。
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

**ユーザーの回答を待つ → 回答後、Step 6へ進む**

#### Step 6: 画像アセット使用確認 [6/8]

```
「【Step 6/8】プロジェクトで画像アセットを使用していますか？

1. はい - 画像をテスト環境でロードする設定を追加します
2. いいえ - 画像ローディングの設定は不要です

画像を使用している場合、テストでも正しく表示されるよう設定します。」
```

**ユーザーの回答を待つ → 回答後、Step 7へ進む**

#### Step 7: テスト作成粒度の確認 [7/8]

```
「【Step 7/8】今後のテスト作成時、どの単位でテストを作成しますか？

1. コンポーネント単位 - ボタンやカードなど、再利用可能な部品ごとにテスト
2. 画面単位 - Screen/Pageごとにテスト
3. 都度確認 - テスト作成時に毎回確認する

この設定はプロジェクトのCLAUDE.mdに記録し、以降のテスト作成時に参照します。」
```

**ユーザーの回答を待つ → 回答後、Step 8（ファイル生成）へ進む**

#### Step 8: ファイル生成 [8/8]

**全ステップ完了後、収集した情報を基に以下のファイルを生成：**

1. `test/flutter_test_config.dart`
   - templates/flutter_test_config.dart.md を参照
   - フォント設定を反映
   - 画像アセット使用時はMaterialIconsのロード設定を追加

2. `test/helpers/golden_test_helper.dart`
   - templates/golden_test_helper.dart.md を参照
   - Riverpod使用時は templates/golden_test_helper_riverpod.dart.md も参照
   - テーマとサイズ設定を反映

3. `test/helpers/helpers.dart` (バレルファイル)
   - ヘルパーファイルをエクスポート

4. `test/golden_test_issues.md` (問題解決ログ)
   - templates/golden_test_issues.md を参照
   - トラブルシューティングの記録用

5. **プロジェクトのCLAUDE.mdに追記**
   - Golden Test設定セクションを追加
   - テスト作成粒度の設定を記録

**CLAUDE.mdへの追記例:**
```markdown
## Golden Test 設定

### テスト作成粒度
- 方針: コンポーネント単位（または画面単位/都度確認）

### プロジェクト固有の注意点
- （問題が発生した場合、ここに記録される）
```

**生成後の発言例:**
```
「以下のファイルを生成しました：

1. test/flutter_test_config.dart
   - グローバルテスト設定
   - フォントローディング
   - アイコンフォントのロード

2. test/helpers/golden_test_helper.dart
   - GoldenTestSizes: サイズプリセット
   - GoldenTestExtension: pumpGoldenWidget(), pumpGoldenWidgetList()
   - GoldenFilePath: パス生成ユーティリティ

3. test/golden_test_issues.md
   - 問題解決ログ（トラブル発生時に記録）

4. CLAUDE.mdに設定を追記しました
   - テスト作成粒度: {選択された粒度}

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

**CLAUDE.mdのテスト作成粒度設定を確認:**
- 「コンポーネント単位」→ コンポーネントテストとして進行
- 「画面単位」→ 画面テストとして進行
- 「都度確認」または設定なし → 以下の質問を行う

```
「このウィジェットは以下のどちらですか？（番号でお答えください）

1. コンポーネント（ボタン、カード、入力フィールドなど）
2. 画面（Screen、Pageなど）」
```

**ユーザーの回答を待つ**

#### Step 3: ウィジェット解析と警告チェック

**ウィジェットコードを解析し、以下をチェック:**

1. **ネットワーク画像の検出** (`Image.network`, `CachedNetworkImage` など)
   - 検出した場合、以下を案内:
   ```
   「⚠️ ネットワーク画像を検出しました。

   Golden Testではネットワーク画像は取得できないため、テスト用にダミー画像で置き換える必要があります。

   対応方法：
   1. モック画像プロバイダーを使用
   2. テスト用のアセット画像に差し替え

   詳しくは knowledge/common-issues.md の「ネットワーク画像の対応」を参照してください。

   このまま進めますか？」
   ```

2. **日本語テキストとフォントの確認**
   - 日本語テキストが含まれ、かつフォントがRobotoなど日本語非対応の場合:
   ```
   「⚠️ 日本語テキストを検出しましたが、設定されているフォント（Roboto）は日本語に対応していません。

   実機ではOSがフォールバックしますが、Golden Testでは日本語が正しく表示されない可能性があります。

   対応方法：
   1. Noto Sans JPなど日本語対応フォントを追加
   2. flutter_test_config.dartでフォントをロード

   詳しくは knowledge/common-issues.md の「日本語フォントの問題」を参照してください。

   このまま進めますか？」
   ```

#### Step 4: ウィジェットパラメータ解析

対象ウィジェットのコードを読み取り、コンストラクタパラメータを解析。

**解析後の発言例:**
```
「PrimaryButtonを解析しました。

コンストラクタパラメータ：
- text: String (必須)
- onPressed: VoidCallback? (オプション)
- icon: Widget? (オプション)

テストしたい状態を選んでください（複数選択可、番号でお答えください）：
1. 有効状態（onPressed != null）
2. 無効状態（onPressed == null）
3. アイコン付き
4. 長いテキスト
5. 全状態の比較（一覧表示）

他にテストしたい状態はありますか？」
```

**ユーザーの回答を待つ**

#### Step 5: テストコード生成

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

⚠️ もしテスト画像がうまく生成されない場合は、エラー内容を教えてください。一緒に解決していきましょう。」
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

実行しますか？

⚠️ テストが失敗したり、画像が期待通りにならない場合は、エラー内容を教えてください。」
```

### モード4: トラブルシューティング

テストがうまくいかない場合の対応フロー。

#### Step 1: 問題の特定

ユーザーからエラー内容や問題の報告を受けたら、以下を確認：

1. **エラーメッセージ**: 具体的なエラー内容
2. **期待と実際の差**: 何が違うのか
3. **環境情報**: Flutter バージョン、OS など

#### Step 2: 原因の特定と解決

`knowledge/common-issues.md` を参照し、該当する問題と解決策を提案。

**よくある問題:**
- フォントが表示されない → フォントローディング設定
- 画像が表示されない → アセットローディングまたはモック
- CI環境で失敗 → devicePixelRatio、環境差異
- 日本語が文字化け → 日本語フォント設定

#### Step 3: 問題解決ログへの記録

問題を解決したら、`test/golden_test_issues.md` に記録を追加：

```
「問題を解決しました！

今後のために、この問題と解決方法を `test/golden_test_issues.md` に記録しておきますね。

---
## {日付}: {問題の概要}

### 問題
{問題の詳細}

### 原因
{原因の説明}

### 解決方法
{解決手順}

### 今後の注意点
{同様の問題を防ぐためのポイント}
---

これで同じ問題が発生しても、すぐに対応できます。」
```

**CLAUDE.mdへの追記（必要に応じて）:**

プロジェクト固有の注意点として、CLAUDE.mdの「Golden Test 設定」セクションにも追記：

```markdown
### プロジェクト固有の注意点
- {解決した問題の要約と対策}
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
| golden_test_issues.md | 問題解決ログ |

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
