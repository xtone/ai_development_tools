---
name: e2e-test-generator
description: |
  テスト仕様書（Excel/Notion）からFlutter integration_testコードを自動生成するスキル。
  Page Objectパターン + Key規約に基づき、仕様ステップとコードの対応を示すマッピングレポートも生成する。
  「E2Eテストを生成」「テスト仕様からテストコードを作って」「integration_testを生成」などの発言で発動。
---

# Flutter E2E テスト自動生成スキル

## 目的

テスト仕様書（Excel / Notion）を Source of Truth として、Flutter の integration_test コードを自動生成する。
テストコードは「自然言語仕様の Dart へのデコード結果」であり、使い捨ての中間生成物として扱う。

## 核心思想

> 「壊れにくくする」のではなく「再生成コストを限りなくゼロにする」

- テスト失敗 → **コードがバグっている** → コードを直す（テストは正しい）
- 仕様変更 → **テストが古い** → テストを再生成（仕様が正しい）
- テストコードを手で保守しない。仕様書を更新し、テストを再生成する。

## 使用タイミング

以下の発言で発動：
- 「E2E テストを生成して」「integration_test を作って」
- 「テスト仕様書からテストコードを生成」
- 「ST-AUTH-001 のテストを生成して」
- 「マッピングレポートを作成」

## 前提条件

- Flutter プロジェクトであること
- テスト仕様書が存在すること（Excel ファイルまたは Notion ページ）
- `integration_test/` ディレクトリが使用可能であること

---

## 実行フロー

### Phase 0: プロジェクト解析（必須・最初に実行）

#### Step 0-1: プロジェクト構造の確認

```
1. pubspec.yaml を読み込み、以下を検出：
   - flutter_test / integration_test の依存
   - 状態管理（riverpod, bloc, provider 等）
   - ルーティング（auto_route, go_router 等）

2. lib/ のディレクトリ構造を解析：
   - 画面ファイルのパス（lib/ui/, lib/presentation/, lib/features/ 等）
   - 既存の Keys クラス（*_keys.dart）
   - 既存の integration_test/

3. 結果をユーザーに確認：
   「プロジェクト構造を解析しました：
   - UI層: lib/ui/{module}/
   - 状態管理: Riverpod
   - ルーティング: auto_route
   - 既存Keys: なし / 3ファイル検出
   この認識で合っていますか？」
```

**ここでユーザーの回答を待つ。次のステップに進まない。**

#### Step 0-2: Key 規約の確認

既存の Key 運用を確認し、Key 規約を提案する。

```
既存の Key を検索：
- `Key('...')` や `ValueKey('...')` のパターン
- 既存の Keys クラス

結果に応じて：
- 既存規約あり → それに従う
- 既存規約なし → 標準規約を提案（references/key-convention.md 参照）
```

**ここでユーザーの回答を待つ。**

#### Step 0-3: カスタムウィジェットの検出

プロジェクト固有のウィジェットパターンを事前に把握する。

```
1. ラッパーウィジェットの検出:
   - CustomTextFormField 等のカスタム入力ウィジェットを検索
   - `super.key` の有無を確認（Key 伝播の可否判定）
   - Key を受け取れないラッパーには KeyedSubtree での対応が必要

2. 認証フローパターンの判定:
   - 直接ログイン画面パターン: アプリ起動 → LoginPage
   - AuthWall 経由パターン: アプリ起動 → AuthWall → LoginPage（2段階認証フロー）
   - AuthWall がある場合、AuthWall 用の Keys / Page Object も必要

3. テキスト入力ウィジェットの種類判定:
   - 生の TextField / TextFormField → tester.enterText() が直接使用可能
   - カスタムラッパー（CustomTextFormField 等）→ find.descendant パターンが必要

4. 結果をユーザーに確認：
   「カスタムウィジェットを検出しました：
   - テキスト入力: CustomTextFormField（super.key あり → 直接 Key 付与可能）
   - 認証フロー: AuthWall 経由（2段階）
   - ナビゲーション: AutoTabsScaffold + BottomNavigationTabItem
   この認識で合っていますか？」
```

**ここでユーザーの回答を待つ。**

---

### Phase 1: テスト仕様書の読み取り

#### Excel の場合

1. ユーザーにファイルパスを確認
2. Excel ファイルを解析し、以下のカラムを特定：
   - 試験項目ID（例: `ST-AUTH-001`）
   - 試験内容（シナリオの説明）
   - 前提条件（ログイン状態、データ等）
   - 手順（番号付き操作ステップ）
   - 期待結果（番号付き期待値）
3. 解析結果をユーザーに表示して確認

#### Notion の場合

1. Notion MCP を使用してページ/データベースを読み取り
2. 同様のカラム構造を特定
3. 解析結果をユーザーに表示して確認

**重要: 手順と期待結果は番号で対応付ける。**

```
「テスト仕様を読み取りました：

ST-AUTH-001: 正常ログイン/ログアウト
- 前提条件: 未ログイン状態
- 手順: 7ステップ
- 期待結果: 7項目
- 対象画面: ログイン画面、ホーム画面、マイページ

この仕様でテストを生成しますか？」
```

**ここでユーザーの回答を待つ。**

---

### Phase 2: 画面コード解析 + Key マッピング

#### Step 2-1: 対象画面の特定

仕様書の手順から、操作対象の画面を推定する。

```
仕様: 「ログイン画面でメールアドレスを入力」
  → ログイン画面の Dart ファイルを探索
  → lib/ui/auth/login_screen.dart を発見
```

#### Step 2-2: 既存 Key の収集

対象画面の Widget ツリーを解析し、既存の Key を収集する。

```dart
// 検索対象
Key('...')
ValueKey('...')
const Key('...')
{Screen}Keys.{name}  // Keys クラスのパターン
```

#### Step 2-3: 不足 Key の特定

仕様書の操作ステップで必要だが、まだ Key が付与されていない要素を特定する。

```
「以下の要素に Key が不足しています：

画面: LoginScreen (lib/ui/auth/login_screen.dart)
  ⚠️ メールアドレス入力フィールド → LoginKeys.emailField 推奨
  ⚠️ パスワード入力フィールド → LoginKeys.passwordField 推奨
  ✅ ログインボタン → 既存 Key あり

Key を追加しますか？（追加する場合、Keys クラスも生成します）」
```

**ここでユーザーの回答を待つ。**

#### Step 2-4: Key の追加（承認された場合）

1. `{screen}_keys.dart` ファイルを生成（または更新）
2. 対象 Widget に `key: {Screen}Keys.{name}` を追加
3. 変更差分をユーザーに表示

**ラッパーウィジェットの Key 伝播戦略:**

- `super.key` があるラッパーウィジェットには直接 Key を付与する
  ```dart
  CustomTextFormField(
    key: LoginKeys.driverIdPart1Field,  // super.key があるため直接付与可能
    controller: idPart1Controller,
  )
  ```
- `super.key` がないラッパーには `KeyedSubtree` でラップする
- Page Object 側では `find.descendant` パターンを使用し、ラッパーの Key から内部の `EditableText` を特定する

---

### Phase 3: テストコード生成

#### Step 3-1: Page Object の生成

画面ごとに Page Object クラスを生成する。
詳細は `references/page-object-pattern.md` を参照。

**Page Object クラスの命名規則:**

- 基本形: `{Screen}PageObject`（ウィジェットクラス名との衝突回避）
  - 例: `LoginPage` ウィジェット → `LoginPageObject` テストクラス
  - 例: `MyPagePage` ウィジェット → `MyPagePageObject` テストクラス
- 例外: ウィジェットクラス名と衝突しない場合は `{Screen}Page` でもよい（例: `AuthWallPage`）

**スクロール対応パターン:**

- 画面外要素へのアクセスには `scrollUntilVisible` を使用する
- マイページのログアウトボタンなど、画面下部の要素が対象
- Page Object 内でスクロール処理をカプセル化する

**`pumpAndSettle` タイムアウト調整:**

- API 通信を伴う操作（ログイン等）では `Duration(seconds: 10)` 以上を設定
- 認証フロー全体のタイムアウトは `Duration(seconds: 15)` を推奨

```
生成ファイル:
  integration_test/page_objects/login_page_object.dart
  integration_test/page_objects/home_page.dart
  integration_test/page_objects/my_page_page_object.dart
```

#### Step 3-2: シナリオテストの生成

仕様書の手順を 1:1 で Dart テストコードに変換する。
詳細は `references/test-template.md` を参照。

```
生成ファイル:
  integration_test/scenarios/st_auth_001_test.dart
```

#### Step 3-3: テストヘルパーの生成（初回のみ）

共通のセットアップ・ティアダウン処理を生成する。

```
生成ファイル:
  integration_test/helpers/test_helper.dart
  integration_test/helpers/app_launcher.dart
```

---

### Phase 4: マッピングレポート生成

仕様ステップとコードの対応表を生成する。
**これが人間のレビューポイント。**

詳細は `references/mapping-report.md` を参照。

```markdown
# マッピングレポート: ST-AUTH-001

| # | 仕様ステップ | 生成アクション | Key | 状態 |
|---|------------|-------------|-----|------|
| 1 | ログイン画面を表示 | pumpAndSettle() | LoginKeys.screen | ✅ Key一致 |
| 2 | メールアドレスを入力 | enterText(LoginKeys.emailField, '...') | LoginKeys.emailField | ✅ Key一致 |
| 3 | パスワードを入力 | enterText(LoginKeys.passwordField, '...') | LoginKeys.passwordField | ✅ Key一致 |
| 4 | ログインボタンをタップ | tap(LoginKeys.loginButton) | LoginKeys.loginButton | ✅ Key一致 |
| 5 | ホーム画面が表示される | expect(find.byKey(HomeKeys.screen)) | HomeKeys.screen | ⚠️ Key推定 |
| 6 | 予約ボタンをタップ | tap(HomeKeys.reserveButton) | HomeKeys.reserveButton | ❌ Key該当なし |

## 判定基準
- ✅ Key一致: Keys クラスに定義済みの Key と完全一致
- ⚠️ Key推定: 画面コードから推定した Key（要確認）
- ❌ Key該当なし: 対応する Key が見つからない（Key 追加が必要）
```

生成ファイル: `integration_test/reports/st_auth_001_mapping.md`

---

### Phase 5: 確認と出力

生成物一覧をユーザーに提示する。

```
「以下のファイルを生成しました：

Keys クラス:
  - lib/ui/auth/login_keys.dart (新規)
  - lib/ui/home/home_keys.dart (新規)

Page Objects:
  - integration_test/page_objects/login_page.dart
  - integration_test/page_objects/home_page.dart

テストコード:
  - integration_test/scenarios/st_auth_001_test.dart

マッピングレポート:
  - integration_test/reports/st_auth_001_mapping.md

マッピングレポートを確認してください。
❌ マークの項目は Key の追加が必要です。
⚠️ マークの項目は Key の妥当性を確認してください。」
```

---

## ガードレールの分離原則

### アサーション（期待結果）

- **仕様書から導出する**。コードの実装からは導出しない。
- 仕様書に「ホーム画面が表示される」とあれば、`expect(find.byKey(HomeKeys.screen), findsOneWidget)` を生成。
- コードに `Navigator.push(HomeScreen())` があっても、それはアサーションの根拠にしない。

### 操作手順

- **仕様書 + コードの Key 探索から導出する**。
- 仕様書の「メールアドレスを入力」→ コードから `LoginKeys.emailField` を探索 → `enterText` を生成。

---

## 再生成ポリシー

| 状況 | 対応 |
|------|------|
| テスト失敗（コードバグ） | コードを修正する。テストは正しい。 |
| 仕様変更 | テストを再生成する。仕様が正しい。 |
| UI リファクタリング（Key 変更なし） | テストはそのまま動く。 |
| UI リファクタリング（Key 変更あり） | Keys クラスを更新し、テストを再生成。 |
| 新画面追加 | 新しい仕様を書き、テストを生成。 |

---

## ファイル構成規約

```
project/
├── lib/
│   └── ui/
│       ├── auth/
│       │   ├── login_screen.dart
│       │   └── login_keys.dart          ← Keys クラス
│       └── home/
│           ├── home_screen.dart
│           └── home_keys.dart           ← Keys クラス
├── integration_test/
│   ├── page_objects/                    ← Page Object（画面ごと）
│   │   ├── login_page.dart
│   │   └── home_page.dart
│   ├── scenarios/                       ← シナリオテスト（仕様と1:1）
│   │   ├── st_auth_001_test.dart
│   │   └── st_rsv_001_test.dart
│   ├── reports/                         ← マッピングレポート
│   │   ├── st_auth_001_mapping.md
│   │   └── st_rsv_001_mapping.md
│   └── helpers/                         ← 共通ヘルパー
│       ├── test_helper.dart
│       └── app_launcher.dart
└── test_specs/                          ← テスト仕様書（参考配置）
    └── 総合試験項目書(Ph1).xlsx
```

---

## Key 規約

詳細は `references/key-convention.md` を参照。

### クイックリファレンス

| 項目 | 規約 |
|------|------|
| クラス名 | `{Screen}Keys`（例: `LoginKeys`） |
| Key 値 | `{screen}_{role}_{name}`（例: `login_field_email`） |
| 対象 | タップ・入力・検証する要素 + 画面自体 |
| ファイル | `{screen}_keys.dart`（画面と同ディレクトリ） |

### Role 一覧

| role | 用途 | 例 |
|------|------|---|
| `screen` | 画面自体 | `login_screen` |
| `field` | テキスト入力 | `login_field_email` |
| `button` | ボタン | `login_button_submit` |
| `text` | テキスト表示 | `home_text_welcome` |
| `list` | リスト | `home_list_reservations` |
| `item` | リストアイテム | `home_item_reservation` |
| `dialog` | ダイアログ | `login_dialog_error` |
| `icon` | アイコン | `home_icon_notification` |

---

## テスト仕様書の想定構造

### Excel カラム構成

| 列 | 内容 | AI での利用 |
|---|---|---|
| D: 試験項目ID | `ST-AUTH-001` 等 | テストファイル名・関数名 |
| E: 試験内容 | シナリオの説明 | テストの description |
| F: 前提条件 | ログイン状態、データ等 | setUp / モック設定 |
| G: 手順 | 番号付き操作ステップ | Page Object 経由の操作コード |
| H: 期待結果 | 番号付き期待値 | アサーション（仕様書由来） |

### テストカテゴリ

| カテゴリ | ID 範囲 | 内容 |
|---------|---------|------|
| 認証系 | ST-AUTH-001〜005 | ログイン、生体認証、オートログイン、セッション |
| 予約系 | ST-RSV-001〜004 | 検索、絞り込み、変更、キャンセル |
| 利用系 | ST-USE-001〜002 | 利用開始〜終了、延長、忘れ物 |
| マイページ | ST-MYP-001 | 設定、請求、クーポン |
| ヘルプ | ST-HLP-001 | FAQ検索、緊急連絡 |

---

## 注意事項

- 各フェーズでユーザーの確認を待つこと。先走って全生成しない。
- マッピングレポートの ❌ 項目がある場合、テストコード生成前に Key 追加を提案すること。
- アサーションは仕様書のみから導出する。コードの実装を根拠にしない。
- 既存の Widget テストや unit テストには影響を与えない。
- 生成コードは日本語コメント付きで出力する。

---

## 実行モード

### 単独実行（PoC 向け）

1テストケースを順次処理する場合に使用。Phase 0〜5 を1エージェントが逐次実行する。

### チーム実行（本番向け）

複数テストケースの一括生成や、品質重視の場合に使用。
PL・PG・QA の3ロールに分割し、Agent Team で並行作業する。
詳細は `references/agent-team-workflow.md` を参照。

```
PL（設計）: 仕様読み取り + 設計判断 + 最終レビュー
PG（実装）: コード解析 + Key追加 + テストコード生成
QA（検証）: マッピングレポート生成 + 整合性チェック
```

---

## 参照ドキュメント

- `references/key-convention.md` - Key 規約の詳細
- `references/page-object-pattern.md` - Page Object パターンのテンプレート
- `references/test-template.md` - テストコードテンプレート
- `references/mapping-report.md` - マッピングレポートのフォーマット
- `references/poc-example.md` - PoC 実行例（ST-AUTH-001 / ic_card プロジェクト）
- `references/real-project-patterns.md` - 実プロジェクトで発見されたパターン集
- `references/agent-team-workflow.md` - Agent Team ワークフロー（PL/PG/QA ロール分割）
