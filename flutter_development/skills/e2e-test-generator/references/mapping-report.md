# マッピングレポート フォーマット

## 概要

マッピングレポートは、テスト仕様書のステップと生成されたテストコードの対応関係を可視化するドキュメント。
**人間がレビューするための唯一のチェックポイント**であり、テスト生成の精度を保証する。

---

## フォーマット

### ヘッダー

```markdown
# マッピングレポート

- **テストID**: ST-AUTH-001
- **試験内容**: 正常ログイン/ログアウト
- **生成日時**: 2024-XX-XX
- **対象画面**: LoginScreen, HomeScreen, MyPageScreen
- **生成ファイル**:
  - `integration_test/scenarios/st_auth_001_test.dart`
  - `integration_test/page_objects/login_page.dart`
  - `integration_test/page_objects/home_page.dart`
  - `integration_test/page_objects/my_page_page.dart`
```

### マッピングテーブル

```markdown
## ステップ対応表

| # | 種別 | 仕様ステップ | 生成アクション | Key | 状態 | 備考 |
|---|------|------------|-------------|-----|------|------|
| 1 | 検証 | ログイン画面が表示される | `loginPage.verifyDisplayed()` | `LoginKeys.screen` | ✅ | |
| 2 | 操作 | メールアドレスを入力する | `loginPage.enterEmail('test@example.com')` | `LoginKeys.emailField` | ✅ | |
| 3 | 操作 | パスワードを入力する | `loginPage.enterPassword('Test1234!')` | `LoginKeys.passwordField` | ✅ | |
| 4 | 操作 | ログインボタンをタップする | `loginPage.tapLogin()` | `LoginKeys.loginButton` | ✅ | |
| 5 | 検証 | ホーム画面が表示される | `homePage.verifyDisplayed()` | `HomeKeys.screen` | ⚠️ | 画面コードから推定 |
| 6 | 操作 | マイページアイコンをタップ | `homePage.tapMyPageIcon()` | `HomeKeys.myPageIcon` | ❌ | Key未定義 |
| 7 | 操作 | ログアウトボタンをタップ | `myPagePage.tapLogout()` | `MyPageKeys.logoutButton` | ❌ | Key未定義 |
| 7 | 検証 | ログイン画面に戻る | `loginPage.verifyDisplayed()` | `LoginKeys.screen` | ✅ | |
```

### 状態の定義

```markdown
## 状態の定義

| 状態 | 意味 | 対応 |
|------|------|------|
| ✅ Key一致 | Keys クラスに定義済みの Key と完全一致 | そのまま使用可能 |
| ⚠️ Key推定 | 画面コードの構造から Key を推定した | **要確認**: 推定が正しいか確認してください |
| ❌ Key該当なし | 対応する Key が見つからない | **要対応**: Key の追加が必要です |
| 🆕 New Key | 既存 Key がゼロの画面に新規追加した Key | Key追加済み。テスト実行可能 |
```

### 前提条件マッピング

```markdown
## 前提条件マッピング

| 仕様の前提条件 | 実現方法 | 状態 |
|--------------|---------|------|
| 未ログイン状態 | `AppLauncher.launchAsLoggedOut(tester)` | ✅ |
| テストユーザーが存在 | テストデータとして定義 | ✅ |
```

### サマリー

```markdown
## サマリー

| 指標 | 値 |
|------|---|
| 総ステップ数 | 8 |
| ✅ Key一致 | 5 (62.5%) |
| ⚠️ Key推定 | 1 (12.5%) |
| ❌ Key該当なし | 2 (25.0%) |
| **カバレッジ** | **75.0%** |

### 必要なアクション

1. ❌ `HomeKeys.myPageIcon` を追加する
   - 対象: `lib/ui/home/home_screen.dart` のマイページアイコン
2. ❌ `MyPageKeys.logoutButton` を追加する
   - 対象: `lib/ui/my_page/my_page_screen.dart` のログアウトボタン
3. ⚠️ `HomeKeys.screen` の Key が正しいか確認する
```

---

## レポートのレビュー手順

### レビュアーが確認すべきこと

1. **✅ 項目**: 仕様のステップと生成アクションが意味的に一致しているか
2. **⚠️ 項目**: 推定された Key が正しい要素を指しているか
3. **❌ 項目**: Key を追加すべき要素が正しく特定されているか
4. **前提条件**: テストの初期状態が仕様の前提条件を満たしているか

### 承認基準

| カバレッジ | 判定 |
|-----------|------|
| 100%（全✅） | そのままテスト実行可能 |
| 80%以上（⚠️あり、❌なし） | ⚠️を確認後、テスト実行可能 |
| 80%未満（❌あり） | Key追加後に再生成が必要 |

---

## Key ゼロプロジェクトのマッピングレポート

既存の Key が全くないプロジェクトでは、全ステップが 🆕 New Key ステータスとなる。
この場合のサマリー例:

```markdown
## サマリー

| 指標 | 値 |
|------|---|
| 総アクション数 | 12 |
| 🆕 New Key | 12 (100%) |
| ✅ Existing Key | 0 (0%) |
| ⚠️ Key推定 | 0 (0%) |
| ❌ Key該当なし | 0 (0%) |
| **カバレッジ** | **100%** |
```

🆕 は全て新規追加された Key であるため、Key の妥当性確認のみが必要。
❌ や ⚠️ が存在しないため、追加アクションは不要。

---

## ファイル配置

```
integration_test/
└── reports/
    ├── st_auth_001_mapping.md
    ├── st_auth_002_mapping.md
    └── st_rsv_001_mapping.md
```

### ファイル命名

```
{test_id}_mapping.md
```

テスト ID を snake_case に変換し、`_mapping.md` サフィックスを付ける。
