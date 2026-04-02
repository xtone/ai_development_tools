# テストコードテンプレート

## 概要

仕様書のシナリオを 1:1 で Dart の integration_test に変換するためのテンプレート。
テストコードは仕様書の「デコード結果」であり、手動で保守しない。

---

## シナリオテストのテンプレート

### 基本構造

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

// Page Objects
import '../page_objects/login_page.dart';
import '../page_objects/home_page.dart';

// App Launcher
import '../helpers/app_launcher.dart';

/// ST-AUTH-001: 正常ログイン/ログアウト
///
/// 試験内容: 正しい認証情報でログインし、ログアウトできること
/// 前提条件: 未ログイン状態、テストユーザーが存在
///
/// 仕様書: テスト仕様書 > 認証系 > ST-AUTH-001
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('ST-AUTH-001: 正常ログイン/ログアウト', () {
    testWidgets('正しい認証情報でログインし、ログアウトできること', (tester) async {
      // === セットアップ ===
      // 前提条件: 未ログイン状態
      await AppLauncher.launchAsLoggedOut(tester);

      // Page Objects
      final loginPage = LoginPage(tester);
      final homePage = HomePage(tester);
      final myPagePage = MyPagePage(tester);

      // === 手順 1: ログイン画面が表示される ===
      // 期待結果 1: ログイン画面が表示されること
      await loginPage.verifyDisplayed();

      // === 手順 2: メールアドレスを入力する ===
      await loginPage.enterEmail('test@example.com');

      // === 手順 3: パスワードを入力する ===
      await loginPage.enterPassword('Test1234!');

      // === 手順 4: ログインボタンをタップする ===
      await loginPage.tapLogin();

      // === 手順 5: ホーム画面が表示される ===
      // 期待結果 5: ホーム画面が表示されること
      await homePage.verifyDisplayed();

      // === 手順 6: マイページアイコンをタップする ===
      await homePage.tapMyPageIcon();

      // === 手順 7: ログアウトボタンをタップする ===
      await myPagePage.tapLogout();

      // === 期待結果 7: ログイン画面に戻ること ===
      await loginPage.verifyDisplayed();
    });
  });
}
```

---

## AuthWall 経由フローのテンプレート

未ログイン状態で AuthWall（認証壁）が表示されるアプリの場合:

```dart
// === セットアップ ===
await AppLauncher.launchAsLoggedOut(tester);

final authWallPage = AuthWallPage(tester);
final loginPage = LoginPageObject(tester);

// === 手順 1: AuthWall が表示される ===
await authWallPage.verifyDisplayed();

// === 手順 2: 「ログイン」ボタンをタップ → ログイン画面に遷移 ===
await authWallPage.tapLogin();
await loginPage.verifyDisplayed();

// 以降、ログイン操作...
```

---

## 3フィールドログインのテンプレート

運転者IDが分割フィールドの場合:

```dart
// テストデータ
const testDriverIdPart1 = 'CP000000';
const testDriverIdPart2 = '001';
const testPassword = 'TestPass123!';

// 個別入力
await loginPage.enterDriverIdPart1(testDriverIdPart1);
await loginPage.enterDriverIdPart2(testDriverIdPart2);
await loginPage.enterPassword(testPassword);
await loginPage.tapLogin();

// または複合メソッド
await loginPage.login(
  driverIdPart1: testDriverIdPart1,
  driverIdPart2: testDriverIdPart2,
  password: testPassword,
);
```

---

## ダイアログなしログアウトのテンプレート

確認ダイアログなしで直接ログアウトするアプリの場合:

```dart
// === ログアウト操作 ===
// 確認ダイアログなし（ic_card パターン）
await myPage.tapLogout();
// ログアウト後、AuthWall に戻ることを検証
await authWallPage.verifyDisplayed();
```

**比較: ダイアログありの場合:**
```dart
// 確認ダイアログあり（標準パターン）
await myPage.tapLogout();
await TestHelper.confirmDialog(tester);
await loginPage.verifyDisplayed();
```

---

## コメント規約

### 手順コメント

仕様書の手順番号と対応させる。

```dart
// === 手順 {N}: {仕様書の手順テキスト} ===
```

### 期待結果コメント

仕様書の期待結果番号と対応させる。操作と期待結果が同じステップの場合はまとめる。

```dart
// === 期待結果 {N}: {仕様書の期待結果テキスト} ===
```

### セットアップコメント

前提条件を明示する。

```dart
// === セットアップ ===
// 前提条件: {仕様書の前提条件テキスト}
```

---

## テストヘルパーのテンプレート

### AppLauncher（アプリ起動ヘルパー）

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/main.dart' as app;

/// テスト用のアプリ起動ヘルパー
///
/// 前提条件に応じたアプリの初期状態をセットアップする。
class AppLauncher {
  /// 未ログイン状態でアプリを起動する
  ///
  /// 前提条件: 未ログイン状態
  static Future<void> launchAsLoggedOut(WidgetTester tester) async {
    // 認証トークンをクリア
    // SharedPreferences / SecureStorage をリセット
    app.main();
    await tester.pumpAndSettle();
  }

  /// ログイン済み状態でアプリを起動する
  ///
  /// 前提条件: ログイン済み
  static Future<void> launchAsLoggedIn(WidgetTester tester) async {
    // テストユーザーの認証トークンをセット
    app.main();
    await tester.pumpAndSettle();
  }

  /// 特定のユーザーでログイン済み状態で起動する
  ///
  /// 前提条件: 特定ユーザーでログイン済み
  static Future<void> launchAsUser(
    WidgetTester tester, {
    required String email,
    required String token,
  }) async {
    // 指定ユーザーの認証トークンをセット
    app.main();
    await tester.pumpAndSettle();
  }
}
```

### TestHelper（共通ヘルパー）

```dart
import 'package:flutter_test/flutter_test.dart';

/// テスト共通ヘルパー
class TestHelper {
  /// スクロールして要素を見つける
  static Future<void> scrollUntilVisible(
    WidgetTester tester, {
    required Finder finder,
    required Finder scrollable,
    double delta = 300,
  }) async {
    await tester.scrollUntilVisible(
      finder,
      delta,
      scrollable: scrollable,
    );
    await tester.pumpAndSettle();
  }

  /// ダイアログの「OK」ボタンをタップする
  static Future<void> dismissDialog(WidgetTester tester) async {
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();
  }

  /// 確認ダイアログで「はい」をタップする
  static Future<void> confirmDialog(WidgetTester tester) async {
    await tester.tap(find.text('はい'));
    await tester.pumpAndSettle();
  }

  /// スナックバーが表示されるまで待機する
  static Future<void> waitForSnackBar(
    WidgetTester tester, {
    String? message,
  }) async {
    await tester.pumpAndSettle();
    if (message != null) {
      expect(find.text(message), findsOneWidget);
    }
  }
}
```

---

## テストファイル命名規約

| 仕様書ID | テストファイル名 |
|---------|---------------|
| `ST-AUTH-001` | `st_auth_001_test.dart` |
| `ST-RSV-002` | `st_rsv_002_test.dart` |
| `ST-USE-001` | `st_use_001_test.dart` |

### ルール

1. ID をそのまま snake_case に変換
2. `_test.dart` サフィックスを付ける
3. `integration_test/scenarios/` 配下に配置

---

## テストデータの扱い

### テストデータの定義

テストデータはテストファイル内のトップレベル定数として定義する。

```dart
/// テストデータ
/// 仕様書の前提条件に基づく
const _testEmail = 'test@example.com';
const _testPassword = 'Test1234!';
const _testUserName = 'テストユーザー';
```

### テストデータの方針

- テストデータは仕様書の前提条件に明記されたものを使う
- ハードコードで問題ない（テストは再生成される前提）
- 環境依存のデータ（API エンドポイント等）は AppLauncher で管理

---

## 複数シナリオの構造化

1つのテストファイルに複数の関連テストを含める場合：

```dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('ST-AUTH: 認証系テスト', () {
    // ST-AUTH-001
    testWidgets('ST-AUTH-001: 正常ログイン/ログアウト', (tester) async {
      // ...
    });

    // ST-AUTH-002
    testWidgets('ST-AUTH-002: 異常ログイン（パスワード誤り）', (tester) async {
      // ...
    });
  });
}
```

ただし、基本は **1 仕様 = 1 ファイル** を推奨。
ファイルが多くなっても、再生成で管理するため問題にならない。
