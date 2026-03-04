# Agent Team ワークフロー

## 概要

E2E テスト生成を PL・PG・QA の3ロールに分割し、Agent Team で並行作業する。
各ロールが専門性を持ち、成果物を受け渡すことで品質と効率を両立する。

---

## ロール定義

### PL（Project Lead / テスト設計）

**責務**: 仕様の読み取りと設計判断

| Phase | 担当内容 |
|-------|---------|
| Phase 0 | プロジェクト構造の解析、Key 規約の決定 |
| Phase 1 | テスト仕様書の読み取り・解釈 |
| Phase 4 | マッピングレポートの最終レビュー |
| 全体 | 判断が必要な場面でのユーザーへの確認 |

**出力物**:
- プロジェクト構造情報（UI パス、状態管理、ルーティング）
- パース済みテスト仕様（構造化データ）
- Key 規約の決定事項

**必要なツール**: Read, Glob, Grep, Notion MCP（仕様書がNotionの場合）

### PG（Programmer / コード生成）

**責務**: 画面コード解析とテストコード生成

| Phase | 担当内容 |
|-------|---------|
| Phase 2 | 画面コード解析、既存 Key 収集、不足 Key 特定 |
| Phase 3 | Keys クラス生成、Page Object 生成、シナリオテスト生成、ヘルパー生成 |

**入力**: PL からのテスト仕様 + プロジェクト構造情報

**出力物**:
- Keys クラス（`{screen}_keys.dart`）
- Page Objects（`integration_test/page_objects/`）
- シナリオテスト（`integration_test/scenarios/`）
- ヘルパー（`integration_test/helpers/`）
- Key マッピング情報（どの Key が一致/推定/不足か）

**必要なツール**: Read, Glob, Grep, Edit, Write

### QA（Quality Assurance / 検証）

**責務**: 生成結果の検証とレポート作成

| Phase | 担当内容 |
|-------|---------|
| Phase 4 | マッピングレポート生成 |
| Phase 5 | 生成物の整合性チェック、テスト実行可能性の検証 |

**入力**: PG からの生成コード + Key マッピング情報 + PL からの仕様データ

**出力物**:
- マッピングレポート（`integration_test/reports/`）
- 整合性チェック結果
- 未解決項目のリスト

**必要なツール**: Read, Glob, Grep, Write, Bash（テスト実行）

---

## タスク分割と依存関係

```
[PL] プロジェクト解析 (Phase 0)
  │
  ├──→ [PL] テスト仕様読み取り (Phase 1)
  │       │
  │       ▼
  │     テスト仕様データ ──────────┐
  │                                │
  ▼                                ▼
プロジェクト構造情報 ──→ [PG] 画面コード解析 (Phase 2)
                           │
                           ▼
                    [PG] テストコード生成 (Phase 3)
                           │
                           ├── Keys クラス
                           ├── Page Objects
                           ├── シナリオテスト
                           └── Key マッピング情報
                                   │
                                   ▼
                    [QA] マッピングレポート生成 (Phase 4)
                           │
                           ▼
                    [QA] 整合性チェック (Phase 5)
                           │
                           ▼
                    [PL] 最終レビュー・ユーザー報告
```

### 並行可能なタスク

PL の Phase 0 完了後、以下を並行実行できる：

```
                    ┌── [PL] Phase 1: 仕様読み取り
Phase 0 完了後 ──┤
                    └── [PG] Phase 2: 画面コード解析（Key 収集）
```

PG が Key 収集を先行して進められるため、PL の仕様読み取りと並行できる。
Phase 3 は PL の仕様データと PG の Key 情報の両方が揃ったら開始。

---

## Team 構成例

### TeamCreate の設定

```
チーム名: e2e-test-gen
説明: E2E テスト自動生成チーム
```

### タスク定義

```
タスク1: [PL] プロジェクト構造を解析する
  - pubspec.yaml の依存解析
  - UI ディレクトリ構造の特定
  - 既存 Key の有無確認
  - Key 規約の決定
  → blockedBy: なし

タスク2: [PL] テスト仕様書を読み取る
  - Excel/Notion からテスト仕様を抽出
  - 手順・期待結果を構造化
  - テストデータを特定
  → blockedBy: タスク1

タスク3: [PG] 画面コードを解析し Key を収集する
  - 対象画面の Dart ファイルを特定
  - 既存 Key を一覧化
  - 不足 Key を特定
  → blockedBy: タスク1（プロジェクト構造情報が必要）

タスク4: [PG] Keys クラスと Page Object を生成する
  - Keys クラスの生成
  - 画面への Key 付与
  - Page Object の生成
  - シナリオテストの生成
  → blockedBy: タスク2, タスク3

タスク5: [QA] マッピングレポートを生成する
  - 仕様ステップとコードの対応表を作成
  - カバレッジを算出
  - 未解決項目をリスト化
  → blockedBy: タスク2, タスク4

タスク6: [QA] 生成物の整合性をチェックする
  - import パスの正しさ
  - Key の一貫性
  - テストの実行可能性
  → blockedBy: タスク4, タスク5

タスク7: [PL] 最終レビューとユーザー報告
  - マッピングレポートの確認
  - 生成物一覧の報告
  - 未解決項目の提示
  → blockedBy: タスク5, タスク6
```

---

## Agent 間のメッセージ例

### PL → PG: 仕様データの受け渡し

```
テスト仕様を読み取りました。

ST-AUTH-001: 正常ログイン/ログアウト
- 手順: 8ステップ
- 対象画面: LoginScreen, HomeScreen, MyPageScreen
- テストデータ: test@example.com / Test1234!

対象画面のパス:
- lib/ui/auth/login_screen.dart
- lib/ui/home/home_screen.dart
- lib/ui/my_page/my_page_screen.dart

これらの画面に対して Keys クラス + Page Object + テストを生成してください。
```

### PG → QA: 生成結果の受け渡し

```
テストコードを生成しました。

生成ファイル:
- lib/ui/auth/login_keys.dart (Keys: screen, emailField, passwordField, loginButton)
- lib/ui/home/home_keys.dart (Keys: screen, myPageNav)
- lib/ui/my_page/my_page_keys.dart (Keys: screen, logoutButton)
- integration_test/page_objects/login_page.dart
- integration_test/page_objects/home_page.dart
- integration_test/page_objects/my_page_page.dart
- integration_test/scenarios/st_auth_001_test.dart

Key マッピング:
- ✅ 一致: LoginKeys.screen, LoginKeys.emailField, LoginKeys.passwordField, LoginKeys.loginButton
- ⚠️ 推定: HomeKeys.screen, HomeKeys.myPageNav, MyPageKeys.screen, MyPageKeys.logoutButton
- ❌ 不足: なし

マッピングレポートを生成してください。
```

### QA → PL: レポートの受け渡し

```
マッピングレポートを生成しました。

サマリー:
- 総ステップ数: 10
- ✅ Key一致: 6 (60%)
- ⚠️ Key推定: 4 (40%)
- ❌ Key該当なし: 0 (0%)
- カバレッジ: 100%

整合性チェック:
- ✅ import パス正常
- ✅ Key の一貫性確認
- ⚠️ テスト実行は Key 追加後に可能

レポートファイル: integration_test/reports/st_auth_001_mapping.md

ユーザーにレビューを依頼してください。
```

---

## 単独実行 vs チーム実行

| 観点 | 単独実行 | チーム実行 |
|------|---------|-----------|
| 速度 | 逐次処理 | Phase 1 + Phase 2 を並行可能 |
| コンテキスト | 1エージェントに全情報 | ロールごとに必要な情報のみ |
| 品質 | 1視点でチェック | 3視点（設計・実装・検証） |
| 適用場面 | 1〜2テストケース | 複数テストケースの一括生成 |
| コスト | 低 | Agent 数分の API コール |

### 推奨

- **PoC（1テストケース）**: 単独実行で十分
- **本番（複数テストケース）**: チーム実行で並行処理

### 複数テストケースの並行生成

チーム実行の真価は、複数テストケースを一括生成する場合に発揮される：

```
[PL] 全仕様を一括読み取り
  │
  ├── ST-AUTH-001 の仕様
  ├── ST-AUTH-002 の仕様
  └── ST-RSV-001 の仕様
      │
      ▼
[PG-1] ST-AUTH-001 のコード生成  ←── 並行
[PG-2] ST-AUTH-002 のコード生成  ←── 並行
[PG-3] ST-RSV-001 のコード生成  ←── 並行
      │
      ▼
[QA] 全テストのマッピングレポート一括生成
```

この場合、PG を複数エージェントに分割し、テストケースごとに並行生成できる。

---

## worktree の活用

PG がコードを変更する（Key 追加等）ため、worktree での隔離を推奨：

```
PG エージェント → isolation: "worktree" で起動
  - メインブランチに影響を与えずに Key 追加 + テストコード生成
  - 完了後、変更をレビューしてマージ
```

これにより、Key 追加で既存コードが壊れるリスクを隔離できる。
