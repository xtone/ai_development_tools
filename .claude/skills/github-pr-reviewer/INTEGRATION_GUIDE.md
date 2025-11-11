# 既存リポジトリへの統合ガイド

既にClaude Code Actionsが動作しているリポジトリに、このPRレビュースキルを追加する方法を説明します。

## 前提条件

既存リポジトリで以下のいずれかが動作していることを想定：

- Claude Code GitHub Actionsワークフローが存在
- `CLAUDE.md` などの設定ファイルが存在
- Anthropic APIキーまたはVertex AI設定が完了

## 統合方法

### 方法1: CLAUDE.md を拡張する（推奨）

既存の `CLAUDE.md` にこのスキルのレビュー基準を追加します。

#### 手順

1. **既存の CLAUDE.md を確認**

```bash
# リポジトリルートで確認
cat CLAUDE.md
```

2. **このスキルの CLAUDE.md を追加**

既存の内容を保持したまま、PRレビューセクションを追加：

```bash
# このスキルのCLAUDE.mdの内容を既存ファイルに追加
cat /path/to/github-pr-reviewer/CLAUDE.md >> CLAUDE.md
```

または、手動で以下のセクションを既存 `CLAUDE.md` に追加：

```markdown
---

# Pull Request レビュー設定

以下、Pull Requestの自動レビュー時に使用する基準とワークフローです。

## レビュー基準

### コード品質
- **可読性**: 明確な変数名、適切なコメント、一貫したコーディングスタイル
- **保守性**: DRY原則、適切なモジュール化、低い結合度
...（CLAUDE.mdの内容をコピー）
```

3. **プロジェクト固有のルールを追加**

既存のコーディング規約やレビュー基準を追加：

```markdown
## プロジェクト固有のレビュールール

### フレームワーク固有のルール
- React Hooksは必ずuseCallbackまたはuseMemoで最適化すること
- TypeScriptの型定義は `any` を使用しない

### テスト要件
- 新機能には必ずユニットテストを追加
- カバレッジは最低80%を維持

### セキュリティ要件
- 環境変数は `.env.example` にサンプルを記載
- 外部APIへのリクエストは必ずタイムアウトを設定
```

4. **コミット**

```bash
git add CLAUDE.md
git commit -m "Add PR review guidelines to CLAUDE.md"
git push
```

---

### 方法2: 専用ワークフローを追加する

既存のワークフローとは別に、PR専用のレビューワークフローを追加します。

#### 既存ワークフローとの共存

**既存**: `@claude` メンション時に動作するワークフロー
**新規**: PR作成/更新時に自動レビューするワークフロー

この2つは競合せずに共存できます。

#### 手順

1. **既存のワークフローを確認**

```bash
ls -la .github/workflows/
```

例：
```
.github/workflows/
├── claude-code.yml          # 既存（@claudeメンション時）
└── (ここに新しいワークフローを追加)
```

2. **PRレビューワークフローをコピー**

使用する認証方法に応じて選択：

**GITHUB_TOKEN使用（シンプル）**:
```bash
cp /path/to/github-pr-reviewer/.github/workflows/pr-review.yml \
   .github/workflows/pr-review.yml
```

**GitHub App使用（エンタープライズ）**:
```bash
cp /path/to/github-pr-reviewer/.github/workflows/pr-review-with-github-app.yml \
   .github/workflows/pr-review-with-github-app.yml
```

**Vertex AI使用**:
```bash
cp /path/to/github-pr-reviewer/.github/workflows/pr-review-vertex-ai.yml \
   .github/workflows/pr-review-vertex-ai.yml
```

3. **トリガー条件を調整**（オプション）

既存ワークフローとの競合を避けるため、条件を調整：

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches:
      - main           # mainブランチへのPRのみ
    paths-ignore:
      - '**.md'        # ドキュメントのみの変更は除外
      - 'docs/**'
```

4. **ワークフロー名を変更**（オプション）

既存ワークフローと区別しやすくするため：

```yaml
name: Automated PR Review (Auto)  # 既存と区別できる名前に
```

5. **コミット**

```bash
git add .github/workflows/pr-review*.yml
git commit -m "Add automated PR review workflow"
git push
```

---

### 方法3: 既存ワークフローを拡張する

既存のClaude Code Actionsワークフローに、PRレビュー機能を追加します。

#### 手順

1. **既存ワークフローを確認**

```yaml
# 既存: .github/workflows/claude-code.yml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]

jobs:
  claude-code:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

2. **PRトリガーを追加**

```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  pull_request:                    # 追加
    types: [opened, synchronize]   # 追加

jobs:
  claude-code:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |                # 追加（PR時のプロンプト）
            ${{ github.event_name == 'pull_request' && 'このPRを包括的にレビューしてください。コード品質、セキュリティ、テスト、パフォーマンスの観点から分析し、問題があればIssueとして起票してください。' || '' }}
```

3. **条件分岐でジョブを分ける**（推奨）

PRレビューと通常のコメント対応を分離：

```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  # 通常のコメント対応
  claude-interactive:
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}

  # PR自動レビュー
  claude-pr-review:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            このPull Requestを包括的にレビューしてください。

            以下の観点から分析を行ってください：
            1. コード品質（可読性、保守性、設計パターン、ベストプラクティス）
            2. セキュリティ（OWASP Top 10、認証・認可、入力検証、機密情報漏洩）
            3. テスト（カバレッジ、テストケースの妥当性、エッジケース）
            4. パフォーマンス（アルゴリズム効率、リソース使用、N+1問題）

            Critical問題があれば変更要求、そうでなければ条件付きApproveし、
            改善点はIssueとして起票してください。
```

---

## 統合パターン別の推奨

### パターン1: 既存設定を維持したい

**推奨**: 方法1（CLAUDE.md拡張）

- 既存の `CLAUDE.md` を維持
- PRレビュー基準を追加
- 既存ワークフローで自動的に適用される

**メリット**:
- 設定ファイルが1つで管理しやすい
- 既存の運用を変更不要

---

### パターン2: PR専用の自動化が欲しい

**推奨**: 方法2（専用ワークフロー追加）

- PR専用のワークフローを追加
- 既存ワークフローと共存
- トリガー条件を明確に分離

**メリット**:
- PRレビューは自動、その他は手動という使い分けが可能
- 設定を独立して管理できる
- 既存ワークフローへの影響なし

---

### パターン3: 統合的に管理したい

**推奨**: 方法3（既存ワークフロー拡張）

- 1つのワークフローで全て管理
- イベントタイプで条件分岐

**メリット**:
- ワークフローファイルが1つで済む
- 認証情報の管理が一元化

**デメリット**:
- ワークフローが複雑になる可能性

---

## スキルの利用（Claude Code CLI）

既存リポジトリでClaude Code CLIからこのスキルを使う場合：

### 前提条件

このスキルが Claude Code のスキルディレクトリにインストールされている：

```bash
ls ~/.claude/skills/github-pr-reviewer/
```

### 使用方法

リポジトリのディレクトリで：

```bash
# Claude Code CLIを起動
claude

# PRをレビュー
> https://github.com/your-org/your-repo/pull/123 をレビューしてください
```

Claude Code が自動的に `github-pr-reviewer` スキルを認識して実行します。

---

## トラブルシューティング

### ワークフローが重複実行される

**原因**: 複数のワークフローが同じイベントでトリガーされている

**解決策**: トリガー条件を調整

```yaml
# 既存ワークフロー: コメント時のみ
on:
  issue_comment:
    types: [created]

# 新規ワークフロー: PR作成/更新時のみ
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

---

### CLAUDE.md の設定が適用されない

**原因**: CLAUDE.md の構文エラーまたは読み込まれていない

**確認方法**:
```bash
# CLAUDE.mdの構文確認
cat CLAUDE.md

# ワークフローログで読み込みを確認
# Actions → 該当ワークフロー → ログを確認
```

**解決策**:
- マークダウンの構文を確認
- セクション区切りが正しいか確認
- ワークフローが最新のClaude Code Actionを使用しているか確認

---

### 既存の設定とレビュー基準が競合する

**原因**: CLAUDE.md に矛盾する指示が存在

**解決策**: セクションを明確に分ける

```markdown
# プロジェクト全体の設定

（既存の設定）

---

# Pull Request レビュー専用設定

（このスキルのレビュー基準）

## レビュー時のみ適用されるルール
- 以下のルールはPRレビュー時にのみ適用されます
- ...
```

---

### 権限エラーが発生する

**原因**: シークレットや権限設定が不足

**確認事項**:
1. `ANTHROPIC_API_KEY` が設定されているか
2. GitHub App使用時: `APP_ID`, `APP_PRIVATE_KEY` が設定されているか
3. Vertex AI使用時: GCP関連のシークレットが設定されているか
4. ワークフローの `permissions` セクションが正しいか

**解決策**: [PERMISSIONS_GUIDE.md](./PERMISSIONS_GUIDE.md) を参照

---

## 実例: 統合手順（方法2推奨）

実際のプロジェクトで方法2を使用する場合の手順：

### 1. 現状確認

```bash
cd /path/to/your/existing/repo

# 既存ワークフローを確認
ls .github/workflows/

# 既存CLAUDE.mdを確認
cat CLAUDE.md
```

### 2. PRレビューワークフローを追加

```bash
# このスキルから適切なワークフローをコピー
cp /path/to/github-pr-reviewer/.github/workflows/pr-review.yml \
   .github/workflows/pr-review.yml
```

### 3. CLAUDE.md にレビュー基準を追加

```bash
# 既存のCLAUDE.mdの末尾に追加
echo "" >> CLAUDE.md
echo "---" >> CLAUDE.md
echo "" >> CLAUDE.md
cat /path/to/github-pr-reviewer/CLAUDE.md >> CLAUDE.md
```

### 4. プロジェクト固有の設定を追加

`CLAUDE.md` を編集して、プロジェクト固有のルールを追加：

```markdown
## プロジェクト固有のレビュールール

### 必須チェック項目
- TypeScriptの型定義の厳密性
- React Hooksの適切な使用
- テストカバレッジ80%以上

### 除外パターン
- `*.test.ts` ファイルのコメント不足は許容
- `generated/` ディレクトリは自動生成のためレビュー不要
```

### 5. コミット＆プッシュ

```bash
git add .github/workflows/pr-review.yml CLAUDE.md
git commit -m "Add automated PR review workflow and guidelines"
git push
```

### 6. テスト

テストPRを作成して動作確認：

```bash
git checkout -b test/pr-review
echo "# Test" >> TEST.md
git add TEST.md
git commit -m "Test PR review workflow"
git push origin test/pr-review

# GitHub上でPRを作成
# ワークフローが自動実行されることを確認
```

---

## ベストプラクティス

### 1. 段階的な導入

最初は一部のブランチのみで試す：

```yaml
on:
  pull_request:
    branches:
      - develop      # まずdevelopブランチのみ
    types: [opened, synchronize, reopened]
```

問題なければ、mainブランチにも適用：

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

### 2. 通知の調整

レビューが多すぎる場合、通知を調整：

- ドラフトPRは除外
- ドキュメントのみの変更は除外
- 小規模な変更（10行未満）は除外

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### 3. コスト管理

API使用量を抑えるため：

```yaml
claude_args: "--max-turns 5"  # ターン数を制限
```

または、手動トリガーのみに変更：

```yaml
on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: 'PR number to review'
        required: true
```

---

## まとめ

| 方法 | 用途 | 難易度 | 推奨度 |
|------|------|--------|--------|
| 方法1: CLAUDE.md拡張 | 既存設定維持 | ⭐ 低 | ⭐⭐⭐ |
| 方法2: 専用ワークフロー | PR専用自動化 | ⭐⭐ 中 | ⭐⭐⭐⭐⭐ |
| 方法3: 既存ワークフロー拡張 | 統合管理 | ⭐⭐⭐ 高 | ⭐⭐⭐ |

**最も推奨**: 方法2（専用ワークフロー追加）
- 既存の運用に影響を与えない
- PR専用の自動化が実現できる
- 設定を独立して管理できる
