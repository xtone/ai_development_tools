---
name: github-pr-reviewer
description: GitHub ActionsでClaude Codeを使ってPull Requestを自動レビューします。コード品質、セキュリティ、テスト、パフォーマンスを評価し、重大な問題がない場合は条件付きApproveを実施、改善点があればIssueとして起票してPR作成者にアサインします。
---

# GitHub PR Reviewer

## Overview

このスキルは、GitHub Actions環境でClaude Codeを使用してPull Requestを包括的に自動レビューします。`gh`コマンドとGitHub MCPを活用し、以下のアクションを実行します：

- **コード分析**: 品質、セキュリティ、テスト、パフォーマンスの観点から評価
- **条件付きApprove**: 重大な問題がない場合にPRを承認
- **Issue起票**: 改善すべき点を個別のIssueとして起票し、PR作成者にアサイン
- **インラインコメント**: GitHub MCPを使用して特定のコード行にコメント
- **レビュー投稿**: Critical問題がある場合は変更要求（REQUEST_CHANGES）

## 前提条件

このスキルはGitHub Actions環境で実行されることを前提としています：

- ✅ `gh` CLI がインストール済み
- ✅ `GITHUB_TOKEN` 環境変数が設定済み
- ✅ GitHub MCPが利用可能（インラインコメント用）
- ✅ リポジトリとPR番号がプロンプトで提供される

## 入力パラメータ

GitHub Actionsワークフローから以下の情報が提供されます：

```yaml
リポジトリ: ${{ github.repository }}
PR番号: ${{ github.event.pull_request.number }}
ブランチ: ${{ github.event.pull_request.head.ref }}
作成者: ${{ github.event.pull_request.user.login }}
```

## レビューワークフロー

### ステップ1: PR情報の取得

`gh` コマンドを使用してPR情報を取得します：

```bash
# PR基本情報の取得
gh pr view ${PR_NUMBER} --json title,body,author,createdAt,headRefName,baseRefName,mergeable,reviewDecision

# 変更ファイル一覧の取得
gh pr diff ${PR_NUMBER} --name-only

# コード差分の取得
gh pr diff ${PR_NUMBER}

# 既存のレビューとコメントの確認
gh pr view ${PR_NUMBER} --json reviews,comments
```

### ステップ2: コード分析

以下の観点から包括的にコードを分析します：

#### 🔧 コード品質 (Code Quality)

- **可読性**
  - 命名規則: 変数名、関数名、クラス名が明確で理解しやすいか
  - コメント: 複雑なロジックに適切なコメントがあるか
  - コードの構造: 適切にモジュール化され、責務が分離されているか

- **保守性**
  - DRY原則: コードの重複がないか
  - 複雑度: 関数やメソッドが複雑すぎないか（循環的複雑度）
  - 依存関係: 適切な結合度が保たれているか

- **設計パターン**
  - デザインパターン: 適切なデザインパターンが使用されているか
  - SOLID原則: オブジェクト指向設計の原則が守られているか
  - アーキテクチャ: プロジェクトのアーキテクチャパターンに準拠しているか

- **ベストプラクティス**
  - 言語固有: 使用言語のイディオムやベストプラクティスに従っているか
  - フレームワーク: 使用フレームワークの推奨パターンに従っているか
  - コーディング規約: プロジェクトのコーディング規約に準拠しているか

#### 🔒 セキュリティ (Security)

- **OWASP Top 10**
  - インジェクション: SQLインジェクション、コマンドインジェクションの脆弱性
  - 認証の不備: 不適切な認証実装、セッション管理の問題
  - データ露出: 機密データの不適切な公開
  - XXE: XMLの外部エンティティ処理の脆弱性
  - アクセス制御: 不適切な認可処理
  - セキュリティ設定ミス: デフォルト設定の使用、不要な機能の有効化
  - XSS: クロスサイトスクリプティングの脆弱性
  - 安全でないデシリアライゼーション
  - 脆弱な依存関係: 既知の脆弱性を持つライブラリの使用
  - ログとモニタリング: 不十分なログ記録

- **認証・認可**
  - 認証フロー: ログイン、ログアウトの適切な実装
  - トークン管理: JWTなどのトークンの安全な取り扱い
  - パスワード: 適切なハッシュ化、保存方法
  - 多要素認証: 適切なMFA実装（該当する場合）

- **入力検証とサニタイゼーション**
  - ユーザー入力: すべてのユーザー入力が検証されているか
  - サニタイゼーション: XSS対策のための適切なエスケープ
  - ホワイトリスト: 許可リストによる検証アプローチ

- **機密情報**
  - ハードコードされたシークレット: APIキー、パスワードの埋め込み
  - 環境変数: 機密情報の適切な管理
  - ログ出力: ログに機密情報が含まれていないか

- **暗号化**
  - データの暗号化: 通信時および保存時の暗号化
  - 暗号アルゴリズム: 安全なアルゴリズムの使用
  - 鍵管理: 暗号鍵の適切な管理

#### 🧪 テスト (Testing)

- **テストカバレッジ**
  - ユニットテスト: 新しい関数やメソッドに対するテスト
  - 統合テスト: コンポーネント間の統合に対するテスト
  - E2Eテスト: エンドツーエンドのユーザーフローテスト

- **テストケースの妥当性**
  - 正常系: 期待される動作のテスト
  - 異常系: エラーケースのテスト
  - エッジケース: 境界値、極端な入力のテスト
  - テストデータ: 適切なテストデータの使用

- **テストの品質**
  - テストの独立性: 各テストが独立して実行可能か
  - テストの保守性: テストコードが理解しやすく保守しやすいか
  - モック/スタブ: 適切なモックやスタブの使用
  - アサーション: 明確で適切なアサーション

#### ⚡ パフォーマンス (Performance)

- **アルゴリズムの効率性**
  - 時間計算量: O(n)、O(n²)などの計算量の評価
  - 空間計算量: メモリ使用量の評価
  - 最適化: より効率的なアルゴリズムの提案

- **リソース使用**
  - メモリリーク: 不要なオブジェクトの保持
  - CPU使用: 不必要な計算の削減
  - I/O: 効率的なファイル操作、ネットワーク通信

- **データベース**
  - クエリ最適化: インデックスの使用、効率的なクエリ
  - N+1問題: 繰り返しクエリの検出
  - トランザクション: 適切なトランザクション管理
  - コネクションプール: データベース接続の効率的な管理

- **スケーラビリティ**
  - 大規模データ: 大量のデータ処理への対応
  - 高負荷: 同時リクエストへの対応
  - キャッシング: 適切なキャッシュ戦略

### ステップ3: 問題の分類

検出された問題を以下のカテゴリーに分類します：

| 重要度 | 説明 | スコア影響 | アクション |
|--------|------|------------|------------|
| **Critical** | 即座にシステムに不具合を起こす問題。マージ前に必ず修正が必要 | -3点 | REQUEST_CHANGES |
| **Major** | セキュリティリスクや重大なバグの可能性。優先的に修正すべき | -2点 | Issue起票 (high) |
| **Minor** | 改善の余地があるがすぐには影響しない問題 | -1点 | Issue起票 (medium) |
| **Suggestion** | ベストプラクティスや最適化の提案 | -0.5点 | Issue起票 (low) |

**スコアリング**: 各カテゴリーを10点満点で評価し、検出された問題の重要度に応じて減点します。

### ステップ4: レビュー結果の投稿

#### パターン1: Critical問題がある場合

`gh` コマンドを使用してREQUEST_CHANGESレビューを投稿：

```bash
gh pr review ${PR_NUMBER} \
  --request-changes \
  --body "## ⚠️ 変更が必要です

以下のCritical問題が検出されました。修正してから再度レビューをリクエストしてください。

### Critical問題

[問題の詳細リスト]

修正後、このレビューを解決してください。"
```

**インラインコメントが必要な場合**は、GitHub MCPを使用：

```typescript
// GitHub MCPを使用してインラインコメントを投稿
mcp__github__create_review_comment({
  repo: repository,
  pr_number: prNumber,
  body: "この行にセキュリティ脆弱性があります...",
  path: "src/auth.ts",
  line: 42
})
```

#### パターン2: Major/Minor問題がある場合

1. **条件付きApproveを実施**：

```bash
gh pr review ${PR_NUMBER} \
  --approve \
  --body "## ✅ 条件付きでApprove

コードレビューを完了しました。重大な問題は見つかりませんでしたが、いくつかの改善点があります。

### 分析結果

#### Code Quality: X/10
[詳細]

#### Security: X/10
[詳細]

#### Testing: X/10
[詳細]

#### Performance: X/10
[詳細]

### 改善項目

改善点をIssueとして起票しました。ご確認ください：
- Issue #XXX
- Issue #YYY

これらは次のイテレーションで対応することをお勧めします。"
```

2. **各問題をIssueとして起票**：

```bash
# Major問題の例
gh issue create \
  --title "🔒 [MAJOR] 入力検証が不十分 (src/api/handler.ts)" \
  --body "## 概要
PR #${PR_NUMBER} のレビューで検出されたセキュリティ上の改善点です。

**関連PR**: #${PR_NUMBER}

## 詳細
**カテゴリー**: security
**重要度**: major
**ファイル**: \`src/api/handler.ts\`

### 問題
ユーザー入力の検証が不十分で、インジェクション攻撃のリスクがあります。

### 推奨される対応
1. すべてのユーザー入力に対してバリデーションを追加
2. ホワイトリスト方式での検証を実装
3. サニタイゼーション処理を追加

## チェックリスト
- [ ] 問題を確認
- [ ] 修正を実装
- [ ] テストを追加/更新
- [ ] セキュリティレビューを実施" \
  --assignee "${PR_AUTHOR}" \
  --label "priority:high,security"
```

#### パターン3: 問題がない場合

```bash
gh pr review ${PR_NUMBER} \
  --approve \
  --body "## ✅ Approved

コードレビューを完了しました。問題は見つかりませんでした。

### 分析結果

#### Code Quality: 10/10
✅ すべての基準を満たしています

#### Security: 10/10
✅ セキュリティ上の問題は検出されませんでした

#### Testing: 10/10
✅ 適切なテストカバレッジがあります

#### Performance: 10/10
✅ パフォーマンス上の問題は見つかりませんでした

### Summary

素晴らしいコードです！マージして問題ありません。"
```

### ステップ5: 除外パターン

以下のファイルや変更は自動レビューから除外します：

- ロックファイル: `package-lock.json`, `yarn.lock`, `Gemfile.lock`, `poetry.lock`, `Cargo.lock`
- 依存関係ディレクトリ: `node_modules/`, `vendor/`, `target/`, `build/`, `dist/`
- 自動生成ファイル: `*.generated.*`, `*.auto.*`, `*_pb2.py`, `*.g.dart`
- バイナリファイル: 画像、動画、フォント、実行ファイル
- 大規模データファイル: 1000行以上のJSON、CSV、XMLなど
- 設定ファイル: `.env.example`, `docker-compose.yml`（変更が小規模な場合）

## 使用例

### GitHub Actionsから実行

```yaml
- name: Run Claude Code PR Review
  uses: anthropics/claude-code-action@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    prompt: |
      以下のPull Requestを包括的にレビューしてください：

      **リポジトリ**: ${{ github.repository }}
      **PR番号**: ${{ github.event.pull_request.number }}
      **ブランチ**: ${{ github.event.pull_request.head.ref }}
      **作成者**: ${{ github.event.pull_request.user.login }}

      スキル `github-pr-reviewer` を使用してレビューを実行してください。

      以下の観点から分析してください：
      1. コード品質（可読性、保守性、設計パターン）
      2. セキュリティ（OWASP Top 10、認証・認可、入力検証）
      3. テスト（カバレッジ、妥当性、エッジケース）
      4. パフォーマンス（アルゴリズム効率、リソース使用、DB最適化）

      レビュー後、以下のアクションを実行してください：
      - Critical問題がある場合: REQUEST_CHANGESレビューを投稿（ghコマンド使用）
      - Major/Minor問題がある場合: 条件付きApprove + Issue起票（ghコマンド使用）
      - 問題がない場合: Approveレビューを投稿（ghコマンド使用）

      インラインコメントが必要な場合は、GitHub MCPを使用してください。
```

## 出力形式

### レビューコメントのテンプレート

```markdown
## [絵文字] [ステータス]

### 分析結果

#### Code Quality: X/10
- ✅ Good: [良い点]
- ⚠️ Minor: [改善点]
- ❌ Critical: [致命的な問題]

#### Security: X/10
[同様の形式]

#### Testing: X/10
[同様の形式]

#### Performance: X/10
[同様の形式]

### 実行されたアクション

1. [アクション1の説明]
2. 📋 Created **Issue #XXX**: "[タイトル]" (assigned to @username)
3. [追加のアクション]

### Summary

[総合的な評価と推奨事項]
```

### Issueタイトルの形式

```
[絵文字] [SEVERITY] 問題の概要 (ファイル名)
```

**絵文字の対応**:
- 🔧 code-quality
- 🔒 security
- 🧪 testing
- ⚡ performance

**重要度の表記**:
- `[CRITICAL]`: 致命的な問題
- `[MAJOR]`: 重要な問題
- `[MINOR]`: 軽微な問題
- `[SUGGESTION]`: 提案

## 制限事項

- PRが非常に大きい場合（500ファイル以上、10,000行以上の変更）、分析に時間がかかるか、一部のファイルを省略する必要があります
- 言語やフレームワーク固有の高度な分析には限界があります
- ビジネスロジックやドメイン知識が必要な判断は人間のレビューが必要です
- AIによる自動分析であり、最終的な判断は人間のレビュアーが行う必要があります

## トラブルシューティング

### `gh` コマンドが見つからない

GitHub Actionsワークフローに以下のステップを追加：

```yaml
- name: Setup GitHub CLI
  run: |
    type -p gh >/dev/null || (sudo apt update && sudo apt install gh)
```

### GitHub MCPが利用できない

インラインコメントをスキップし、通常のレビューコメントのみ投稿します。

### 権限エラー

`GITHUB_TOKEN` に以下の権限が必要です：
- `pull-requests: write`
- `issues: write`
- `contents: read`

## 関連ドキュメント

- [GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md): GitHub Actionsの詳細な設定方法
- [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md): GitHub MCPの統合方法
- [PERMISSIONS_GUIDE.md](./PERMISSIONS_GUIDE.md): 必要な権限の設定方法
- [VERTEX_AI_SETUP.md](./VERTEX_AI_SETUP.md): Vertex AIを使用する場合の設定方法
