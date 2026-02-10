# GitHub PRレビューアクション

GitHub上でPRレビューを実行する際の、コメント投稿・評価方法のリファレンス。

---

## 1. このガイドのスコープ

- 対象：GitHub Actions上でのClaude Code実行、またはGitHubリポジトリでのPRレビュー
- 目的：レビュー結果を適切な形式でGitHub上に投稿する
- 前提：`gh` CLI が利用可能であること

---

## 2. PR情報の取得

レビュー開始前に、PRの全体像を把握する。

### 基本情報の取得

```bash
# PR基本情報の取得
gh pr view <PR番号> --json title,body,author,createdAt,headRefName,baseRefName,mergeable,reviewDecision

# 変更ファイル一覧の取得
gh pr diff <PR番号> --name-only

# コード差分の取得
gh pr diff <PR番号>

# 既存のレビューとコメントの確認
gh pr view <PR番号> --json reviews,comments
```

### 取得すべき情報

| 情報 | コマンド/フィールド | 用途 |
|------|---------------------|------|
| タイトル・説明 | `title`, `body` | 変更の意図を理解 |
| 作成者 | `author` | コンテキストの把握 |
| ブランチ情報 | `headRefName`, `baseRefName` | 差分の範囲を特定 |
| マージ可否 | `mergeable` | コンフリクトの有無 |
| 既存レビュー | `reviewDecision` | 他レビュアーの判断 |

---

## 3. インラインコメントの投稿

具体的なファイル・行番号が特定できる問題は、インラインコメントで指摘する。

### MCPツールを使用する場合

```
mcp__github_inline_comment__create_inline_comment
```

このツールが利用可能な場合は、ファイルパスと行番号を指定してインラインコメントを投稿できる。

### gh APIを使用する場合

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  -f body="コメント内容" \
  -f commit_id="$(gh pr view <PR番号> --json headRefOid -q .headRefOid)" \
  -f path="ファイルパス" \
  -F line=行番号 \
  -f side="RIGHT"
```

### インラインコメントのベストプラクティス

- **問題の重要度を明示**: `**Critical**:`, `**Major**:`, `**Minor**:` などのプレフィックスを使用
- **具体的な修正案を提示**: 問題だけでなく解決方法も記載
- **コード例を含める**: 可能であれば修正後のコードスニペットを提示

---

## 4. レビュー結果の投稿

レビュー完了後、結果をPRに投稿する。

### 投稿パターン

#### パターン1: Critical問題あり → REQUEST_CHANGES

マージ前に必ず修正が必要な問題がある場合。

```bash
gh pr review <PR番号> \
  --request-changes \
  --body "## ⚠️ 変更が必要です

以下のCritical問題が検出されました。修正してから再度レビューをリクエストしてください。

### Critical問題

- [問題の概要] - 詳細はインラインコメントを参照

**注**: 具体的な問題箇所と修正方法はファイルのインラインコメントで指摘しています。

修正後、このレビューを解決してください。"
```

#### パターン2: Major/Minor問題あり → 条件付きAPPROVE

重大ではないが改善すべき問題がある場合。

```bash
gh pr review <PR番号> \
  --approve \
  --body "## ✅ 条件付きでApprove

レビューを完了しました。重大な問題は見つかりませんでしたが、いくつかの改善点があります。

### 分析結果

#### 📦 Skill Quality: X/10
- 良い点: [概要]
- 改善点: [件数]件の指摘（インラインコメント参照）

### 改善項目

**注**: 具体的な改善箇所と推奨される対応は、各ファイルのインラインコメントで詳しく説明しています。

これらは次のイテレーションで対応することをお勧めします。"
```

#### パターン3: 問題なし → APPROVE

問題が検出されなかった場合。

```bash
gh pr review <PR番号> \
  --approve \
  --body "## ✅ Approved

レビューを完了しました。問題は見つかりませんでした。

### 分析結果

#### 📦 Skill Quality: 10/10
✅ フロントマターが正しく設定されています
✅ descriptionにトリガー条件が明記されています
✅ ディレクトリ構造が適切です
✅ 参照ファイルがすべて存在します

### Summary

マージして問題ありません。"
```

---

## 5. レビュー結果のフォーマット

### 標準フォーマット

```markdown
## Code Review: [判定結果]

### 変更概要
- **スコープ**: [変更の概要を1-2文で]
- **変更ファイル数**: [N]ファイル
- **主な言語/FW**: [検出された言語/FW]

### スコア: X/10

### 検出された問題

| # | 重要度 | ファイル | 問題 | 推奨される対応 |
|---|--------|---------|------|---------------|
| 1 | [Critical/Major/Minor/Suggestion] | [ファイルパス:行番号] | [問題の説明] | [対応方法] |

### 良い点
- [コードの良い点を具体的に記載]

### 判定
- **結果**: [Approve / Conditional Approve / Reject]
- **理由**: [判定理由の要約]

### 次のステップ
- [修正が必要な場合の具体的なアクション]
```

---

## 6. GitHub Actionsでの実行時の注意事項

### 権限設定

GitHub Actionsで実行する場合、以下の権限が必要：

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

### 環境変数

`gh` CLIが正しく動作するために必要：

```yaml
env:
  GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

または、GitHub Appトークンを使用：

```yaml
env:
  GH_TOKEN: ${{ steps.app-token.outputs.token }}
```

### 自動レビューの注意事項

- レビューはAIによる自動分析であり、最終的な判断は人間のレビュアーが行う必要がある
- スキルの実用性やドメイン知識が必要な判断は人間のレビューが必要
- 自動レビューの結果を過信せず、補助的なツールとして活用する

---

## 7. チェックリスト

### レビュー投稿前

- [ ] PR情報を取得し、変更の意図を理解した
- [ ] 変更ファイルを確認し、差分を分析した
- [ ] 問題を重要度別に分類した
- [ ] インラインコメントで具体的な箇所を指摘した

### レビュー投稿時

- [ ] 適切なレビューアクション（approve/request-changes/comment）を選択した
- [ ] レビュー本文に分析結果のサマリーを含めた
- [ ] インラインコメントへの参照を含めた
- [ ] 次のステップを明示した
