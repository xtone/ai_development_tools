---
name: github-pr-reviewer
description: GitHub Pull Requestを自動的にレビューし、コード品質、セキュリティ、テスト、パフォーマンスを評価します。重大な問題がない場合は条件付きApproveを実施し、改善点があればIssueとして起票してPR作成者にアサインします。PRのURLまたは番号を指定して使用してください。
---

# GitHub PR Reviewer

## Overview

このスキルは、GitHub Pull Requestを包括的に自動レビューし、適切なフィードバックを提供します。AIがコード品質、セキュリティ、テスト、パフォーマンスの観点から評価を行い、以下のアクションを実行します：

- 重大な問題がない場合：条件付きApproveを実施
- 改善すべき点がある場合：Issueとして起票し、PR作成者にアサイン
- 即座にシステムに不具合を起こす問題がある場合：PR上にコメントして修正を要求

## When to Use This Skill

以下のような場合にこのスキルを使用してください：

- `github.com/owner/repo/pull/123` のようなPR URLが提供された時
- 「PR #123をレビューして」のようなリクエストがあった時
- レビュー対象のPRが明確に指定されている時

## Workflow

### 1. PR情報の取得

まず、指定されたPRの詳細情報を取得します：

- PRのタイトル、説明
- 変更されたファイル一覧
- コードの差分（diff）
- 既存のコメントやレビュー

```bash
python scripts/fetch_pr_info.py --pr-url <PR_URL>
```

### 2. コード分析とレビュー

以下の観点から自動的にコードを分析します：

#### コード品質
- 可読性：命名規則、コメントの適切性、コードの構造
- 保守性：重複コード、複雑度、モジュール化
- 設計パターン：適切なデザインパターンの使用
- ベストプラクティス：言語やフレームワーク固有のベストプラクティス

#### セキュリティ
- OWASP Top 10の脆弱性チェック
- 認証・認可の適切な実装
- 入力検証とサニタイゼーション
- 機密情報（API key、パスワードなど）の漏洩チェック
- SQLインジェクション、XSS、CSRF対策

#### テスト
- テストカバレッジ
- テストケースの妥当性
- エッジケースの考慮
- テストの保守性

#### パフォーマンス
- アルゴリズムの効率性（時間計算量、空間計算量）
- リソース使用量（メモリ、CPU）
- データベースクエリの最適化
- スケーラビリティの考慮

```bash
python scripts/analyze_pr.py --pr-data <PR_DATA_JSON>
```

### 3. レビュー結果の分類

分析結果を以下のカテゴリーに分類します：

- **Critical（致命的）**: 即座にシステムに不具合を起こす問題
- **Major（重要）**: セキュリティリスクや重大なバグの可能性
- **Minor（軽微）**: 改善の余地があるがすぐには影響しない問題
- **Suggestion（提案）**: ベストプラクティスや最適化の提案

### 4. アクションの実行

分類に基づいて適切なアクションを実行します：

**Critical問題がある場合:**
```bash
python scripts/post_review_comment.py \
  --pr-url <PR_URL> \
  --comment-type "REQUEST_CHANGES" \
  --findings <FINDINGS_JSON>
```

**Criticalがなく、MajorまたはMinor問題がある場合:**
```bash
# 条件付きApproveを実施
python scripts/approve_pr.py \
  --pr-url <PR_URL> \
  --comment "条件付きでApproveします。改善点をIssueとして起票しました。"

# 各問題をIssueとして起票
python scripts/create_issues.py \
  --pr-url <PR_URL> \
  --findings <FINDINGS_JSON> \
  --assignee <PR_AUTHOR>
```

**問題がない場合:**
```bash
python scripts/approve_pr.py \
  --pr-url <PR_URL> \
  --comment "コードレビューを完了しました。問題は見つかりませんでした。"
```

## Environment Setup

このスキルを使用するには、GitHub Personal Access Token（PAT）が必要です：

1. GitHubで以下のスコープを持つPATを生成：
   - `repo`（プライベートリポジトリの場合）
   - `public_repo`（パブリックリポジトリのみの場合）
   - `pull_requests:write`

2. 環境変数として設定：
```bash
export GITHUB_TOKEN="your_personal_access_token"
```

または、`~/.github_token`ファイルに保存することも可能です。

## Usage Examples

### 例1: PR URLを指定してレビュー
```
ユーザー: https://github.com/example/repo/pull/123 をレビューしてください
```

スキルは以下を実行します：
1. PR情報を取得
2. コードを分析
3. 問題を分類
4. 適切なアクションを実行（ApproveまたはIssue起票）

### 例2: PR番号とリポジトリ情報を指定
```
ユーザー: example/repo のPR #456をレビューして
```

### 例3: 特定の観点に絞ってレビュー
```
ユーザー: https://github.com/example/repo/pull/789 のセキュリティ面をレビューしてください
```

## Review Output Format

レビュー結果は以下の形式で出力されます：

```markdown
## PR Review Summary

**PR**: #123 - Feature: Add user authentication
**Author**: @username
**Status**: ✅ Approved with suggestions

### Analysis Results

#### Code Quality: 8/10
- ✅ Good: 命名規則が適切
- ✅ Good: コードの構造が明確
- ⚠️ Minor: 一部のメソッドが長すぎる（50行以上）

#### Security: 9/10
- ✅ Good: 入力検証が適切
- ✅ Good: 認証処理が適切に実装されている
- ⚠️ Minor: エラーメッセージに詳細な情報が含まれすぎている

#### Testing: 7/10
- ✅ Good: ユニットテストが追加されている
- ⚠️ Major: 統合テストが不足している
- ⚠️ Minor: エッジケースのテストが不十分

#### Performance: 8/10
- ✅ Good: クエリが最適化されている
- ⚠️ Minor: N+1問題の可能性がある箇所がある

### Actions Taken

1. ✅ **Approved** with conditional approval
2. 📋 Created **Issue #124**: "統合テストの追加" (assigned to @username)
3. 📋 Created **Issue #125**: "メソッドのリファクタリング" (assigned to @username)
4. 📋 Created **Issue #126**: "エラーハンドリングの改善" (assigned to @username)

### Summary

このPRは全体的に良好な品質です。重大な問題は見つかりませんでしたが、いくつかの改善点があります。条件付きでApproveし、改善項目をIssueとして起票しました。
```

## Resources

### scripts/

- `fetch_pr_info.py`: GitHub APIを使用してPR情報を取得
- `analyze_pr.py`: コードの包括的な分析を実行
- `approve_pr.py`: PRをApproveする
- `post_review_comment.py`: レビューコメントを投稿
- `create_issues.py`: 改善点をIssueとして起票
- `github_api.py`: GitHub API操作の共通モジュール

### references/

- `api_reference.md`: GitHub API v3/v4のリファレンス
- `review_checklist.md`: レビューチェックリストの詳細
- `security_patterns.md`: セキュリティパターンとアンチパターン
- `performance_guidelines.md`: パフォーマンス最適化のガイドライン

## Limitations

- PRが非常に大きい場合（1000ファイル以上）、分析に時間がかかる可能性があります
- 一部の言語やフレームワーク固有の高度な分析には限界があります
- レビューはAIによる自動分析であり、最終的な判断は人間が行う必要があります
