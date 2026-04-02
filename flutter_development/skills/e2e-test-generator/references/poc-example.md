# PoC 実行例: ST-AUTH-001（正常ログイン/ログアウト）— ic_card プロジェクト

## 概要

この文書は、E2E テスト自動生成スキルの PoC として ic_card プロジェクトで ST-AUTH-001 を対象にした場合の、
入力から出力までの完全な実行例を示す。

### ic_card プロジェクトの特徴

| 項目 | 内容 |
|------|------|
| パッケージ名 | `mitsui_carshares_app` |
| 状態管理 | Riverpod + Hooks（HookConsumerWidget） |
| ルーティング | Auto Route（`context.router`） |
| 認証フロー | AuthWall 経由（2段階: AuthWall → LoginPage） |
| ログインフィールド | 3フィールド（運転者ID前半 + 後半 + パスワード） |
| テキスト入力 | CustomTextFormField（カスタムラッパー StatefulWidget） |
| ボトムナビ | AutoTabsScaffold + BottomNavigationTabItem（カスタム） |
| ログアウト | ダイアログなし（直接ログアウト） |
| 既存 Key | ゼロ（全て新規追加） |

---

## 入力: テスト仕様書

### ST-AUTH-001: 正常ログイン/ログアウト

| 項目 | 内容 |
|------|------|
| 試験項目ID | ST-AUTH-001 |
| 試験内容 | 正しい認証情報でログインし、ログアウトできること |
| 前提条件 | 未ログイン状態、テストユーザー（CP000000 / 001 / TestPass123!）が存在 |

#### 手順と期待結果

| # | 手順 | 期待結果 |
|---|------|---------|
| 1 | アプリを起動する | AuthWall（認証壁）が表示される |
| 2 | 「ログイン」ボタンをタップする | ログイン画面が表示される |
| 3 | 運転者ID前半に「CP000000」を入力する | 入力値が表示される |
| 4 | 運転者ID後半に「001」を入力する | 入力値が表示される |
| 5 | パスワード欄に「TestPass123!」を入力する | マスクされた入力値が表示される |
| 6 | 「ログイン」ボタンをタップする | ローディング後、メイン画面が表示される |
| 7 | 下部ナビゲーションの「マイページ」をタップする | マイページ画面が表示される |
| 8 | 「ログアウト」ボタンをタップする（スクロール必要） | AuthWall に戻る |

---

## Phase 0: プロジェクト解析結果

### Step 0-1: プロジェクト構造

```
プロジェクト構造を解析しました：
- UI層: lib/ui/{module}/widgets/
- 状態管理: Riverpod + Hooks（HookConsumerWidget）
- ルーティング: Auto Route（AutoTabsScaffold）
- 既存Keys: なし（0ファイル）
- カスタムウィジェット: CustomTextFormField（super.key あり）
```

### Step 0-3: カスタムウィジェット検出結果

```
カスタムウィジェットを検出しました：
- テキスト入力: CustomTextFormField（super.key あり → 直接 Key 付与可能）
- 認証フロー: AuthWall 経由（lib/ui/auth/components/auth_wall.dart）
- ナビゲーション: AutoTabsScaffold + BottomNavigationTabItem
- ログアウト: 確認ダイアログなし（直接ログアウト）
```

### 対象画面のファイルパス

| 画面 | ファイルパス | ウィジェットクラス | 種類 |
|------|-----------|---------------|------|
| AuthWall | `lib/ui/auth/components/auth_wall.dart` | `AuthWall` | HookConsumerWidget + SafeArea |
| ログイン | `lib/ui/auth/widgets/login_page.dart` | `LoginPage` | HookConsumerWidget |
| メイン | `lib/routing/routes/app_router.dart` | （AutoTabsScaffold） | Auto Route 定義 |
| マイページ | `lib/ui/mypage/widgets/mypage_page.dart` | `MyPagePage` | HookConsumerWidget + SingleChildScrollView |

---

## 出力 1: Keys クラス（4ファイル）

### lib/ui/auth/components/auth_wall_keys.dart

```dart
import 'package:flutter/material.dart';

/// AuthWall（認証壁）画面のテスト用Key定義
///
/// E2Eテスト（integration_test）から画面要素を特定するために使用する。
/// Key値の命名規約: {screen}_{role}_{name}
abstract class AuthWallKeys {
  // 画面自体
  static const screen = Key('auth_wall_screen');

  // ボタン
  static const loginButton = Key('auth_wall_button_login');
}
```

### lib/ui/auth/widgets/login_keys.dart

```dart
import 'package:flutter/material.dart';

/// ログイン画面のテスト用Key定義
///
/// 3フィールドログイン: 運転者ID前半 + 後半 + パスワード
/// CustomTextFormField（super.key あり）に直接 Key を付与する。
abstract class LoginKeys {
  // 画面自体
  static const screen = Key('login_screen');

  // テキスト入力フィールド（分割フィールド）
  static const driverIdPart1Field = Key('login_field_driver_id_part1');
  static const driverIdPart2Field = Key('login_field_driver_id_part2');
  static const passwordField = Key('login_field_password');

  // ボタン
  static const loginButton = Key('login_button_submit');

  // テキスト表示
  static const errorText = Key('login_text_error');
}
```

### lib/routing/main_keys.dart

```dart
import 'package:flutter/material.dart';

/// メイン画面（タブナビゲーション）のテスト用Key定義
///
/// AutoTabsScaffold + BottomNavigationTabItem への Key 付与
abstract class MainKeys {
  // 画面自体
  static const screen = Key('main_screen');

  // ボトムナビゲーション
  static const navHome = Key('main_nav_home');
  static const navReservation = Key('main_nav_reservation');
  static const navUsage = Key('main_nav_usage');
  static const navNotification = Key('main_nav_notification');
  static const navMyPage = Key('main_nav_my_page');
}
```

### lib/ui/mypage/widgets/mypage_keys.dart

```dart
import 'package:flutter/material.dart';

/// マイページ画面のテスト用Key定義
///
/// SingleChildScrollView 内のメニュー項目。
/// ログアウトボタンは画面下部にあるため、スクロール対応が必要。
abstract class MyPageKeys {
  // 画面自体
  static const screen = Key('mypage_screen');

  // ボタン
  static const logoutButton = Key('mypage_button_logout');

  // メニュー項目
  static const menuProfile = Key('mypage_item_profile');
  static const menuBilling = Key('mypage_item_billing');
  static const menuCoupon = Key('mypage_item_coupon');
  static const menuSettings = Key('mypage_item_settings');
}
```

---

## 出力 2: Page Objects（4ファイル）

### integration_test/page_objects/auth_wall_page.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mitsui_carshares_app/ui/auth/components/auth_wall_keys.dart';

/// AuthWall（認証壁）画面の Page Object
///
/// ウィジェットクラス名「AuthWall」と衝突しないため、
/// 例外的に {Screen}Page 命名を使用。
class AuthWallPage {
  final WidgetTester tester;

  AuthWallPage(this.tester);

  // === Finder 定義 ===

  Finder get screen => find.byKey(AuthWallKeys.screen);
  Finder get loginButton => find.byKey(AuthWallKeys.loginButton);

  // === 検証メソッド ===

  /// AuthWall が表示されていることを検証する
  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle(const Duration(seconds: 5));
    expect(screen, findsOneWidget);
  }

  // === 操作メソッド ===

  /// ログインボタンをタップしてログイン画面に遷移する
  Future<void> tapLogin() async {
    await tester.tap(loginButton);
    await tester.pumpAndSettle();
  }
}
```

### integration_test/page_objects/login_page_object.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mitsui_carshares_app/ui/auth/widgets/login_keys.dart';

/// ログイン画面の Page Object
///
/// ウィジェットクラス名「LoginPage」との衝突を回避するため
/// LoginPageObject を使用する。
///
/// CustomTextFormField ラッパーを使用しているため、
/// テキスト入力には find.descendant パターンを使用する。
class LoginPageObject {
  final WidgetTester tester;

  LoginPageObject(this.tester);

  // === Finder 定義 ===

  Finder get screen => find.byKey(LoginKeys.screen);
  Finder get driverIdPart1Field => find.byKey(LoginKeys.driverIdPart1Field);
  Finder get driverIdPart2Field => find.byKey(LoginKeys.driverIdPart2Field);
  Finder get passwordField => find.byKey(LoginKeys.passwordField);
  Finder get loginButton => find.byKey(LoginKeys.loginButton);
  Finder get errorText => find.byKey(LoginKeys.errorText);

  // === 検証メソッド ===

  /// ログイン画面が表示されていることを検証する
  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle();
    expect(screen, findsOneWidget);
  }

  /// エラーメッセージが表示されていることを検証する
  Future<void> verifyErrorDisplayed() async {
    await tester.pumpAndSettle();
    expect(errorText, findsOneWidget);
  }

  // === 操作メソッド ===

  /// 運転者ID前半を入力する（CustomTextFormField ラッパー対応）
  Future<void> enterDriverIdPart1(String value) async {
    // CustomTextFormField の Key から内部の EditableText を特定
    final editableText = find.descendant(
      of: driverIdPart1Field,
      matching: find.byType(EditableText),
    );
    await tester.tap(editableText);
    await tester.enterText(editableText, value);
    await tester.pumpAndSettle();
  }

  /// 運転者ID後半を入力する（CustomTextFormField ラッパー対応）
  Future<void> enterDriverIdPart2(String value) async {
    final editableText = find.descendant(
      of: driverIdPart2Field,
      matching: find.byType(EditableText),
    );
    await tester.tap(editableText);
    await tester.enterText(editableText, value);
    await tester.pumpAndSettle();
  }

  /// パスワードを入力する（CustomTextFormField ラッパー対応）
  Future<void> enterPassword(String password) async {
    final editableText = find.descendant(
      of: passwordField,
      matching: find.byType(EditableText),
    );
    await tester.tap(editableText);
    await tester.enterText(editableText, password);
    await tester.pumpAndSettle();
  }

  /// ログインボタンをタップする
  Future<void> tapLogin() async {
    await tester.tap(loginButton);
    // API通信を伴うためタイムアウトを長めに設定
    await tester.pumpAndSettle(const Duration(seconds: 15));
  }

  // === 複合操作メソッド ===

  /// 運転者IDとパスワードを入力してログインする
  Future<void> login({
    required String driverIdPart1,
    required String driverIdPart2,
    required String password,
  }) async {
    await enterDriverIdPart1(driverIdPart1);
    await enterDriverIdPart2(driverIdPart2);
    await enterPassword(password);
    await tapLogin();
  }
}
```

### integration_test/page_objects/main_page.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mitsui_carshares_app/routing/main_keys.dart';

/// メイン画面（タブナビゲーション）の Page Object
///
/// AutoTabsScaffold + BottomNavigationTabItem による
/// カスタムボトムナビゲーションを操作する。
class MainPage {
  final WidgetTester tester;

  MainPage(this.tester);

  // === Finder 定義 ===

  Finder get screen => find.byKey(MainKeys.screen);
  Finder get navHome => find.byKey(MainKeys.navHome);
  Finder get navReservation => find.byKey(MainKeys.navReservation);
  Finder get navUsage => find.byKey(MainKeys.navUsage);
  Finder get navNotification => find.byKey(MainKeys.navNotification);
  Finder get navMyPage => find.byKey(MainKeys.navMyPage);

  // === 検証メソッド ===

  /// メイン画面が表示されていることを検証する
  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle();
    expect(screen, findsOneWidget);
  }

  // === 操作メソッド ===

  /// ホームタブをタップする
  Future<void> tapHome() async {
    await tester.tap(navHome);
    await tester.pumpAndSettle();
  }

  /// 予約タブをタップする
  Future<void> tapReservation() async {
    await tester.tap(navReservation);
    await tester.pumpAndSettle();
  }

  /// 利用タブをタップする
  Future<void> tapUsage() async {
    await tester.tap(navUsage);
    await tester.pumpAndSettle();
  }

  /// 通知タブをタップする
  Future<void> tapNotification() async {
    await tester.tap(navNotification);
    await tester.pumpAndSettle();
  }

  /// マイページタブをタップする
  Future<void> tapMyPage() async {
    await tester.tap(navMyPage);
    await tester.pumpAndSettle();
  }
}
```

### integration_test/page_objects/mypage_page_object.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mitsui_carshares_app/ui/mypage/widgets/mypage_keys.dart';

/// マイページ画面の Page Object
///
/// ウィジェットクラス名「MyPagePage」との衝突を回避するため
/// MyPagePageObject を使用する。
///
/// SingleChildScrollView 内にメニュー項目が並んでおり、
/// ログアウトボタンは画面下部にあるためスクロール対応が必要。
class MyPagePageObject {
  final WidgetTester tester;

  MyPagePageObject(this.tester);

  // === Finder 定義 ===

  Finder get screen => find.byKey(MyPageKeys.screen);
  Finder get logoutButton => find.byKey(MyPageKeys.logoutButton);
  Finder get menuProfile => find.byKey(MyPageKeys.menuProfile);

  // === 検証メソッド ===

  /// マイページ画面が表示されていることを検証する
  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle();
    expect(screen, findsOneWidget);
  }

  // === 操作メソッド ===

  /// ログアウトボタンをタップする（スクロール対応）
  ///
  /// ログアウトボタンは SingleChildScrollView の下部にあり、
  /// 初期表示では画面外にある可能性があるため scrollUntilVisible を使用する。
  /// ic_card では確認ダイアログなしで直接ログアウトされる。
  Future<void> tapLogout() async {
    // ログアウトボタンが画面外にある可能性があるためスクロール
    await tester.scrollUntilVisible(
      logoutButton,
      300,  // スクロール量（ピクセル）
      scrollable: find.byType(SingleChildScrollView).first,
    );
    await tester.tap(logoutButton);
    // ログアウトAPI通信の待機
    await tester.pumpAndSettle(const Duration(seconds: 5));
  }
}
```

---

## 出力 3: シナリオテスト

### integration_test/scenarios/st_auth_001_test.dart

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import '../page_objects/auth_wall_page.dart';
import '../page_objects/login_page_object.dart';
import '../page_objects/main_page.dart';
import '../page_objects/mypage_page_object.dart';
import '../helpers/app_launcher.dart';

/// ST-AUTH-001: 正常ログイン/ログアウト（ic_card）
///
/// 試験内容: 正しい認証情報でログインし、ログアウトできること
/// 前提条件: 未ログイン状態、テストユーザーが存在
///
/// ic_card 固有のフロー:
///   AuthWall → LoginPage（3フィールド） → MainPage → MyPage → ログアウト → AuthWall
///
/// 仕様書: テスト仕様書 > 認証系 > ST-AUTH-001
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  // テストデータ（仕様書の前提条件より）
  const testDriverIdPart1 = 'CP000000';
  const testDriverIdPart2 = '001';
  const testPassword = 'TestPass123!';

  group('ST-AUTH-001: 正常ログイン/ログアウト', () {
    testWidgets('正しい認証情報でログインし、ログアウトできること', (tester) async {
      // === セットアップ ===
      // 前提条件: 未ログイン状態
      await AppLauncher.launchAsLoggedOut(tester);

      // Page Objects
      final authWallPage = AuthWallPage(tester);
      final loginPage = LoginPageObject(tester);
      final mainPage = MainPage(tester);
      final myPagePage = MyPagePageObject(tester);

      // === 手順 1: アプリを起動する ===
      // 期待結果 1: AuthWall（認証壁）が表示される
      await authWallPage.verifyDisplayed();

      // === 手順 2: 「ログイン」ボタンをタップする ===
      // 期待結果 2: ログイン画面が表示される
      await authWallPage.tapLogin();
      await loginPage.verifyDisplayed();

      // === 手順 3: 運転者ID前半に「CP000000」を入力する ===
      // 期待結果 3: 入力値が表示される
      await loginPage.enterDriverIdPart1(testDriverIdPart1);

      // === 手順 4: 運転者ID後半に「001」を入力する ===
      // 期待結果 4: 入力値が表示される
      await loginPage.enterDriverIdPart2(testDriverIdPart2);

      // === 手順 5: パスワード欄に入力する ===
      // 期待結果 5: マスクされた入力値が表示される
      await loginPage.enterPassword(testPassword);

      // === 手順 6: 「ログイン」ボタンをタップする ===
      // 期待結果 6: ローディング後、メイン画面が表示される
      await loginPage.tapLogin();
      await mainPage.verifyDisplayed();

      // === 手順 7: 下部ナビゲーションの「マイページ」をタップする ===
      // 期待結果 7: マイページ画面が表示される
      await mainPage.tapMyPage();
      await myPagePage.verifyDisplayed();

      // === 手順 8: 「ログアウト」ボタンをタップする（スクロール必要） ===
      // 期待結果 8: AuthWall に戻る（確認ダイアログなし）
      await myPagePage.tapLogout();
      await authWallPage.verifyDisplayed();
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
- **生成日時**: 2025-XX-XX
- **対象画面**: AuthWall, LoginPage, MainPage（タブナビ）, MyPagePage
- **プロジェクト**: ic_card（mitsui_carshares_app）
- **生成ファイル**:
  - `integration_test/scenarios/st_auth_001_test.dart`
  - `integration_test/page_objects/auth_wall_page.dart`
  - `integration_test/page_objects/login_page_object.dart`
  - `integration_test/page_objects/main_page.dart`
  - `integration_test/page_objects/mypage_page_object.dart`

## ステップ対応表

| # | 種別 | 仕様ステップ | 生成アクション | Key | 状態 | 備考 |
|---|------|------------|-------------|-----|------|------|
| 1 | 検証 | AuthWall が表示される | `authWallPage.verifyDisplayed()` | `AuthWallKeys.screen` | 🆕 | 新規追加 |
| 2 | 操作 | ログインボタンをタップ | `authWallPage.tapLogin()` | `AuthWallKeys.loginButton` | 🆕 | 新規追加 |
| 2 | 検証 | ログイン画面が表示される | `loginPage.verifyDisplayed()` | `LoginKeys.screen` | 🆕 | 新規追加 |
| 3 | 操作 | 運転者ID前半を入力 | `loginPage.enterDriverIdPart1(...)` | `LoginKeys.driverIdPart1Field` | 🆕 | find.descendant パターン |
| 4 | 操作 | 運転者ID後半を入力 | `loginPage.enterDriverIdPart2(...)` | `LoginKeys.driverIdPart2Field` | 🆕 | find.descendant パターン |
| 5 | 操作 | パスワードを入力 | `loginPage.enterPassword(...)` | `LoginKeys.passwordField` | 🆕 | find.descendant パターン |
| 6 | 操作 | ログインボタンをタップ | `loginPage.tapLogin()` | `LoginKeys.loginButton` | 🆕 | pumpAndSettle 15秒 |
| 6 | 検証 | メイン画面が表示される | `mainPage.verifyDisplayed()` | `MainKeys.screen` | 🆕 | 新規追加 |
| 7 | 操作 | マイページをタップ | `mainPage.tapMyPage()` | `MainKeys.navMyPage` | 🆕 | BottomNavigationTabItem |
| 7 | 検証 | マイページが表示される | `myPagePage.verifyDisplayed()` | `MyPageKeys.screen` | 🆕 | 新規追加 |
| 8 | 操作 | ログアウトをタップ | `myPagePage.tapLogout()` | `MyPageKeys.logoutButton` | 🆕 | scrollUntilVisible 使用 |
| 8 | 検証 | AuthWall に戻る | `authWallPage.verifyDisplayed()` | `AuthWallKeys.screen` | 🆕 | ダイアログなし |

## 前提条件マッピング

| 仕様の前提条件 | 実現方法 | 状態 |
|--------------|---------|------|
| 未ログイン状態 | `AppLauncher.launchAsLoggedOut(tester)` | 🆕 |
| テストユーザーが存在 | テストデータとして定義（CP000000/001/TestPass123!） | 🆕 |

## サマリー

| 指標 | 値 |
|------|---|
| 総アクション数 | 12 |
| 🆕 New Key | 12 (100%) |
| ✅ Existing Key | 0 (0%) |
| ⚠️ Key推定 | 0 (0%) |
| ❌ Key該当なし | 0 (0%) |
| **カバレッジ** | **100%** |

### 必要なアクション

全て 🆕 New Key のため、Key 追加は完了済み。以下の確認のみ必要:

1. 🆕 各 Key が正しいウィジェットに付与されているか確認
2. 🆕 CustomTextFormField の find.descendant パターンが動作するか確認
3. 🆕 scrollUntilVisible でログアウトボタンに到達できるか確認
```

---

## 発見した課題と対処法

### 課題 1: CustomTextFormField への直接 enterText が動作しない

**問題**: `tester.enterText(find.byKey(LoginKeys.driverIdPart1Field), value)` が動作しない。
CustomTextFormField はラッパーウィジェットであり、Key は外側のラッパーに付与されるが、
`enterText` は内部の `EditableText` に対して実行する必要がある。

**対処法**: `find.descendant` パターンを使用する。

```dart
final editableText = find.descendant(
  of: find.byKey(LoginKeys.driverIdPart1Field),
  matching: find.byType(EditableText),
);
await tester.enterText(editableText, value);
```

### 課題 2: ログアウトボタンが画面外

**問題**: MyPagePage は SingleChildScrollView 内にメニュー項目が並んでおり、
ログアウトボタンは画面下部にあるため初期表示では見えない。
`tester.tap(logoutButton)` が「widget not found」エラーになる。

**対処法**: `scrollUntilVisible` を使用する。

```dart
await tester.scrollUntilVisible(
  logoutButton,
  300,
  scrollable: find.byType(SingleChildScrollView).first,
);
```

### 課題 3: AuthWall の存在

**問題**: テンプレートでは「アプリ起動 → ログイン画面」を想定していたが、
ic_card では「アプリ起動 → AuthWall → ログイン画面」の2段階フロー。
AuthWall 用の Keys と Page Object が追加で必要。

**対処法**: Phase 0-3 で認証フローパターンを事前に検出し、AuthWall 用の
Keys クラスと Page Object を追加生成する。

### 課題 4: ログアウト後の遷移先

**問題**: テンプレートでは「ログアウト → 確認ダイアログ → ログイン画面」を想定していたが、
ic_card では「ログアウト → AuthWall」（ダイアログなし、遷移先も異なる）。

**対処法**: Phase 0-3 でログアウトフローを事前に確認し、テストの期待結果を適切に調整する。

### 課題 5: Page Object クラス名の衝突

**問題**: `LoginPage` をPage Object クラス名にすると、アプリの `LoginPage` ウィジェットと
名前が衝突し、import 時に曖昧になる。

**対処法**: Page Object クラス名を `{Screen}PageObject` とする。
`LoginPage` → `LoginPageObject`、`MyPagePage` → `MyPagePageObject`。
ウィジェットクラス名と衝突しない場合のみ `{Screen}Page` を許容（例: `AuthWallPage`）。

### 課題 6: 分割フィールドの命名

**問題**: 運転者IDが2つのフィールドに分割されているため、
`login_field_driver_id` だけでは区別できない。

**対処法**: `_part{N}` サフィックスで区別する。
`login_field_driver_id_part1`、`login_field_driver_id_part2`。

---

## PoC から得られた知見

### テンプレートへのフィードバック

| 項目 | テンプレートの想定 | ic_card の実態 | 対応 |
|------|-----------------|--------------|------|
| ログインフィールド | email + password（2フィールド） | driverIdPart1 + driverIdPart2 + password（3フィールド） | 3フィールドテンプレート追加 |
| 認証フロー | 直接 LoginPage | AuthWall → LoginPage（2段階） | AuthWall フローテンプレート追加 |
| テキスト入力 | 生の TextField | CustomTextFormField（ラッパー） | find.descendant パターン追加 |
| ナビゲーション | Navigator.push | Auto Route（context.router） | Auto Route 対応記載 |
| ボトムナビ | BottomNavigationBar | BottomNavigationTabItem（カスタム） | カスタムナビ Key 付与記載 |
| ログアウト | ボタン → 確認ダイアログ → ログアウト | ボタン → 直接ログアウト（ダイアログなし） | ダイアログなしテンプレート追加 |
| 既存 Key | 一部既存 | ゼロ（全て新規追加） | 🆕 New Key ステータス追加 |
| Page Object 命名 | `{Screen}Page` | `{Screen}PageObject` | 命名規則更新 |
| テキスト入力方法 | `tester.enterText(finder, text)` | `find.descendant(of:matching:)` パターン | ラッパー対応パターン追加 |
| スクロール | 不要 | `scrollUntilVisible` 必要 | スクロール対応パターン追加 |

### 実行結果の評価

- **変換精度**: 仕様書の全8手順がテストコードに反映された
- **マッピングレポート**: 全 🆕 ステータスにより、レビューが明確
- **Key 後付け**: CustomTextFormField の `super.key` により、全てのフィールドに Key を付与できた
- **Page Object パターン**: find.descendant パターンにより、カスタムウィジェットにも対応できた
