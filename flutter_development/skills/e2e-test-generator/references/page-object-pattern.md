# Page Object パターン テンプレート

## 概要

Page Object パターンは、画面ごとに操作メソッドを集約するパターン。
UI 構造の変更を Page Object 内に閉じ込め、シナリオテストへの影響を最小化する。

---

## テンプレート

### 基本構造

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

// Keys クラスのインポート
import 'package:your_app/ui/auth/login_keys.dart';

/// ログイン画面の Page Object
///
/// テスト仕様書の操作ステップを、具体的な Widget 操作に変換する。
/// UI構造の変更はこのクラス内で吸収し、シナリオテストには影響を与えない。
class LoginPage {
  final WidgetTester tester;

  LoginPage(this.tester);

  // === Finder 定義 ===

  Finder get screen => find.byKey(LoginKeys.screen);
  Finder get emailField => find.byKey(LoginKeys.emailField);
  Finder get passwordField => find.byKey(LoginKeys.passwordField);
  Finder get loginButton => find.byKey(LoginKeys.loginButton);
  Finder get errorText => find.byKey(LoginKeys.errorText);

  // === 検証メソッド ===

  /// この画面が表示されていることを検証する
  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle();
    expect(screen, findsOneWidget);
  }

  /// エラーメッセージが表示されていることを検証する
  Future<void> verifyErrorDisplayed(String message) async {
    await tester.pumpAndSettle();
    expect(errorText, findsOneWidget);
    expect(find.text(message), findsOneWidget);
  }

  // === 操作メソッド ===

  /// メールアドレスを入力する
  Future<void> enterEmail(String email) async {
    await tester.enterText(emailField, email);
    await tester.pumpAndSettle();
  }

  /// パスワードを入力する
  Future<void> enterPassword(String password) async {
    await tester.enterText(passwordField, password);
    await tester.pumpAndSettle();
  }

  /// ログインボタンをタップする
  Future<void> tapLogin() async {
    await tester.tap(loginButton);
    await tester.pumpAndSettle();
  }

  // === 複合操作メソッド ===

  /// メールアドレスとパスワードを入力してログインする
  Future<void> login({
    required String email,
    required String password,
  }) async {
    await enterEmail(email);
    await enterPassword(password);
    await tapLogin();
  }
}
```

---

## 設計ルール

### 1. クラス名

`{Screen}PageObject` とする（画面名 + PageObject）。
ウィジェットクラス名との衝突を回避するため `Page` ではなく `PageObject` を使用する。

| 画面ファイル | ウィジェットクラス | Page Object クラス名 |
|------------|---------------|-------------------|
| `login_page.dart` | `LoginPage` | `LoginPageObject` |
| `mypage_page.dart` | `MyPagePage` | `MyPagePageObject` |
| `auth_wall.dart` | `AuthWall` | `AuthWallPage` |
| `home_screen.dart` | `HomeScreen` | `HomeScreenPageObject` |
| `reservation_detail_screen.dart` | `ReservationDetailScreen` | `ReservationDetailPageObject` |

**例外**: ウィジェットクラス名と衝突しない場合は `{Screen}Page` でもよい（例: `AuthWallPage`）。

### 2. ファイル配置

```
integration_test/
└── page_objects/
    ├── login_page.dart
    ├── home_page.dart
    └── reservation_detail_page.dart
```

### 3. Finder の定義

- `get` プロパティとして定義する
- Keys クラスの Key を使用する
- `find.byKey()` を基本とする

```dart
// ✅ 良い例
Finder get emailField => find.byKey(LoginKeys.emailField);

// ❌ 悪い例（テキストで探す → 多言語化で壊れる）
Finder get emailField => find.text('メールアドレス');

// ❌ 悪い例（型で探す → 同じ型が複数あると壊れる）
Finder get emailField => find.byType(TextField);
```

### 4. 操作メソッドの設計

- メソッド名は仕様書の操作ステップに対応する自然な名前にする
- 各操作メソッドの最後に `pumpAndSettle()` を呼ぶ
- 戻り値は `Future<void>`（非同期）

```dart
// 仕様: 「メールアドレスを入力する」
Future<void> enterEmail(String email) async { ... }

// 仕様: 「ログインボタンをタップする」
Future<void> tapLogin() async { ... }
```

### 5. 検証メソッドの設計

- `verify` プレフィックスを付ける
- アサーションは仕様書の期待結果に対応させる
- `expect` は検証メソッド内に閉じ込める

```dart
// 仕様: 「ホーム画面が表示されること」
Future<void> verifyDisplayed() async { ... }

// 仕様: 「エラーメッセージが表示されること」
Future<void> verifyErrorDisplayed(String message) async { ... }
```

### 6. 複合操作メソッド（オプション）

よく使う操作の組み合わせは複合メソッドとして提供してもよい。
ただし、シナリオテストからは個別メソッドも直接呼べるようにする。

```dart
/// ログイン操作（メール入力 + パスワード入力 + ログインボタンタップ）
Future<void> login({required String email, required String password}) async {
  await enterEmail(email);
  await enterPassword(password);
  await tapLogin();
}
```

---

## ラッパーウィジェットのテキスト入力パターン

### find.descendant パターン

カスタムの TextFormField ラッパーを使用している場合、
`tester.enterText()` を Key の Finder に対して直接呼び出すと動作しないことがある。
ラッパー内部の `EditableText` を `find.descendant` で特定する。

```dart
/// カスタム TextFormField ラッパーへのテキスト入力
Future<void> enterDriverIdPart1(String value) async {
  // Key が付与されたラッパーから内部の EditableText を特定
  final editableText = find.descendant(
    of: driverIdPart1Field,  // find.byKey(LoginKeys.driverIdPart1Field)
    matching: find.byType(EditableText),
  );
  await tester.tap(editableText);
  await tester.enterText(editableText, value);
  await tester.pumpAndSettle();
}
```

### 直接入力が動作するケース

Key が `TextField` / `TextFormField` 自体に付与されている場合は直接入力可能。

```dart
Future<void> enterEmail(String email) async {
  await tester.enterText(emailField, email);
  await tester.pumpAndSettle();
}
```

---

## スクロール対応パターン

### 画面外要素へのアクセス

ログアウトボタンなど、画面の下部にあり初期表示では見えない要素には
`scrollUntilVisible` を使用する。

```dart
/// ログアウトボタンをタップする（スクロール対応）
Future<void> tapLogout() async {
  // ログアウトボタンが画面外にある可能性があるためスクロール
  await tester.scrollUntilVisible(
    logoutButton,
    300,  // スクロール量（ピクセル）
    scrollable: find.byType(SingleChildScrollView).first,
  );
  await tester.tap(logoutButton);
  await tester.pumpAndSettle(const Duration(seconds: 5));
}
```

### スクロール対応が必要な画面の判定

- マイページ: メニュー項目が多く、ログアウトボタンが画面外になりやすい
- 設定画面: 設定項目が多い場合
- フォーム画面: 入力フィールドが多い場合

Page Object 生成時に、対象画面の Widget ツリーの深さとスクロール可能なコンテナの
有無を確認し、スクロール対応が必要か判断する。

---

## 画面遷移の扱い

Page Object は自分の画面の操作のみを担当する。
画面遷移後の検証は、遷移先の Page Object で行う。

```dart
// シナリオテストでの使い方
final loginPage = LoginPage(tester);
final homePage = HomePage(tester);

// ログイン画面で操作
await loginPage.verifyDisplayed();
await loginPage.login(email: 'test@example.com', password: 'password');

// ホーム画面に遷移したことを検証（遷移先の Page Object を使う）
await homePage.verifyDisplayed();
```

---

## 待機処理のパターン

### 基本: pumpAndSettle()

アニメーションやビルドが完了するまで待機する。ほとんどのケースで十分。

```dart
await tester.pumpAndSettle();
```

### API レスポンス待ち

API 通信を伴う操作では、タイムアウト付きの待機が必要な場合がある。

```dart
/// ログイン処理（API通信あり）
Future<void> tapLoginAndWait() async {
  await tester.tap(loginButton);
  // API レスポンスを待つ（最大10秒）
  await tester.pumpAndSettle(const Duration(seconds: 10));
}
```

### ローディング表示の待機

ローディングインジケーターが消えるまで待機する。

```dart
/// ローディングが完了するまで待機する
Future<void> waitForLoading() async {
  // ローディングインジケーターが表示されている間待機
  await tester.pumpAndSettle(const Duration(seconds: 15));
}
```

---

## テンプレート生成の入力情報

AI がPage Object を生成する際に必要な情報：

1. **画面名**（Keys クラスから）
2. **Keys クラスの全 Key 一覧**
3. **仕様書の操作ステップ**（どのメソッドが必要か）
4. **仕様書の期待結果**（どの検証メソッドが必要か）

```
入力: LoginKeys (screen, emailField, passwordField, loginButton, errorText)
     + 仕様: 「メール入力」「パスワード入力」「ログインタップ」「エラー表示検証」

出力: LoginPage クラス
       - verifyDisplayed()
       - enterEmail(email)
       - enterPassword(password)
       - tapLogin()
       - verifyErrorDisplayed(message)
```
