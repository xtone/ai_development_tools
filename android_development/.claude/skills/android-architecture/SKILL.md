---
name: android-architecture
description: "Androidプロジェクトのアーキテクチャ設計を支援。プロジェクト特性に応じてMVI/MVVM/シンプルComposeから最適なパターンを提案し、パッケージ構造の設計と既存プロジェクトの分析を行う。"
---

# Android Architecture Skill

Androidプロジェクトのアーキテクチャ設計を支援するスキルです。

## 目的

1. **新規プロジェクト**: 適切なアーキテクチャパターンとパッケージ構造を提案
2. **既存プロジェクト**: 現状分析とアーキテクチャドキュメント生成
3. **チーム教育**: アーキテクチャの理解を促進するドキュメント作成

## コマンド

### `analyze` - 既存プロジェクトの分析

```
User: このプロジェクトのアーキテクチャを分析して
User: /android-architecture analyze
```

**実行内容**:
1. プロジェクト構造をスキャン
2. 採用パターンを特定（MVI/MVVM/MVP等）
3. 層構成を分析（Clean Architecture準拠度）
4. `docs/ANDROID_ARCHITECTURE.md` を生成

### `setup` - 新規プロジェクトへの導入

```
User: このプロジェクトにアーキテクチャを導入して
User: /android-architecture setup
User: /android-architecture setup mvi    # パターン指定も可能
User: /android-architecture setup mvvm
User: /android-architecture setup simple
```

**実行内容**:
1. 要件ヒアリング（画面数、状態管理の複雑さ、チーム経験）
2. 最適なパターンを提案（MVI/MVVM/シンプルCompose）
3. 選択されたパターンの基盤クラスを生成
4. サンプル機能（Feature）を作成
5. セットアップガイドを生成

**パターン別の生成物**:
| パターン | 生成物 |
|---------|-------|
| MVI | StateManager, Reducer, Presenter, サンプル機能 |
| MVVM | BaseViewModel, UiState, サンプル機能 |
| Simple | ガイドラインのみ（基盤クラスなし） |

### `document` - ドキュメント生成のみ

```
User: アーキテクチャドキュメントを作成して
User: /android-architecture document
```

**実行内容**:
1. 現状のコードを読み取り
2. `docs/ANDROID_ARCHITECTURE.md` を生成
3. チーム向けの説明資料として整形

## 推奨アーキテクチャ

プロジェクトの特性に応じて3つのパターンから選択します。

### パターン1: MVI（複雑な状態管理向け）

```
Screen (Compose)
    │ Intent
    ▼
 ViewModel
    │ Action
    ▼
StateManager ─────┬──────────────┐
                  │              │
              Reducer        Presenter
          (純粋な状態変換)   (副作用実行)
```

**適用例**: dメニューニュース（本番アプリ、複雑な状態遷移）
詳細は `knowledge/mvi-pattern.md` を参照。

### パターン2: MVVM（シンプルな画面向け）

```
Screen (Compose)
    │ Event
    ▼
 ViewModel ────── UiState
    │
    ▼
 UseCase / Repository
```

**適用例**: 設定画面、CRUD中心のアプリ
詳細は `knowledge/mvvm-pattern.md` を参照。

### パターン3: シンプルCompose（モック/展示会向け）

```
MainActivity
    │
    ▼
AppNavigation (remember + mutableStateOf)
    │
    ▼
Screen Composables
```

**適用例**: AI HOME（展示会デモ、状態管理が単純）
詳細は `knowledge/simple-compose.md` を参照。

### パッケージ構造

```
app/                    # アプリケーションモジュール（DI統合）
├── ui/                 # UI層（Compose + ViewModel）
├── domain/             # ドメイン層（UseCase, Repository Interface）
└── data/               # データ層（Repository実装, Room, Retrofit）
```

※ シンプルComposeの場合はシングルモジュールも可

## 判断基準

### アーキテクチャパターンの選択

| 条件 | 推奨パターン |
|------|-------------|
| 複雑な状態管理が必要 | MVI |
| シンプルなCRUD画面 | MVVM（軽量） |
| 展示会デモ/モックアプリ | シンプルCompose |
| レガシーコードとの共存 | MVP → 段階的にMVIへ |

### パッケージ構造の選択

| 条件 | 推奨構造 |
|------|---------|
| 機能が多い（10+画面） | by-feature |
| 機能が少ない（〜5画面） | by-layer |
| マルチモジュール化予定 | by-feature + module分割 |

## System Instructions

### 1. `analyze` コマンドの実行手順

#### ステップ1: プロジェクト構造の確認

```bash
# モジュール構成を確認
ls -la */src/main/kotlin/

# パッケージ構造を確認
find . -name "*.kt" -path "*/src/main/*" | head -50
```

**確認ポイント**:
- モジュール分割（app, ui, domain, data等）
- パッケージ命名規則
- 共通コードの配置場所

#### ステップ2: アーキテクチャパターンの特定

以下のファイルパターンを検索:

```bash
# MVI パターン
find . -name "*Intent.kt" -o -name "*StateManager.kt" -o -name "*Reducer.kt"

# MVVM パターン
find . -name "*ViewModel.kt" | head -10

# Repository パターン
find . -name "*Repository.kt" | head -10
```

#### ステップ3: 基盤クラスの分析

MVIの場合、以下を確認:
- `MviIntent`, `MviAction`, `MviState`, `MviEvent` インターフェース
- `StateManager` 基底クラス
- `StateReducer` 基底クラス

#### ステップ4: ドキュメント生成

`knowledge/dmenunews-example.md` を参考に、以下の構成でドキュメントを生成:

1. プロジェクト構造と設計思想
2. 採用アーキテクチャとその理由
3. 状態管理の方針
4. DI構成
5. データ層の設計
6. パッケージ構造の詳細
7. テスト戦略
8. 開発フロー
9. FAQ

### 2. `setup` コマンドの実行手順

#### ステップ1: 要件ヒアリング

ユーザーに以下を確認:
- プロジェクトの規模（画面数）
- 状態管理の複雑さ（複数画面で共有する状態があるか）
- 既存コードの有無
- チームの経験レベル
- 特別な要件（マルチモジュール等）
- 用途（本番アプリ/モック/展示会デモ）

#### ステップ2: パターン推奨

ヒアリング結果に基づいて最適なパターンを提案:

| 条件 | 推奨パターン |
|------|-------------|
| 10+画面、複雑な状態遷移、チームにMVI経験者 | **MVI** |
| 5-10画面、シンプルなCRUD、チーム初心者多め | **MVVM** |
| モック/展示会、状態共有なし、短期開発 | **シンプルCompose** |

**推奨フォーマット**:
```
プロジェクト特性の分析結果:
- 画面数: XX画面
- 状態管理: [複雑/シンプル]
- 用途: [本番/モック]

推奨パターン: [MVI/MVVM/シンプルCompose]
理由: ...

このパターンで進めてよいですか？
```

#### ステップ3: 基盤クラス生成（パターン別）

**MVI選択時**: `ui/common/mvi/` に以下を作成
- `MviIntent.kt`
- `MviAction.kt`
- `MviState.kt`
- `MviEvent.kt`
- `StateManager.kt`
- `StateReducer.kt`
- `MviPresenter.kt`

**MVVM選択時**: `ui/common/` に以下を作成
- `BaseViewModel.kt`
- `UiState.kt`
- `UiEvent.kt`

**シンプルCompose選択時**: 基盤クラスは作成しない
- `docs/ARCHITECTURE_GUIDELINES.md` のみ生成

#### ステップ4: サンプル機能の作成（パターン別）

**MVI選択時**: `ui/feature/sample/` に作成
- `SampleScreen.kt`
- `SampleViewModel.kt`
- `SampleUiState.kt`
- `SampleIntent.kt`
- `mvi/SampleStateManager.kt`
- `mvi/SampleReducer.kt`

**MVVM選択時**: `ui/feature/sample/` に作成
- `SampleScreen.kt`
- `SampleViewModel.kt`
- `SampleUiState.kt`

**シンプルCompose選択時**: サンプルは作成しない
- 既存の `aihome-example.md` を参照として案内

#### ステップ5: セットアップガイド生成

`docs/ARCHITECTURE_SETUP.md` を生成:
- 選択したパターンの説明
- ディレクトリ構造
- 新機能追加の手順
- テスト方針

### 3. エラーハンドリング

**エラー1: パターンが特定できない**
- 複数パターンが混在している可能性を報告
- 各パターンの使用箇所を列挙
- 統一の提案を行う

**エラー2: 既存コードとの競合**
- 既存の基盤クラスを尊重
- 拡張・改善の提案にとどめる
- 破壊的変更は避ける

**エラー3: パターン選択に迷う**
- ヒアリング項目を追加で確認
- 両方のメリット・デメリットを提示
- 最終判断はユーザーに委ねる

## Knowledge Files

- `knowledge/dmenunews-example.md` - dメニューニュースでの実装例（MVI）
- `knowledge/aihome-example.md` - AI HOMEでの実装例（シンプルCompose）
- `knowledge/mvi-pattern.md` - MVIパターンの詳細ガイド
- `knowledge/mvvm-pattern.md` - MVVMパターンの詳細ガイド
- `knowledge/simple-compose.md` - シンプルComposeの詳細ガイド
- `knowledge/migration-guide.md` - 既存プロジェクトへの移行ガイド
- `knowledge/skill-integration.md` - Androidスキル連携ガイド

## 関連スキル

- `android-ui-guidelines` - Compose UIの実装ガイドライン
- `android-api-client-guidelines` - APIクライアントの実装ガイドライン
- `android-test-runner` - テスト実行と失敗分析
- `android-test-generator` - テストコード自動生成

## 成功基準

- プロジェクト構造が正確に分析されている
- アーキテクチャパターンが正しく特定されている
- **プロジェクト特性に適したパターンが提案されている**
- 生成ドキュメントが新規メンバーの理解を助ける
- 提案が既存コードを破壊しない

## バージョン

### v1.1 - パターン選択対応 (2026-01-13)
- `setup` コマンドにパターン選択機能を追加
- MVVM、シンプルComposeのサポート追加
- 要件ヒアリングステップの強化
- `knowledge/mvvm-pattern.md` 追加
- `knowledge/simple-compose.md` 追加

### v1.0 - 初版 (2026-01-08)
- `analyze` コマンド実装
- `setup` コマンド実装
- `document` コマンド実装
- dmenunews実例をknowledgeとして追加

---

**Maintainer**: 石原正也
**公開範囲**: Public
**セットアップ**: 即利用可
