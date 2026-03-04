# PoC 実行例: ST-AUTH-001（正常ログイン/ログアウト）

## 概要

この文書は、E2E テスト自動生成スキルの PoC として ST-AUTH-001 を対象にした場合の、
入力から出力までの具体例を示す。

---

## 入力: テスト仕様書

### ST-AUTH-001: 正常ログイン/ログアウト

| 項目 | 内容 |
|------|------|
| 試験項目ID | ST-AUTH-001 |
| 試験内容 | 正しい認証情報でログインし、ログアウトできること |
| 前提条件 | 未ログイン状態、テストユーザー（test@example.com / Test1234!）が存在 |

#### 手順と期待結果

| # | 手順 | 期待結果 |
|---|------|---------|
| 1 | アプリを起動する | ログイン画面が表示される |
| 2 | メールアドレス欄に「test@example.com」を入力する | 入力値が表示される |
| 3 | パスワード欄に「Test1234!」を入力する | マスクされた入力値が表示される |
| 4 | 「ログイン」ボタンをタップする | ローディングが表示される |
| 5 | ローディングが完了する | ホーム画面が表示される |
| 6 | 下部ナビゲーションの「マイページ」をタップする | マイページ画面が表示される |
| 7 | 「ログアウト」ボタンをタップする | 確認ダイアログが表示される |
| 8 | 確認ダイアログで「はい」をタップする | ログイン画面に戻る |

---

## 出力 1: Keys クラス

### lib/ui/auth/login_keys.dart

```dart
import 'package:flutter/material.dart';

/// ログイン画面のテスト用Key定義
abstract class LoginKeys {
  static const screen = Key('login_screen');
  static const emailField = Key('login_field_email');
  static const passwordField = Key('login_field_password');
  static const loginButton = Key('login_button_submit');
  static const loadingIndicator = Key('login_indicator_loading');
  static const errorText = Key('login_text_error');
}
```

### lib/ui/home/home_keys.dart

```dart
import 'package:flutter/material.dart';

/// ホーム画面のテスト用Key定義
abstract class HomeKeys {
  static const screen = Key('home_screen');
  static const myPageNav = Key('home_nav_my_page');
}
```

### lib/ui/my_page/my_page_keys.dart

```dart
import 'package:flutter/material.dart';

/// マイページ画面のテスト用Key定義
abstract class MyPageKeys {
  static const screen = Key('my_page_screen');
  static const logoutButton = Key('my_page_button_logout');
  static const logoutDialog = Key('my_page_dialog_logout');
}
```

---

## 出力 2: Page Objects

### integration_test/page_objects/login_page.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/ui/auth/login_keys.dart';

/// ログイン画面の Page Object
class LoginPage {
  final WidgetTester tester;

  LoginPage(this.tester);

  Finder get screen => find.byKey(LoginKeys.screen);
  Finder get emailField => find.byKey(LoginKeys.emailField);
  Finder get passwordField => find.byKey(LoginKeys.passwordField);
  Finder get loginButton => find.byKey(LoginKeys.loginButton);

  /// ログイン画面が表示されていることを検証する
  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle();
    expect(screen, findsOneWidget);
  }

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
    await tester.pumpAndSettle(const Duration(seconds: 10));
  }
}
```

### integration_test/page_objects/home_page.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/ui/home/home_keys.dart';

/// ホーム画面の Page Object
class HomePage {
  final WidgetTester tester;

  HomePage(this.tester);

  Finder get screen => find.byKey(HomeKeys.screen);
  Finder get myPageNav => find.byKey(HomeKeys.myPageNav);

  /// ホーム画面が表示されていることを検証する
  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle();
    expect(screen, findsOneWidget);
  }

  /// マイページナビゲーションをタップする
  Future<void> tapMyPageNav() async {
    await tester.tap(myPageNav);
    await tester.pumpAndSettle();
  }
}
```

### integration_test/page_objects/my_page_page.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/ui/my_page/my_page_keys.dart';

/// マイページ画面の Page Object
class MyPagePage {
  final WidgetTester tester;

  MyPagePage(this.tester);

  Finder get screen => find.byKey(MyPageKeys.screen);
  Finder get logoutButton => find.byKey(MyPageKeys.logoutButton);

  /// マイページ画面が表示されていることを検証する
  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle();
    expect(screen, findsOneWidget);
  }

  /// ログアウトボタンをタップする
  Future<void> tapLogout() async {
    await tester.tap(logoutButton);
    await tester.pumpAndSettle();
  }
}
```

---

## 出力 3: シナリオテスト

### integration_test/scenarios/st_auth_001_test.dart

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import '../page_objects/login_page.dart';
import '../page_objects/home_page.dart';
import '../page_objects/my_page_page.dart';
import '../helpers/app_launcher.dart';
import '../helpers/test_helper.dart';

/// ST-AUTH-001: 正常ログイン/ログアウト
///
/// 試験内容: 正しい認証情報でログインし、ログアウトできること
/// 前提条件: 未ログイン状態、テストユーザーが存在
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  // テストデータ（仕様書の前提条件より）
  const testEmail = 'test@example.com';
  const testPassword = 'Test1234!';

  group('ST-AUTH-001: 正常ログイン/ログアウト', () {
    testWidgets('正しい認証情報でログインし、ログアウトできること', (tester) async {
      // === セットアップ ===
      // 前提条件: 未ログイン状態
      await AppLauncher.launchAsLoggedOut(tester);

      final loginPage = LoginPage(tester);
      final homePage = HomePage(tester);
      final myPagePage = MyPagePage(tester);

      // === 手順 1: アプリを起動する ===
      // 期待結果 1: ログイン画面が表示される
      await loginPage.verifyDisplayed();

      // === 手順 2: メールアドレス欄に入力する ===
      // 期待結果 2: 入力値が表示される
      await loginPage.enterEmail(testEmail);

      // === 手順 3: パスワード欄に入力する ===
      // 期待結果 3: マスクされた入力値が表示される
      await loginPage.enterPassword(testPassword);

      // === 手順 4: 「ログイン」ボタンをタップする ===
      // 期待結果 4-5: ローディング → ホーム画面が表示される
      await loginPage.tapLogin();

      // === 手順 5: ホーム画面が表示される ===
      await homePage.verifyDisplayed();

      // === 手順 6: 「マイページ」をタップする ===
      // 期待結果 6: マイページ画面が表示される
      await homePage.tapMyPageNav();
      await myPagePage.verifyDisplayed();

      // === 手順 7: 「ログアウト」ボタンをタップする ===
      // 期待結果 7: 確認ダイアログが表示される
      await myPagePage.tapLogout();

      // === 手順 8: 確認ダイアログで「はい」をタップする ===
      // 期待結果 8: ログイン画面に戻る
      await TestHelper.confirmDialog(tester);
      await loginPage.verifyDisplayed();
    });
  });
}
```

---

## 出力 4: マッピングレポート

### integration_test/reports/st_auth_001_mapping.md

```markdown
# マッピングレポート

- **テストID**: ST-AUTH-001
- **試験内容**: 正常ログイン/ログアウト
- **生成日時**: 20XX-XX-XX
- **対象画面**: LoginScreen, HomeScreen, MyPageScreen

## ステップ対応表

| # | 種別 | 仕様ステップ | 生成アクション | Key | 状態 |
|---|------|------------|-------------|-----|------|
| 1 | 検証 | ログイン画面が表示される | `loginPage.verifyDisplayed()` | `LoginKeys.screen` | ✅ |
| 2 | 操作 | メールアドレスを入力する | `loginPage.enterEmail(testEmail)` | `LoginKeys.emailField` | ✅ |
| 3 | 操作 | パスワードを入力する | `loginPage.enterPassword(testPassword)` | `LoginKeys.passwordField` | ✅ |
| 4 | 操作 | ログインボタンをタップ | `loginPage.tapLogin()` | `LoginKeys.loginButton` | ✅ |
| 5 | 検証 | ホーム画面が表示される | `homePage.verifyDisplayed()` | `HomeKeys.screen` | ⚠️ |
| 6 | 操作 | マイページをタップ | `homePage.tapMyPageNav()` | `HomeKeys.myPageNav` | ⚠️ |
| 6 | 検証 | マイページが表示される | `myPagePage.verifyDisplayed()` | `MyPageKeys.screen` | ⚠️ |
| 7 | 操作 | ログアウトをタップ | `myPagePage.tapLogout()` | `MyPageKeys.logoutButton` | ⚠️ |
| 8 | 操作 | 確認ダイアログで「はい」 | `TestHelper.confirmDialog(tester)` | - | ✅ |
| 8 | 検証 | ログイン画面に戻る | `loginPage.verifyDisplayed()` | `LoginKeys.screen` | ✅ |

## 前提条件マッピング

| 仕様の前提条件 | 実現方法 | 状態 |
|--------------|---------|------|
| 未ログイン状態 | `AppLauncher.launchAsLoggedOut(tester)` | ✅ |
| テストユーザーが存在 | テストデータとして定義 | ✅ |

## サマリー

| 指標 | 値 |
|------|---|
| 総ステップ数 | 10 |
| ✅ Key一致 | 6 (60%) |
| ⚠️ Key推定 | 4 (40%) |
| ❌ Key該当なし | 0 (0%) |
| **カバレッジ** | **100%** |

### 必要なアクション

1. ⚠️ `HomeKeys.screen` - ホーム画面の Scaffold に Key が付与されているか確認
2. ⚠️ `HomeKeys.myPageNav` - BottomNavigationBar のマイページアイテムの Key を確認
3. ⚠️ `MyPageKeys.screen` - マイページ画面の Scaffold に Key が付与されているか確認
4. ⚠️ `MyPageKeys.logoutButton` - ログアウトボタンの Key を確認
```

---

## PoC で検証すべきこと

### 1. 変換精度

- [ ] 仕様書の全手順がテストコードに反映されているか
- [ ] 期待結果が正しくアサーションに変換されているか
- [ ] 前提条件がセットアップに反映されているか

### 2. マッピングレポートの実用性

- [ ] レポートを見て、生成結果の妥当性を判断できるか
- [ ] ❌ / ⚠️ 項目から、次のアクションが明確か
- [ ] レビュアーが5分以内で確認できるか

### 3. Key 後付けの可否

- [ ] 既存画面に Key を後付けできるか
- [ ] Key 追加が既存コードを壊さないか
- [ ] Keys クラスが適切に生成されるか

### 4. Page Object パターンの適用可否

- [ ] Page Object が画面の操作を適切にカプセル化しているか
- [ ] UI 変更時に Page Object だけの修正で済むか
- [ ] シナリオテストが仕様書と読み比べやすいか

---

## PoC 実行手順

### 1. 準備

```bash
# Flutter プロジェクトのルートで実行
cd /path/to/flutter/project

# integration_test の依存を確認
grep -q 'integration_test' pubspec.yaml || echo "integration_test の追加が必要"
```

### 2. スキル実行

```
「ST-AUTH-001 のE2Eテストを生成して」
```

### 3. レビュー

1. マッピングレポートを確認
2. ⚠️ / ❌ 項目を確認
3. Key の追加を承認
4. テストコードの妥当性を確認

### 4. 実行

```bash
# テストを実行
flutter test integration_test/scenarios/st_auth_001_test.dart
```

### 5. 評価

- テストが実行できたか
- テストが意図通りの動作をしたか
- 失敗した場合、原因は何か（Key の問題？タイミング？仕様の解釈？）
