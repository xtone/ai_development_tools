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

`{Screen}Page` とする（画面名 + Page）。

| 画面ファイル | Page Object クラス名 |
|------------|-------------------|
| `login_screen.dart` | `LoginPage` |
| `home_screen.dart` | `HomePage` |
| `reservation_detail_screen.dart` | `ReservationDetailPage` |

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
