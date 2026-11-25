---
name: extract-frontend-rules
description: コードベースを分析してフロントエンド規約を抽出し、.claude/rules/frontend/に出力します。フロントエンドプロジェクトの規約文書化や新メンバーオンボーディング時に使用してください。
---

# フロントエンド規約抽出

Task toolで `extract-frontend-rules` エージェントを起動して実行してください。

## 引数の処理

`$ARGUMENTS` の内容に応じてエージェントへのプロンプトを構成する:

- 引数なし → 全カテゴリを分析
- `--structure` → ディレクトリ構造のみ
- `--naming` → 命名規則のみ
- `--components` → コンポーネント設計のみ
- `--imports` → import/exportのみ
- `--api` → API呼び出しのみ
- `--testing` → テストパターンのみ
- `--forms` → フォーム・バリデーションのみ
- `--state` → 状態管理のみ
- 複数指定可（例: `--structure --naming`）

## 実行方法

```
Task tool:
  subagent_type: extract-frontend-rules
  description: "フロントエンド規約を抽出"
  prompt: "以下のカテゴリのフロントエンド規約を分析・抽出してください: [引数から判定したカテゴリ]"
```

エージェントの完了後、結果サマリーをユーザーに報告してください。

## 実行例

`/extract-frontend-rules --structure --naming` を実行した場合:

```
Task tool:
  subagent_type: extract-frontend-rules
  description: "フロントエンド規約を抽出"
  prompt: "以下のカテゴリのフロントエンド規約を分析・抽出してください: ディレクトリ構造, 命名規則"
```

出力先: `.claude/rules/frontend/directory-structure.md`, `.claude/rules/frontend/naming-conventions.md`

## 生成されるルールファイル例

`.claude/rules/frontend/naming-conventions.md` の出力例:

````markdown
# 命名規則

> 自動生成: 2026-02-10
> 検出フレームワーク: Next.js 15 + TypeScript + Tailwind CSS v4

## 概要

プロジェクト内で一貫して使用されているファイル・コンポーネント・関数の命名パターン。

## ルール

### ルール1: コンポーネントファイルはPascalCase

**適用条件**: React/Nextコンポーネントファイル

**ルール内容**:
- コンポーネントファイル名はPascalCaseを使用する
- ファイル拡張子は `.tsx` を使用する

**コード例**:
```typescript
// 正しい例
import { UserProfile } from './UserProfile/UserProfile.tsx'

// 間違った例
import { userProfile } from './userProfile/userProfile.tsx'
```

**検出根拠**:
- `src/app/_components/Header/Header.tsx`
- `src/shared/components/Button/Button.tsx`
- `src/app/dashboard/_components/Chart/Chart.tsx`
````
