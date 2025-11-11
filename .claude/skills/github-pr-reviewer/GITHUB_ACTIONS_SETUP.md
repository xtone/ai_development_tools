# GitHub Actions セットアップガイド

GitHub ActionsでClaude Code を使用して自動PRレビューを実行するためのセットアップ手順です。

## 前提条件

- GitHubリポジトリへの管理者権限
- Anthropic APIキーの取得

## セットアップ手順

### 1. Anthropic APIキーの取得

1. [Anthropic Console](https://console.anthropic.com/)にアクセス
2. サインインまたはアカウント作成
3. API Keysセクションに移動
4. 新しいAPIキーを作成してコピー

### 2. GitHubリポジトリへのシークレット追加

1. GitHubリポジトリの **Settings** → **Secrets and variables** → **Actions** に移動
2. **New repository secret** をクリック
3. 以下のシークレットを追加：

   **Name**: `ANTHROPIC_API_KEY`
   **Secret**: [手順1で取得したAPIキー]

4. **Add secret** をクリック

### 3. ワークフローファイルの配置

このスキルには `.github/workflows/pr-review.yml` が含まれています。

リポジトリに配置するには：

```bash
# このスキルディレクトリから対象のリポジトリにコピー
cp -r .github /path/to/your/repository/

# またはGitで管理
cd /path/to/your/repository
git add .github/workflows/pr-review.yml
git commit -m "Add automated PR review workflow"
git push
```

### 4. CLAUDE.md設定ファイルの配置（オプションだが推奨）

`CLAUDE.md` をリポジトリルートに配置することで、レビュー基準をカスタマイズできます：

```bash
cp CLAUDE.md /path/to/your/repository/
cd /path/to/your/repository
git add CLAUDE.md
git commit -m "Add Claude Code review configuration"
git push
```

### 5. 権限の確認

ワークフローが正しく動作するために、以下の権限が必要です：

`.github/workflows/pr-review.yml` に既に設定されています：

```yaml
permissions:
  contents: write
  pull-requests: write
  issues: write
```

リポジトリの **Settings** → **Actions** → **General** で、
**Workflow permissions** が以下のように設定されていることを確認：

- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

## 使い方

### 自動レビュー

セットアップ完了後、以下のタイミングで自動的にレビューが実行されます：

- Pull Requestが作成されたとき
- Pull Requestが更新されたとき（新しいコミットがpushされたとき）
- Pull Requestが再オープンされたとき

### レビュー結果の確認

1. PRページの **Checks** タブで実行状況を確認
2. 完了後、PRにレビューコメントが自動投稿されます
3. 改善点があれば、Issueが自動的に作成されます

### レビュー結果の例

```markdown
## PR Review Summary

**Status**: ⚠️ Approved with suggestions

### Analysis Results

#### Code Quality: 8/10
- ✅ Good: 命名規則が適切
- ✅ Good: コードの構造が明確
- ⚠️ Minor: 一部のメソッドが長すぎる

#### Security: 9/10
- ✅ Good: 入力検証が適切
- ✅ Good: 認証処理が適切に実装されている

#### Testing: 7/10
- ✅ Good: ユニットテストが追加されている
- ⚠️ Major: 統合テストが不足している

#### Performance: 8/10
- ✅ Good: クエリが最適化されている

### Actions Taken
1. ✅ **Approved** with conditional approval
2. 📋 Created **Issue #124**: "🧪 [MAJOR] 統合テストの追加 (api.py)"
3. 📋 Created **Issue #125**: "🔧 [MINOR] メソッドのリファクタリング (service.py)"

### Summary
このPRは全体的に良好な品質です。条件付きでApproveし、改善項目をIssueとして起票しました。
```

## カスタマイズ

### レビュー基準の変更

`CLAUDE.md` を編集して、プロジェクト固有のレビュー基準を設定できます：

```markdown
## カスタムルール

### プロジェクト固有のチェック
- React Hooksの使用ルール
- TypeScriptの型定義の厳密性
- テストカバレッジの最低基準: 80%
```

### ワークフローのカスタマイズ

`.github/workflows/pr-review.yml` を編集して動作を変更できます：

```yaml
# 最大ターン数の変更
claude_args: "--max-turns 15"

# 特定のモデルを使用
claude_args: "--model claude-3-5-sonnet-20241022"

# 特定のブランチのみ対象
on:
  pull_request:
    branches: [main, develop]
    types: [opened, synchronize]
```

### トリガーの変更

PRコメントでレビューをトリガーする場合：

```yaml
on:
  issue_comment:
    types: [created]

jobs:
  review-on-command:
    if: github.event.issue.pull_request && contains(github.event.comment.body, '/review')
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "この PR を詳細にレビューしてください"
```

## トラブルシューティング

### ワークフローが実行されない

**原因**: 権限不足
**解決策**: Settings → Actions → General で "Read and write permissions" を有効化

### APIキーエラー

**エラー**: `Error: ANTHROPIC_API_KEY is not set`
**解決策**: シークレットが正しく設定されているか確認

### レビューコメントが投稿されない

**原因**: pull-requests権限不足
**解決策**: `permissions.pull-requests: write` が設定されているか確認

### Issueが作成されない

**原因**: issues権限不足
**解決策**: `permissions.issues: write` が設定されているか確認

## コスト管理

Claude APIの使用にはコストがかかります。以下の方法でコストを管理できます：

### レビュー対象の制限

```yaml
# ドラフトPRを除外
on:
  pull_request:
    types: [opened, synchronize]
    # ドラフトPRは自動的に除外される（ready_for_reviewイベントを追加で処理可能）

# 特定のファイルパターンのみ対象
jobs:
  review:
    runs-on: ubuntu-latest
    if: |
      contains(github.event.pull_request.changed_files, '.py') ||
      contains(github.event.pull_request.changed_files, '.js')
```

### ターン数の制限

```yaml
# 最大ターン数を減らす
claude_args: "--max-turns 5"
```

### 手動トリガーのみ

```yaml
on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: 'PR number to review'
        required: true
```

## セキュリティ

- **APIキーの管理**: シークレットとして保存し、コードにハードコードしない
- **権限の最小化**: 必要最低限の権限のみ付与
- **定期的な監査**: ワークフローログを定期的に確認

## サポート

問題が発生した場合：

1. GitHub Actionsのログを確認
2. このリポジトリのIssueを作成
3. [Claude Code ドキュメント](https://code.claude.com/docs)を参照

## 参考リンク

- [Claude Code GitHub Actions ドキュメント](https://code.claude.com/docs/ja/github-actions)
- [Anthropic API ドキュメント](https://docs.anthropic.com/)
- [GitHub Actions ドキュメント](https://docs.github.com/actions)
