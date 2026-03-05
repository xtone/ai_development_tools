# 実プロジェクトで発見されたパターン集

## 概要

E2E テスト自動生成スキルの PoC を実プロジェクト（ic_card / mitsui_carshares_app）で実施した際に
発見されたパターンと対処法をまとめたドキュメント。
テンプレートの想定と異なるケースへの対応策を提供する。

---

## パターン 1: Firebase 初期化の integration_test 対応

### 問題の説明

Firebase を使用するアプリでは、`main()` 内で `Firebase.initializeApp()` が呼ばれる。
integration_test ではアプリを直接起動するため、Firebase の初期化がテスト環境で正しく
動作しない場合がある。特に以下の問題が発生する:

- `Firebase.initializeApp()` が二重に呼ばれるエラー
- テスト環境では Firebase サービスが利用できない
- `DefaultFirebaseOptions` が integration_test 用に設定されていない

### ic_card での実装例

```dart
// lib/main.dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  // ...
  runApp(const ProviderScope(child: MyApp()));
}
```

### テスト時の対処法

integration_test 用のエントリポイントを別途用意する。

```dart
// integration_test/helpers/app_launcher.dart
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mitsui_carshares_app/app.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class AppLauncher {
  static bool _firebaseInitialized = false;

  /// 未ログイン状態でアプリを起動する
  static Future<void> launchAsLoggedOut(WidgetTester tester) async {
    // Firebase の二重初期化を防ぐ
    if (!_firebaseInitialized) {
      await Firebase.initializeApp();
      _firebaseInitialized = true;
    }

    // 認証トークンをクリア
    // SharedPreferences / SecureStorage をリセット

    await tester.pumpWidget(
      const ProviderScope(
        child: MyApp(),
      ),
    );
    await tester.pumpAndSettle(const Duration(seconds: 5));
  }
}
```

### テンプレートの推奨パターン

Phase 0-1 でプロジェクト解析時に `firebase_core` の依存を検出した場合:

1. Firebase 初期化の二重呼び出し防止フラグを AppLauncher に追加する
2. `firebase_options.dart` の存在を確認する
3. テスト実行時には `firebase_core_platform_interface` のモックを検討する

---

## パターン 2: CustomTextFormField 等ラッパーの Key 伝播

### 問題の説明

多くのプロジェクトでは、`TextField` / `TextFormField` をラップした
カスタムウィジェットを使用している。このラッパーに Key を付与しても、
`tester.enterText(find.byKey(...), text)` が動作しないことがある。

原因: `enterText` は `EditableText` ウィジェットを探すが、Key はラッパーの
外側に付与されるため、Finder が `EditableText` に到達できない。

### ic_card での実装例

```dart
// lib/ui/common/widgets/custom_text_form_field.dart
class CustomTextFormField extends StatefulWidget {
  const CustomTextFormField({
    super.key,  // Key を受け取る
    this.controller,
    this.labelText,
    this.obscureText = false,
    this.keyboardType,
    this.onChanged,
    // ...
  });

  final TextEditingController? controller;
  final String? labelText;
  final bool obscureText;
  // ...

  @override
  State<CustomTextFormField> createState() => _CustomTextFormFieldState();
}

class _CustomTextFormFieldState extends State<CustomTextFormField> {
  @override
  Widget build(BuildContext context) {
    return TextFormField(  // ← 内部に TextFormField がある
      controller: widget.controller,
      obscureText: widget.obscureText,
      // ...
    );
  }
}
```

```dart
// lib/ui/auth/widgets/login_page.dart（Key 付与後）
CustomTextFormField(
  key: LoginKeys.driverIdPart1Field,  // super.key があるため直接付与
  controller: idPart1Controller,
  labelText: '運転者ID（前半）',
)
```

### テスト時の対処法

#### super.key パターン（推奨）

`super.key` を受け取るラッパーには直接 Key を付与し、Page Object 側で `find.descendant` を使用する。

```dart
// Page Object 内
Future<void> enterDriverIdPart1(String value) async {
  final editableText = find.descendant(
    of: find.byKey(LoginKeys.driverIdPart1Field),
    matching: find.byType(EditableText),
  );
  await tester.tap(editableText);
  await tester.enterText(editableText, value);
  await tester.pumpAndSettle();
}
```

#### KeyedSubtree パターン（super.key がない場合）

```dart
// Widget 側
KeyedSubtree(
  key: LoginKeys.emailField,
  child: LegacyCustomField(
    controller: emailController,
  ),
)

// Page Object 側（同じ find.descendant パターン）
Future<void> enterEmail(String email) async {
  final editableText = find.descendant(
    of: find.byKey(LoginKeys.emailField),
    matching: find.byType(EditableText),
  );
  await tester.tap(editableText);
  await tester.enterText(editableText, email);
  await tester.pumpAndSettle();
}
```

### テンプレートの推奨パターン

Phase 0-3 でカスタムウィジェット検出時に:

1. `super.key` の有無を確認する
2. `super.key` あり → 直接 Key 付与 + Page Object で `find.descendant`
3. `super.key` なし → `KeyedSubtree` ラップ + Page Object で `find.descendant`
4. Page Object テンプレートに `_enterTextInWrapper` ヘルパーメソッドを追加する

```dart
/// ラッパーウィジェット内の EditableText にテキストを入力するヘルパー
Future<void> _enterTextInWrapper(Finder wrapperFinder, String value) async {
  final editableText = find.descendant(
    of: wrapperFinder,
    matching: find.byType(EditableText),
  );
  await tester.tap(editableText);
  await tester.enterText(editableText, value);
  await tester.pumpAndSettle();
}
```

---

## パターン 3: Auto Route ナビゲーションパターン

### 問題の説明

Auto Route を使用するプロジェクトでは、ナビゲーションが `Navigator.push` ではなく
`context.router.push` / `context.router.replaceAll` で行われる。
integration_test ではルーターの初期化やタブ管理の挙動が標準の Navigator と異なる。

特に `AutoTabsScaffold` を使用したタブナビゲーションでは、
`BottomNavigationBar` の代わりにカスタムの `BottomNavigationTabItem` が使われることがある。

### ic_card での実装例

```dart
// lib/routing/routes/app_router.dart
@AutoRouterConfig()
class AppRouter extends RootStackRouter {
  @override
  List<AutoRoute> get routes => [
    AutoRoute(page: AuthRoute.page, initial: true),
    AutoRoute(
      page: MainRoute.page,
      children: [
        AutoRoute(page: HomeRoute.page),
        AutoRoute(page: ReservationRoute.page),
        AutoRoute(page: UsageRoute.page),
        AutoRoute(page: NotificationRoute.page),
        AutoRoute(page: MyPageRoute.page),
      ],
    ),
  ];
}

// lib/routing/widgets/main_page.dart
class MainPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return AutoTabsScaffold(
      routes: const [
        HomeRoute(),
        ReservationRoute(),
        UsageRoute(),
        NotificationRoute(),
        MyPageRoute(),
      ],
      bottomNavigationBuilder: (context, tabsRouter) {
        return BottomNavigationBar(
          currentIndex: tabsRouter.activeIndex,
          onTap: tabsRouter.setActiveIndex,
          items: [
            BottomNavigationTabItem(
              key: MainKeys.navHome,  // Key 付与
              icon: Icons.home,
              label: 'ホーム',
            ),
            // ...
            BottomNavigationTabItem(
              key: MainKeys.navMyPage,  // Key 付与
              icon: Icons.person,
              label: 'マイページ',
            ),
          ],
        );
      },
    );
  }
}
```

### テスト時の対処法

Auto Route のタブナビゲーションでは、ボトムナビのタップで画面遷移が発生する。
Page Object では通常の `tester.tap` で操作可能だが、以下に注意:

1. タブの切り替え後の `pumpAndSettle` に十分な時間を設定する
2. `AutoTabsScaffold` 内のタブは遅延ロードされる場合がある
3. ルート変更の検証には `context.router.current` ではなく、画面内の Key を使用する

```dart
// Page Object（MainPage）
Future<void> tapMyPage() async {
  await tester.tap(find.byKey(MainKeys.navMyPage));
  await tester.pumpAndSettle(const Duration(seconds: 3));
}
```

### テンプレートの推奨パターン

Phase 0-1 で `auto_route` を検出した場合:

1. `@AutoRouterConfig` のルート定義を解析し、タブ構造を把握する
2. `AutoTabsScaffold` の `bottomNavigationBuilder` を確認する
3. 各タブアイテムに Key を付与する
4. 遷移後の検証は遷移先画面の `screen` Key で行う（ルーター状態に依存しない）

---

## パターン 4: HookConsumerWidget のテスト考慮事項

### 問題の説明

Riverpod + Flutter Hooks を使用するプロジェクトでは、画面ウィジェットが
`HookConsumerWidget` として実装される。この場合、以下の考慮が必要:

- `ProviderScope` がテスト時に必要
- `useXxx` フック（`useState`, `useTextEditingController` 等）がウィジェットの
  ライフサイクルに依存
- Provider の初期状態がテスト結果に影響する

### ic_card での実装例

```dart
// lib/ui/auth/widgets/login_page.dart
class LoginPage extends HookConsumerWidget {
  const LoginPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Hooks によるコントローラー管理
    final idPart1Controller = useTextEditingController();
    final idPart2Controller = useTextEditingController();
    final passwordController = useTextEditingController();

    // Riverpod による状態管理
    final authState = ref.watch(authNotifierProvider);

    return Scaffold(
      key: LoginKeys.screen,
      body: Column(
        children: [
          CustomTextFormField(
            key: LoginKeys.driverIdPart1Field,
            controller: idPart1Controller,
          ),
          // ...
        ],
      ),
    );
  }
}
```

### テスト時の対処法

integration_test ではアプリ全体を起動するため、`ProviderScope` は
アプリのルートウィジェットに既に含まれている。
個別の Provider をモックする必要がある場合は `overrides` を使用する。

```dart
// integration_test/helpers/app_launcher.dart
static Future<void> launchAsLoggedOut(WidgetTester tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        // 必要に応じて Provider をオーバーライド
        // authTokenProvider.overrideWith((ref) => null),
      ],
      child: const MyApp(),
    ),
  );
  await tester.pumpAndSettle(const Duration(seconds: 5));
}
```

### テンプレートの推奨パターン

Phase 0-1 で `hooks_riverpod` を検出した場合:

1. `ProviderScope` を AppLauncher に含める
2. 認証状態に影響する Provider を特定し、必要に応じてオーバーライドする
3. `useTextEditingController` で管理されるフィールドでも、Key + `find.descendant` で操作可能
4. Provider の状態変更後の UI 更新には `pumpAndSettle` で待機する

---

## パターン 5: カスタムボトムナビゲーション

### 問題の説明

標準の `BottomNavigationBar` + `BottomNavigationBarItem` ではなく、
カスタムのタブアイテムウィジェットを使用しているプロジェクトがある。
カスタムウィジェットが `key` パラメータを受け取るかどうかを確認する必要がある。

### ic_card での実装例

```dart
// lib/routing/widgets/bottom_navigation_tab_item.dart
class BottomNavigationTabItem extends BottomNavigationBarItem {
  const BottomNavigationTabItem({
    super.key,  // BottomNavigationBarItem 経由で Key を受け取る
    required super.icon,
    required super.label,
    super.activeIcon,
  });
}
```

```dart
// 使用箇所（Key 付与後）
BottomNavigationTabItem(
  key: MainKeys.navMyPage,
  icon: const Icon(Icons.person_outline),
  activeIcon: const Icon(Icons.person),
  label: 'マイページ',
)
```

### テスト時の対処法

`BottomNavigationBarItem` は直接 Widget ツリーに現れないため、
Key が `BottomNavigationBar` 内のどの要素に反映されるかを確認する必要がある。

多くの場合、`BottomNavigationBarItem` の `key` は内部で生成される `InkWell` や
`Semantics` に伝播するため、`find.byKey` で見つけることができる。
動作しない場合は、`find.text('マイページ')` や `find.byIcon(Icons.person)` を代替手段として使う。

```dart
// Page Object
Future<void> tapMyPage() async {
  // Key が BottomNavigationBarItem に正しく伝播する場合
  await tester.tap(find.byKey(MainKeys.navMyPage));
  await tester.pumpAndSettle();
}

// Key が伝播しない場合のフォールバック
Future<void> tapMyPageFallback() async {
  await tester.tap(find.text('マイページ'));
  await tester.pumpAndSettle();
}
```

### テンプレートの推奨パターン

Phase 0-3 でカスタムボトムナビを検出した場合:

1. カスタムタブアイテムが `key` / `super.key` を受け取るか確認する
2. Key が Widget ツリー上で有効か（`find.byKey` で発見可能か）テスト実行時に確認する
3. Key が伝播しない場合は `find.text` をフォールバックとして使用する
4. フォールバック使用時はマッピングレポートに注記を追加する

---

## パターン 6: AuthWall パターン

### 問題の説明

一部のアプリでは、未ログイン状態で表示される「認証壁」（AuthWall）画面が存在する。
この場合、アプリ起動後に直接ログイン画面が表示されるのではなく、
AuthWall → ログインボタンタップ → ログイン画面 という2段階の遷移が必要。

この認証フローパターンはテンプレートの「直接ログイン画面」の想定と異なり、
AuthWall 用の Keys クラスと Page Object が追加で必要になる。

### ic_card での実装例

```dart
// lib/ui/auth/components/auth_wall.dart
class AuthWall extends HookConsumerWidget {
  const AuthWall({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authNotifierProvider);

    // ログイン済みなら子ウィジェット（通常画面）を表示
    if (authState.isAuthenticated) {
      return child;
    }

    // 未ログインなら AuthWall を表示
    return SafeArea(
      child: Scaffold(
        key: AuthWallKeys.screen,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // アプリロゴ
              const AppLogo(),
              const SizedBox(height: 32),
              // ログインボタン
              ElevatedButton(
                key: AuthWallKeys.loginButton,
                onPressed: () => context.router.push(const LoginRoute()),
                child: const Text('ログイン'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### テスト時の対処法

AuthWall を経由する認証フローのテストでは、以下の Page Object を追加で作成する。

```dart
// integration_test/page_objects/auth_wall_page.dart
class AuthWallPage {
  final WidgetTester tester;
  AuthWallPage(this.tester);

  Finder get screen => find.byKey(AuthWallKeys.screen);
  Finder get loginButton => find.byKey(AuthWallKeys.loginButton);

  Future<void> verifyDisplayed() async {
    await tester.pumpAndSettle(const Duration(seconds: 5));
    expect(screen, findsOneWidget);
  }

  Future<void> tapLogin() async {
    await tester.tap(loginButton);
    await tester.pumpAndSettle();
  }
}
```

テストシナリオでの使用:

```dart
// AuthWall → Login の遷移
await authWallPage.verifyDisplayed();
await authWallPage.tapLogin();
await loginPage.verifyDisplayed();

// ログアウト後は AuthWall に戻る（LoginPage ではなく）
await myPage.tapLogout();
await authWallPage.verifyDisplayed();  // LoginPage ではない！
```

### テンプレートの推奨パターン

Phase 0-3 で認証フロー判定時に:

1. `AuthWall` / `AuthGuard` / `AuthGate` 等の認証壁ウィジェットを検索する
2. 検出した場合、AuthWall 用の Keys と Page Object を自動生成に含める
3. ログアウト後の遷移先を AuthWall に設定する（LoginPage ではなく）
4. テストの手順数が標準より1-2ステップ増えることをマッピングレポートに反映する

---

## パターン 7: 辞書ベースの動的テキスト

### 問題の説明

一部のアプリでは、画面に表示するテキストをハードコードせず、
辞書（Dictionary）から動的に取得する。ic_card では `useUnifiedDictionaryByIndex`
フックを使用しており、テキストの内容がビルド時ではなく実行時に決定される。

この場合、`find.text('ログイン')` のようなテキストベースの Finder が
テスト環境で動作しない可能性がある。

### ic_card での実装例

```dart
// lib/ui/auth/widgets/login_page.dart
class LoginPage extends HookConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // 辞書からテキストを取得
    final dictionary = useUnifiedDictionaryByIndex(
      ref,
      screenId: 'login',
    );

    return Column(
      children: [
        Text(dictionary['login_title'] ?? 'ログイン'),  // 辞書から取得
        CustomTextFormField(
          key: LoginKeys.driverIdPart1Field,
          labelText: dictionary['driver_id_label'] ?? '運転者ID',  // 辞書から取得
        ),
        ElevatedButton(
          key: LoginKeys.loginButton,
          onPressed: _handleLogin,
          child: Text(dictionary['login_button'] ?? 'ログイン'),  // 辞書から取得
        ),
      ],
    );
  }
}
```

### テスト時の対処法

辞書ベースのテキストがテスト環境で正しく読み込まれるか確認する。
テキストベースの検索（`find.text`）は避け、Key ベースの検索（`find.byKey`）を
一貫して使用する。

```dart
// 悪い例: テキストベースの検索（辞書の内容に依存）
await tester.tap(find.text('ログイン'));  // 辞書が読み込まれないと失敗

// 良い例: Key ベースの検索（辞書に依存しない）
await tester.tap(find.byKey(LoginKeys.loginButton));  // 常に動作
```

テキスト表示の検証が必要な場合は、Key で要素を特定してからテキスト内容を検証する。

```dart
// Key で見つけた要素内のテキストを検証
Future<void> verifyLoginTitle(String expectedText) async {
  final titleFinder = find.byKey(LoginKeys.titleText);
  expect(titleFinder, findsOneWidget);

  // テキスト内容の検証（辞書の内容に依存）
  final textWidget = tester.widget<Text>(
    find.descendant(
      of: titleFinder,
      matching: find.byType(Text),
    ),
  );
  expect(textWidget.data, expectedText);
}
```

### テンプレートの推奨パターン

Phase 0-1 で辞書パターンを検出した場合:

1. `useUnifiedDictionaryByIndex` / `LocalizationDelegate` / `AppLocalizations` 等の使用を検出する
2. テキストベースの Finder を避け、Key ベースの Finder を優先する
3. テキスト内容の検証が仕様書で求められている場合のみ、Key + テキスト検証パターンを使用する
4. テスト環境での辞書初期化が必要か AppLauncher で確認する
5. マッピングレポートで辞書依存のステップに注記を追加する

---

## パターン一覧サマリー

| # | パターン | 検出タイミング | 影響範囲 |
|---|---------|-------------|---------|
| 1 | Firebase 初期化 | Phase 0-1 | AppLauncher |
| 2 | ラッパーウィジェットの Key 伝播 | Phase 0-3 | Key 付与 + Page Object |
| 3 | Auto Route ナビゲーション | Phase 0-1 | Page Object + Key 付与 |
| 4 | HookConsumerWidget | Phase 0-1 | AppLauncher |
| 5 | カスタムボトムナビゲーション | Phase 0-3 | Key 付与 + Page Object |
| 6 | AuthWall パターン | Phase 0-3 | Keys + Page Object + シナリオ |
| 7 | 辞書ベースの動的テキスト | Phase 0-1 | Page Object + マッピングレポート |

各パターンは Phase 0 の早い段階で検出し、以降の Phase で適切に対処することが重要。
Phase 0-3（カスタムウィジェットの検出）は、これらのパターンを網羅的に把握するための
重要なステップである。
