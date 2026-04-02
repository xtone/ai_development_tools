# Key 規約ガイド

## 概要

Flutter E2E テストにおける Key の命名規約と付与ルール。
Key は integration_test からUI要素を特定するための識別子であり、テストの安定性に直結する。

---

## Key クラスの定義

### ファイル配置

画面の Dart ファイルと同じディレクトリに配置する。

```
lib/ui/auth/
├── login_screen.dart
└── login_keys.dart      ← Keys クラス
```

### クラス定義

```dart
/// ログイン画面のテスト用Key定義
///
/// E2Eテスト（integration_test）から画面要素を特定するために使用する。
/// Key値の命名規約: {screen}_{role}_{name}
abstract class LoginKeys {
  // 画面自体
  static const screen = Key('login_screen');

  // テキスト入力フィールド
  static const emailField = Key('login_field_email');
  static const passwordField = Key('login_field_password');

  // ボタン
  static const loginButton = Key('login_button_submit');
  static const forgotPasswordButton = Key('login_button_forgot_password');

  // テキスト表示
  static const errorText = Key('login_text_error');

  // ダイアログ
  static const errorDialog = Key('login_dialog_error');
}
```

### ルール

1. **`abstract class`** を使用する（インスタンス化しない）
2. クラス名は `{Screen}Keys`（PascalCase）
3. フィールドは `static const`
4. Key 値は `{screen}_{role}_{name}`（snake_case）

---

## Key 値の命名規約

### フォーマット

```
{screen}_{role}_{name}
```

### screen（画面名）

画面のファイル名から `_screen.dart` / `_page.dart` を除いた部分。

| ファイル名 | screen |
|-----------|--------|
| `login_screen.dart` | `login` |
| `home_screen.dart` | `home` |
| `reservation_detail_screen.dart` | `reservation_detail` |
| `my_page_screen.dart` | `my_page` |

### role（要素の役割）

| role | 用途 | Flutter Widget 例 |
|------|------|-------------------|
| `screen` | 画面自体（Scaffold） | `Scaffold` |
| `field` | テキスト入力 | `TextField`, `TextFormField` |
| `button` | ボタン | `ElevatedButton`, `TextButton`, `IconButton`, `GestureDetector` |
| `text` | テキスト表示 | `Text`, `RichText` |
| `image` | 画像表示 | `Image`, `CachedNetworkImage` |
| `list` | リスト全体 | `ListView`, `GridView` |
| `item` | リストの個別アイテム | リスト内の各行 Widget |
| `card` | カード | `Card`, タップ可能なコンテナ |
| `tab` | タブ | `Tab`, `TabBar` のタブ |
| `switch` | トグルスイッチ | `Switch`, `CupertinoSwitch` |
| `checkbox` | チェックボックス | `Checkbox` |
| `radio` | ラジオボタン | `Radio` |
| `dropdown` | ドロップダウン | `DropdownButton` |
| `dialog` | ダイアログ | `AlertDialog`, `showDialog` |
| `snackbar` | スナックバー | `SnackBar` |
| `icon` | アイコン（タップ不可） | `Icon` |
| `indicator` | インジケーター | `CircularProgressIndicator` |
| `nav` | ナビゲーション要素 | `BottomNavigationBar` のアイテム |
| `section` | セクション区切り | セクションヘッダー、グループ |

### name（要素名）

操作や検証の対象を表す名前。簡潔で一意になるようにする。

```
良い例: email, password, submit, welcome_message, reservation_list
悪い例: field1, btn, txt, a, container
```

---

## Key の付与対象

### 必須で Key を付与する要素

| 操作 | 対象 Widget | 例 |
|------|------------|---|
| タップする | ボタン、リンク、カード | `LoginKeys.loginButton` |
| テキスト入力する | TextField | `LoginKeys.emailField` |
| テキスト表示を検証する | Text | `HomeKeys.welcomeText` |
| 画面表示を検証する | Scaffold / 最上位 Widget | `LoginKeys.screen` |
| 存在を検証する | 任意のWidget | `HomeKeys.notificationIcon` |

### Key を付与しない要素

- 装飾のみの Widget（Padding, SizedBox, Container 等）
- テストで操作・検証しない要素
- レイアウト用の Widget（Row, Column, Stack 等）

---

## Key の付与方法

### Widget への付与

```dart
// Scaffold（画面自体）
Scaffold(
  key: LoginKeys.screen,
  // ...
)

// TextField
TextField(
  key: LoginKeys.emailField,
  decoration: const InputDecoration(labelText: 'メールアドレス'),
)

// ElevatedButton
ElevatedButton(
  key: LoginKeys.loginButton,
  onPressed: _handleLogin,
  child: const Text('ログイン'),
)

// Text（表示検証）
Text(
  'ようこそ',
  key: HomeKeys.welcomeText,
)
```

---

## ラッパーウィジェットの Key 付与

### カスタムウィジェットへの Key 伝播

プロジェクトで独自のラッパーウィジェットを使用している場合の Key 付与パターン。

#### super.key を受け取るラッパー

`super.key` を受け取る `StatefulWidget` / `StatelessWidget` には直接 Key を付与できる。

```dart
// カスタムウィジェットの定義（既存コード）
class CustomTextFormField extends StatefulWidget {
  const CustomTextFormField({
    super.key,  // ← Key を受け取る
    this.controller,
    // ...
  });
}

// Key の付与
CustomTextFormField(
  key: LoginKeys.driverIdPart1Field,  // 直接付与可能
  controller: idPart1Controller,
)
```

#### super.key を受け取らないラッパー

Key を受け取らないウィジェットの場合、外側に `KeyedSubtree` でラップする。

```dart
KeyedSubtree(
  key: LoginKeys.emailField,
  child: LegacyTextField(
    controller: emailController,
  ),
)
```

### 分割フィールドの命名規約

1つの論理入力が複数フィールドに分割されている場合の命名:

```
{screen}_field_{name}_part{N}

例:
login_field_driver_id_part1   ← 運転者ID前半（CP000000）
login_field_driver_id_part2   ← 運転者ID後半（001）
```

パート番号は入力順に 1 から採番する。

---

### リストアイテムへの付与

動的なリストでは、ユニークな識別子を含める。

```dart
ListView.builder(
  key: HomeKeys.reservationList,
  itemBuilder: (context, index) {
    final reservation = reservations[index];
    return Card(
      // リストアイテムは Key 値にインデックスや ID を付与
      key: Key('home_item_reservation_${reservation.id}'),
      child: // ...
    );
  },
)
```

---

## 既存画面への Key 後付け手順

AI がテスト生成時に Key 不足を検出した場合のフロー：

1. **検出**: 仕様ステップに対応する Key がない要素を特定
2. **提案**: 不足 Key の一覧をマッピングレポートの ❌ として表示
3. **承認**: ユーザーが追加を承認
4. **生成**: Keys クラスの作成 + Widget への Key 付与
5. **差分表示**: 変更内容をユーザーに表示

```
「LoginScreen に以下の Key を追加します：

+++ lib/ui/auth/login_keys.dart (新規作成)
+ abstract class LoginKeys {
+   static const screen = Key('login_screen');
+   static const emailField = Key('login_field_email');
+   static const passwordField = Key('login_field_password');
+   static const loginButton = Key('login_button_submit');
+ }

--- lib/ui/auth/login_screen.dart
  Scaffold(
+   key: LoginKeys.screen,
    body: Column(
      children: [
        TextField(
+         key: LoginKeys.emailField,
          decoration: ...
```

---

## プロジェクト間の Key 衝突防止

screen 部分がプロジェクト内で一意であれば、Key の衝突は起きない。
同名画面がある場合はモジュールプレフィックスを検討する。

```
// 通常
login_field_email

// モジュール衝突がある場合
auth_login_field_email
admin_login_field_email
```
