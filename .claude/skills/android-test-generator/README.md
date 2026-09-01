# Android Test Generator

Android実装コードから適切なテストケースを自動生成するClaude Codeスキル。

## 概要

```
実装コード → Test Generator → テストコード
              ↓
         プロジェクトのパターンに準拠
         Given-When-Then構造
         MockK + runTest
```

## 対応テスト対象

| 対象 | サポート状況 | テンプレート |
|------|-------------|-------------|
| UseCase | ✅ 完全対応 | `templates/usecase-test.md` |
| Repository | ✅ 完全対応 | `templates/repository-test.md` |
| ViewModel/StateManager | ✅ 完全対応 | `templates/viewmodel-test.md` |

## 使い方

### 1. 手動モード

```
「GetFavoriteArticlesUseCaseのテストを作って」
「このクラスのテストを生成して」
「app/src/main/.../MyRepository.kt のテストを作成」
```

### 2. PR作成時の自動チェック（将来対応）

PR作成時にテストがない変更を検出し、テスト生成を提案。

## 生成されるテストの特徴

### 構造
- **Given-When-Then** 形式
- バッククォートによるテストメソッド命名
- 日本語/英語の混在対応

### 技術スタック
- **Mock**: MockK (`coEvery`, `coVerify`)
- **Coroutine**: `runTest` + `StandardTestDispatcher`
- **アサーション**: JUnit Assert / Google Truth

### 生成されるテストケース

**UseCase**:
1. 成功ケース（`Result.success`）
2. 失敗ケース（`Result.failure`）
3. 境界値ケース（空リスト等）

**Repository**:
1. API成功ケース
2. API失敗ケース（例外スロー）
3. キャッシュ動作（該当する場合）

**ViewModel/StateManager**:
1. 初期状態の検証
2. Intent/Action処理
3. State遷移

## プロジェクト設定

`knowledge/project-config.md` でプロジェクト固有の設定が可能:

```yaml
assertion:
  primary: "junit"           # junit | truth | both
  use_truth_for_ui: true     # UI層でTruthを使用

coroutine:
  dispatcher_rule: "standard" # standard | main_dispatcher_rule

flow:
  verification: "collect"     # collect | turbine

naming:
  language: "english"         # english | japanese | mixed
  use_backtick: true
```

## ディレクトリ構成

```
android-test-generator/
├── SKILL.md                      # スキル定義（メイン）
├── README.md                     # このファイル
├── knowledge/
│   └── project-config.md         # プロジェクト設定テンプレート
└── templates/
    ├── usecase-test.md           # UseCaseテストテンプレート
    ├── repository-test.md        # Repositoryテストテンプレート
    └── viewmodel-test.md         # ViewModelテストテンプレート
```

## インストール

### 汎用版として使用

```bash
# ai_development_tools リポジトリから
cp -r .claude/skills/android-test-generator ~/.claude/skills/
```

### プロジェクト固有版として使用

```bash
# プロジェクトの .claude/skills/ にコピー
cp -r android-test-generator your-project/.claude/skills/

# プロジェクト設定を編集
vi your-project/.claude/skills/android-test-generator/knowledge/project-config.md
```

## 関連スキル

- **android-test-runner**: 生成したテストの実行・失敗分析

```
開発フロー:
実装 → Test Generator → テスト生成 → Test Runner → テスト実行
```

## バージョン履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| v0.1 | 2025-12-02 | 初版作成（dmenu-news分析結果に基づく） |

## ライセンス

MIT License
