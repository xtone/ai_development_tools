# Android スキル連携ガイド

Androidプロジェクト開発における複数スキルの連携方法と推奨フローを解説します。

---

## 1. スキル一覧と役割

### 1.1 利用可能なスキル

| スキル | 役割 | 対象フェーズ |
|--------|------|------------|
| **android-architecture** | アーキテクチャ設計・分析 | 設計 |
| android-ui-guidelines | Compose UIの実装ガイド | 実装 |
| android-api-client-guidelines | APIクライアント実装ガイド | 実装 |
| android-test-generator | テストコード自動生成 | テスト |
| android-test-runner | テスト実行と失敗分析 | テスト |
| figma-to-compose | Figmaデザインからの変換 | 実装 |

### 1.2 スキル間の依存関係

```
                    ┌─────────────────────────┐
                    │  android-architecture   │
                    │  (本スキル)             │
                    └───────────┬─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ android-ui-       │ │ android-api-    │ │ figma-to-       │
│ guidelines        │ │ client-         │ │ compose         │
│                   │ │ guidelines      │ │                 │
└─────────┬─────────┘ └────────┬────────┘ └─────────────────┘
          │                    │
          └────────┬───────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ android-test-       │
        │ generator           │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ android-test-       │
        │ runner              │
        └─────────────────────┘
```

---

## 2. 推奨開発フロー

### 2.1 新規プロジェクト開発

```
Phase 1: 設計
├── 1. android-architecture analyze
│     → 既存コードがあれば分析
│
├── 2. android-architecture setup [pattern]
│     → MVI/MVVM/シンプルCompose を選択
│     → 基盤クラス生成
│
└── 3. android-architecture document
      → アーキテクチャドキュメント生成

Phase 2: 実装
├── 4. figma-to-compose (デザインがある場合)
│     → FigmaからCompose変換
│
├── 5. android-ui-guidelines
│     → UI実装のガイドライン適用
│
└── 6. android-api-client-guidelines
      → API連携の実装

Phase 3: テスト
├── 7. android-test-generator
│     → 実装コードからテスト生成
│
└── 8. android-test-runner
      → テスト実行、失敗分析
```

### 2.2 既存プロジェクト改善

```
1. android-architecture analyze
   → 現状のアーキテクチャを把握

2. android-architecture document
   → チーム共有用ドキュメント生成

3. (必要に応じて) migration-guide.md 参照
   → MVVM → MVI 移行など
```

---

## 3. パターン別の推奨スキル組み合わせ

### 3.1 MVI選択時

```
android-architecture (MVI)
    │
    ├── android-ui-guidelines ★必須
    │     → MVI + Compose の実装パターン
    │
    ├── android-api-client-guidelines ★必須
    │     → Repository層の実装
    │
    ├── android-test-generator ★推奨
    │     → Reducer, UseCaseの単体テスト生成
    │
    └── android-test-runner ★推奨
          → テスト実行、カバレッジ確認
```

### 3.2 MVVM選択時

```
android-architecture (MVVM)
    │
    ├── android-ui-guidelines ★必須
    │     → ViewModel + Compose の実装パターン
    │
    ├── android-api-client-guidelines ○任意
    │     → API連携がある場合
    │
    └── android-test-generator ○任意
          → ViewModelテスト生成
```

### 3.3 シンプルCompose選択時

```
android-architecture (Simple)
    │
    ├── android-ui-guidelines ○任意
    │     → 基本的なComposeパターン参考
    │
    ├── figma-to-compose ★推奨
    │     → デザインからの変換で高速開発
    │
    └── テスト系スキル △不要
          → モック/展示会では不要
```

---

## 4. スキル間のデータ連携

### 4.1 android-architecture → android-test-generator

**生成されるアーキテクチャ情報**:
```
docs/ANDROID_ARCHITECTURE.md
├── 採用パターン: MVI/MVVM/Simple
├── パッケージ構造
├── テスト対象クラス
│   ├── Reducer (MVI)
│   ├── UseCase
│   └── Repository
└── テスト方針
```

**android-test-generator での活用**:
- Reducerの単体テスト生成（MVI）
- ViewModelテスト生成（MVVM）
- UseCase統合テスト生成

### 4.2 android-ui-guidelines → android-test-generator

**UIガイドラインで定義**:
- Composableの命名規則
- State Hoistingパターン
- Preview関数の配置

**テスト生成での活用**:
- Preview関数からスナップショットテスト生成
- UIテストパターンの適用

---

## 5. 典型的なユースケース

### 5.1 新規本番アプリ開発

```bash
# Day 1: 設計
User: このプロジェクトにアーキテクチャを導入して
→ android-architecture setup (MVI推奨)

# Day 2-N: 実装
User: ユーザー一覧画面を実装して
→ android-ui-guidelines 参照

User: APIクライアントを実装して
→ android-api-client-guidelines 参照

# 実装完了後: テスト
User: このUseCaseのテストを生成して
→ android-test-generator

User: テストを実行して
→ android-test-runner
```

### 5.2 展示会デモ開発

```bash
# Day 1: 設計
User: 展示会向けのモックアプリを作りたい
→ android-architecture setup simple

# Day 2-N: 高速実装
User: このFigmaデザインを実装して
→ figma-to-compose
→ android-ui-guidelines (参考程度)

# テストは不要
```

### 5.3 既存プロジェクトの改善

```bash
# 現状把握
User: このプロジェクトのアーキテクチャを分析して
→ android-architecture analyze

# ドキュメント化
User: アーキテクチャドキュメントを作成して
→ android-architecture document

# テスト追加
User: テストがないので追加したい
→ android-test-generator
→ android-test-runner
```

---

## 6. トラブルシューティング

### 6.1 スキル間の競合

**問題**: 異なるスキルが矛盾する推奨をする

**対処**:
- android-architecture の判断を優先
- パターン選択に応じて他スキルの推奨を適用

### 6.2 スキルが見つからない

**問題**: プロジェクトでスキルが認識されない

**対処**:
```bash
# スキルの配置を確認
ls .claude/skills/

# 必要なスキルをコピー
cp -r path/to/ai_development_tools/.claude/skills/android-* .claude/skills/
```

### 6.3 パターン変更したい

**問題**: MVVM → MVI に変更したい

**対処**:
1. `migration-guide.md` を参照
2. 段階的に移行（Phase 1-3）
3. `android-architecture analyze` で進捗確認

---

## 7. 関連ドキュメント

- [MVIパターン詳細](./mvi-pattern.md)
- [MVVMパターン詳細](./mvvm-pattern.md)
- [シンプルCompose詳細](./simple-compose.md)
- [移行ガイド](./migration-guide.md)
- [dmenunews実装例](./dmenunews-example.md)
- [AI HOME実装例](./aihome-example.md)

---

**作成日**: 2026-01-13
**作成者**: Claude Code（android-architectureスキル）
