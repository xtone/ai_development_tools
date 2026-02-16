---
name: flutter-team
description: "Flutter開発チームのオーケストレーター。ユーザーの依頼内容を解析し、最適なスキル/チームに自動ルーティングします。Figma URLの種類（Light/Dark Mode）やUI状態分析の依頼を判定し、適切なスキルを呼び出します。"
---

# Flutter Team Orchestrator

ユーザーの依頼内容（`$ARGUMENTS`）を解析し、最適なスキル/チームにルーティングするオーケストレータースキルです。

## ルーティング判定

`$ARGUMENTS` の内容を以下の順序で判定してください。

### 判定ルール

#### 1. Figma URL の判定

`$ARGUMENTS` に Figma URL（`https://www.figma.com/design/...`）が含まれるか確認します。

**Light Mode URL の判定条件:**
- URL のパス・パラメータ、または URL 前後のテキストに以下のキーワードが含まれる:
  - `light`, `Light`, `ライト`, `ライトモード`
- または、URL 前後のコンテキストで Light Mode と明示されている

**Dark Mode URL の判定条件:**
- URL のパス・パラメータ、または URL 前後のテキストに以下のキーワードが含まれる:
  - `dark`, `Dark`, `ダーク`, `ダークモード`
- または、URL 前後のコンテキストで Dark Mode と明示されている

**ルーティング:**

| 検出パターン | アクション |
|---|---|
| Light Mode URL のみ | → **Route A** |
| Dark Mode URL のみ | → **Route B** |
| Light + Dark 両方の URL | → **Route C** |
| Figma URL はあるが Light/Dark の判別ができない | → ユーザーに Light/Dark どちらか確認する |

#### 2. UI状態分析の判定

`$ARGUMENTS` に以下のキーワードが含まれる場合 → **Route D**:
- `Fire UI Stack`, `fire-ui-stack`, `UI状態`, `5つの状態`
- `Ideal State`, `Blank State`, `Loading State`, `Error State`, `Partial State`
- `状態分析`, `UI分析`

#### 3. 上記以外

上記のいずれにも該当しない場合 → **Route E**（一般的なFlutter実装チーム）

---

## Route A: Light Mode Agent

Figma の Light Mode デザイン URL が検出された場合。

**実行方法:**

`Skill` ツールを使用して `light-mode-agent` スキルを呼び出してください:

```
Skill:
  skill: "light-mode-agent"
  args: "$ARGUMENTS"
```

## Route B: Dark Mode Agent

Figma の Dark Mode デザイン URL が検出された場合。

**実行方法:**

`Skill` ツールを使用して `dark-mode-agent` スキルを呼び出してください:

```
Skill:
  skill: "dark-mode-agent"
  args: "$ARGUMENTS"
```

## Route C: Light + Dark 並列実行

Light Mode と Dark Mode の両方の URL が検出された場合。

**実行方法:**

`Skill` ツールを使用して、両方のスキルを **並列** で呼び出してください:

```
# 以下を並列で実行
Skill:
  skill: "light-mode-agent"
  args: "{Light Mode URL と関連する指示}"

Skill:
  skill: "dark-mode-agent"
  args: "{Dark Mode URL と関連する指示}"
```

両方の完了後、統合レポートを作成してください。

## Route D: Fire UI Stack 分析

UI状態分析が依頼された場合。

**実行方法:**

`Skill` ツールを使用して `fire-ui-stack` スキルを呼び出してください:

```
Skill:
  skill: "fire-ui-stack"
  args: "$ARGUMENTS"
```

## Route E: 一般 Flutter 実装チーム

上記のいずれにも該当しない一般的な Flutter 実装の場合、3人チームを構成します。

### チーム構成

以下の3人のチームメイトを生成してください：

#### 1. デザイン担当 (Designer)
- **役割**: Figmaデザインの解析とデザイン仕様の整理
- **タスク**:
  - デザインからレイアウト構造を把握
  - カラー、フォント、スペーシングの仕様を抽出
  - コンポーネントの分類（Atomic Design）
- **成果物**: デザイン仕様書

#### 2. Flutter コード担当 (Flutter Developer)
- **役割**: Flutterウィジェットの実装
- **タスク**:
  - デザイン仕様に基づいてWidgetを実装
  - 適切な状態管理パターンを選択
  - 既存のコンポーネントを再利用
- **成果物**: Flutterコード

#### 3. UI/UX担当 (UI/UX Specialist)
- **役割**: ユーザビリティとアクセシビリティのレビュー
- **タスク**:
  - インタラクションの設計レビュー
  - アクセシビリティ対応の確認
  - エッジケースの洗い出し
- **成果物**: UI/UXレビューレポート

### ワークフロー

1. **Designer** がデザイン仕様を整理
2. **Flutter Developer** が仕様に基づいて実装
3. **UI/UX Specialist** が実装をレビュー
4. 必要に応じて議論・修正

### 対象

$ARGUMENTS

---

チームメイト間で積極的にコミュニケーションを取り、高品質なFlutter UIを実装してください。
