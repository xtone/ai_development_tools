# GitHub PR Reviewer Skill

GitHub Pull Requestを自動的にレビューし、コード品質、セキュリティ、テスト、パフォーマンスを評価するClaude Skillです。

## 概要

このスキルは以下の機能を提供します：

- PR情報の自動取得
- コード品質、セキュリティ、テスト、パフォーマンスの包括的な分析
- 重大な問題がない場合の条件付きApprove
- 改善点のIssue自動起票（PR作成者にアサイン）
- Critical問題発見時の変更要求

## クイックスタート

### 新規リポジトリの場合
このREADMEの「セットアップ」セクションを参照してください。

### 既にClaude Code Actionsが動作しているリポジトリの場合
**[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** を参照してください。

既存の設定を保ったまま、このPRレビュースキルを追加する方法を詳しく説明しています。

## セットアップ

### 1. GitHub Personal Access Token (PAT) の取得

1. GitHubの Settings → Developer settings → Personal access tokens → Tokens (classic) に移動
2. "Generate new token (classic)" をクリック
3. 以下のスコープを選択：
   - `repo` (プライベートリポジトリの場合)
   - `public_repo` (パブリックリポジトリのみの場合)
4. トークンを生成してコピー

### 2. トークンの設定

以下のいずれかの方法でトークンを設定：

**方法1: 環境変数**
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

**方法2: ファイル保存**
```bash
echo "your_github_personal_access_token" > ~/.github_token
chmod 600 ~/.github_token
```

### 3. スキルのインストール

このスキルを Claude Code のスキルディレクトリに配置します。

```bash
# スキルディレクトリの例
~/.claude/skills/github-pr-reviewer/
```

## 使い方

このスキルは3つの方法で使用できます：

### 方法1: GitHub Actions（推奨）

**自動的にPRを作成/更新時にレビューを実行**

#### オプションA: Anthropic API（直接）

詳細なセットアップ手順は [GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md) を参照してください。

**2つの認証方法**:

**A-1. GITHUB_TOKEN使用（シンプル）**
```
実行ユーザー: github-actions[bot]
ワークフロー: pr-review.yml
```
簡易セットアップ：
1. Anthropic APIキーをリポジトリシークレットに追加（`ANTHROPIC_API_KEY`）
2. `.github/workflows/pr-review.yml` をリポジトリにコピー
3. PRを作成すると自動的にレビューが実行されます

**A-2. GitHub App使用（推奨・エンタープライズ）**
```
実行ユーザー: [カスタムApp名][bot]
ワークフロー: pr-review-with-github-app.yml
```
簡易セットアップ：
1. GitHub Appを作成（詳細は [PERMISSIONS_GUIDE.md](./PERMISSIONS_GUIDE.md)）
2. Anthropic APIキーとGitHub App情報をシークレットに追加
3. `.github/workflows/pr-review-with-github-app.yml` をリポジトリにコピー

**権限の詳細**: [PERMISSIONS_GUIDE.md](./PERMISSIONS_GUIDE.md) を参照

#### オプションB: Google Cloud Vertex AI（エンタープライズ向け）

詳細なセットアップ手順は [VERTEX_AI_SETUP.md](./VERTEX_AI_SETUP.md) を参照してください。

**メリット**:
- エンタープライズサポート
- データレジデンシーの管理
- Google Cloudとの統合課金
- Workload Identity Federationによる安全な認証

簡易セットアップ：
1. Google Cloud でVertex AI APIを有効化
2. Workload Identity Federationを設定
3. GitHub Secretsを設定（`GCP_WORKLOAD_IDENTITY_PROVIDER`、`GCP_SERVICE_ACCOUNT`など）
4. `.github/workflows/pr-review-vertex-ai.yml` をリポジトリにコピー
5. PRを作成すると自動的にレビューが実行されます

### 方法2: Claude Code CLI（手動実行）

Claude Code で以下のようにリクエストしてください：

```
https://github.com/owner/repo/pull/123 をレビューしてください
```

または

```
owner/repo のPR #456をレビューして
```

### スキルが自動的に実行する処理

1. **PR情報の取得**: PRの詳細、変更ファイル、コミット履歴を取得
2. **コード分析**: 以下の観点から分析
   - コード品質（可読性、保守性、設計パターン）
   - セキュリティ（脆弱性、認証・認可、入力検証）
   - テスト（カバレッジ、テストケースの妥当性）
   - パフォーマンス（アルゴリズム効率、リソース使用）
3. **結果の分類**: Critical/Major/Minor/Suggestionに分類
4. **アクションの実行**:
   - Critical問題がある場合: 変更要求（REQUEST_CHANGES）
   - Major/Minor問題がある場合: 条件付きApprove + Issue起票
   - 問題がない場合: Approve

## スクリプト

このスキルには以下のPythonスクリプトが含まれています：

### github_api.py
GitHub API操作の共通モジュール

### fetch_pr_info.py
PR情報を取得してJSON形式で出力

```bash
python scripts/fetch_pr_info.py --pr-url https://github.com/owner/repo/pull/123
```

### analyze_pr.py
PR情報を分析してコード品質、セキュリティ、テスト、パフォーマンスを評価

```bash
python scripts/analyze_pr.py --pr-data pr_info.json
```

### approve_pr.py
PRをApprove

```bash
python scripts/approve_pr.py --pr-url https://github.com/owner/repo/pull/123 --analysis analysis.json
```

### post_review_comment.py
変更要求のレビューコメントを投稿

```bash
python scripts/post_review_comment.py --pr-url https://github.com/owner/repo/pull/123 --findings analysis.json
```

### create_issues.py
分析結果から改善点をIssueとして起票

```bash
python scripts/create_issues.py --pr-url https://github.com/owner/repo/pull/123 --findings analysis.json
```

## レビュー出力例

```markdown
## PR Review Summary

**PR**: #123 - Feature: Add user authentication
**Author**: @username
**Status**: ✅ Approved with suggestions

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
2. 📋 Created **Issue #124**: "統合テストの追加" (assigned to @username)
3. 📋 Created **Issue #125**: "メソッドのリファクタリング" (assigned to @username)

### Summary

このPRは全体的に良好な品質です。条件付きでApproveし、改善項目をIssueとして起票しました。
```

## 制限事項

- PRが非常に大きい（1000ファイル以上）場合、分析に時間がかかる可能性があります
- 一部の言語やフレームワーク固有の高度な分析には限界があります
- レビューはAIによる自動分析であり、最終的な判断は人間が行う必要があります

## トラブルシューティング

### 認証エラー
```
GitHub token not found. Please set GITHUB_TOKEN environment variable
```

→ GitHub Personal Access Tokenが設定されていません。セットアップ手順を確認してください。

### 権限エラー
```
403 Forbidden
```

→ トークンに必要な権限がないか、レート制限に達しています。トークンのスコープを確認してください。

### PR URLが無効
```
Invalid PR URL
```

→ PR URLの形式が正しくありません。`https://github.com/owner/repo/pull/123` の形式で指定してください。

## ライセンス

このスキルはMITライセンスの下で提供されます。

## 貢献

バグ報告や機能要望は、GitHubのIssueでお願いします。
