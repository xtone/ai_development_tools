---
name: extract-frontend-rules
description: コードベースを分析してフロントエンドのコーディング規約・パターンを抽出し、.claude/rules/frontend/配下にルールファイルとして出力します。フロントエンドプロジェクトの規約を文書化したい場合や、新メンバーのオンボーディング時に使用してください。
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
