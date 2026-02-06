# Android Test Generator v1.0

Android実装コードから適切なテストケースを自動生成するClaude Codeスキル。

## 概要

```
実装コード → Test Generator → テストコード
              ↓
         クラス種別を自動判定
         プロジェクトのパターンに準拠
         Given-When-Then構造
         MockK + runTest
```

## 対応テスト対象

| 対象 | サポート状況 | テンプレート | 層 |
|------|-------------|-------------|-----|
| Reducer | ✅ v1.0 | `templates/reducer-test.md` | UI |
| StateManager | ✅ v1.0 | `templates/statemanager-test.md` | UI |
| Presenter | ✅ v1.0 | `templates/presenter-test.md` | UI |
| ViewModel (MVI) | ✅ v1.0 | `templates/viewmodel-test.md` | UI |
| ViewModel (AAC) | ✅ v1.0 | `templates/viewmodel-test.md` | UI |
| Handler | ✅ v1.0 | `templates/handler-test.md` | UI |
| UseCase | ✅ v0.1 | `templates/usecase-test.md` | Domain |
| Repository | ✅ v0.1 | `templates/repository-test.md` | Data |
| ApiService | ✅ v1.0 | `templates/api-service-test.md` | Data |
| Mapper | ✅ v1.0 | `templates/mapper-test.md` | Data |

## 使い方

### 1. 手動モード

```
「GetFavoriteArticlesUseCaseのテストを作って」
「このクラスのテストを生成して」
「app/src/main/.../MyRepository.kt のテストを作成」
```

### 2. クラス種別自動判定

実装コードを解析し、以下のパターンでテンプレートを自動選択:

| 優先度 | 判定条件 | テンプレート |
|--------|---------|-------------|
| 1 | `fun reduce(state:` 検出 | Reducer |
| 2 | `processIntent` + `handleAction` 検出 | StateManager |
| 3 | クラス名に `Presenter` + UseCase依存 | Presenter |
| 4 | クラス名に `ViewModel` + StateManager依存 | ViewModel (MVI) |
| 5 | クラス名に `ViewModel` + UseCase依存 | ViewModel (AAC) |
| 6 | クラス名に `Handler` | Handler |
| 7 | クラス名に `UseCase` | UseCase |
| 8 | クラス名に `Repository` + ApiService依存 | Repository |
| 9 | クラス名に `Mapper` or `toXxx()` 拡張関数 | Mapper |

### 3. PR作成時の自動チェック（将来対応）

PR作成時にテストがない変更を検出し、テスト生成を提案。

## 生成されるテストの特徴

### 構造
- **Given-When-Then** 形式
- バッククォートによるテストメソッド命名
- 日本語/英語の混在対応
- `@file:Suppress` 自動付与

### 技術スタック
- **Mock**: MockK (`coEvery`, `coVerify`, `every`, `verify`)
- **Coroutine**: `runTest` / `testScope.runTest` + `StandardTestDispatcher`
- **アサーション**: JUnit Assert / Google Truth（層に応じて使い分け）
- **HTTP**: MockWebServer（ApiServiceテスト用）

### モジュール別設定

| 層 | アサーション | コルーチン | Mockポリシー | Flow検証 |
|----|------------|-----------|------------|---------|
| Domain | JUnit Assert | `runTest` | strict | `first()` |
| Data | Truth | `runTest` | relaxed | `first()` |
| UI | Truth | `testScope.runTest` | mixed | manual collect |

## プロジェクト設定

`knowledge/project-config.md` でプロジェクト固有の設定が可能:

```yaml
# モジュール別設定
domain:
  assertion: "junit"
  coroutine: "runTest"
  mock_policy: "strict"

data:
  assertion: "truth"
  coroutine: "runTest"
  mock_policy: "relaxed"

ui:
  assertion: "truth"
  coroutine: "testScope_runTest"
  mock_policy: "mixed"

# 共通設定
naming:
  language: "mixed"
  use_backtick: true
```

## ディレクトリ構成

```
android-test-generator/
├── SKILL.md                          # スキル定義（メイン）
├── README.md                         # このファイル
├── knowledge/
│   └── project-config.md             # プロジェクト設定テンプレート
└── templates/
    ├── reducer-test.md               # Reducerテストテンプレート
    ├── statemanager-test.md          # StateManagerテストテンプレート
    ├── presenter-test.md             # Presenterテストテンプレート
    ├── viewmodel-test.md             # ViewModelテストテンプレート（MVI/AAC）
    ├── handler-test.md               # Handlerテストテンプレート
    ├── usecase-test.md               # UseCaseテストテンプレート
    ├── repository-test.md            # Repositoryテストテンプレート
    ├── api-service-test.md           # ApiServiceテストテンプレート
    └── mapper-test.md                # Mapperテストテンプレート
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
| v1.0 | 2026-02-02 | MVI 4層テンプレート追加、Data層テンプレート追加、Handler追加、モジュール別設定対応、クラス種別自動判定 |
| v0.1 | 2025-12-02 | 初版作成（dmenu-news分析結果に基づく） |

## ライセンス

MIT License
