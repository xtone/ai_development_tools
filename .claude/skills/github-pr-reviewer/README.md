# GitHub PR Reviewer Skill

GitHub Pull Requestを自動的にレビューし、コード品質、セキュリティ、テスト、パフォーマンスを評価するClaude Codeスキルです。

## 概要

このスキルは**GitHub Actions専用**で、以下の機能を提供します：

- `gh`コマンドを使用したPR情報の取得
- コード品質、セキュリティ、テスト、パフォーマンスの包括的な分析
- 重大な問題がない場合の条件付きApprove
- 改善点のIssue自動起票（PR作成者にアサイン）
- Critical問題発見時の変更要求
- GitHub MCPを使用したインラインコメント（オプション）

## 特徴

- ✅ **シンプル**: Pythonスクリプト不要、プロンプトベースの実装
- ✅ **標準ツール**: `gh`コマンドのみ使用
- ✅ **柔軟性**: GitHub MCPでインラインコメントが可能
- ✅ **複数の認証方式**: Anthropic API、GitHub App、Vertex AI

## クイックスタート

### 前提条件

- GitHub Actions環境
- `gh` CLIがインストール済み（通常のGitHub Actions環境には含まれています）
- GitHub MCPがインストール済み（インラインコメント用、オプション）

### 基本セットアップ

1. **スキルファイルをリポジトリに配置**

```bash
# スキルディレクトリを .claude/skills/ にコピー
cp -r github-pr-reviewer /path/to/your/repo/.claude/skills/
```

2. **ワークフローファイルを選択して配置**

3つのオプションから選択:

#### オプション1: Anthropic API（直接）

```bash
cp .github/workflows/pr-review.yml /path/to/your/repo/.github/workflows/
```

**必要なシークレット**:
- `ANTHROPIC_API_KEY`: Anthropic APIキー

#### オプション2: GitHub App（推奨）

```bash
cp .github/workflows/pr-review-with-github-app.yml /path/to/your/repo/.github/workflows/
```

**必要なシークレット**:
- `ANTHROPIC_API_KEY`: Anthropic APIキー
- `APP_ID`: GitHub AppのID
- `APP_PRIVATE_KEY`: GitHub Appの秘密鍵

#### オプション3: Vertex AI（エンタープライズ向け）

```bash
cp .github/workflows/pr-review-vertex-ai.yml /path/to/your/repo/.github/workflows/
```

**必要なシークレット**:
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: GCPのWorkload Identity Provider
- `GCP_SERVICE_ACCOUNT`: GCPのサービスアカウント
- `APP_ID`: GitHub AppのID
- `APP_PRIVATE_KEY`: GitHub Appの秘密鍵

3. **PRを作成**

PRを作成または更新すると、自動的にレビューが実行されます。

## 使用方法

### GitHub Actionsでの自動実行

PR作成・更新時に自動実行されます。ワークフローは以下を実行します：

1. `gh`コマンドでPR情報を取得
2. スキル `github-pr-reviewer` を呼び出し
3. コードを包括的に分析
4. レビュー結果を投稿
5. 必要に応じてIssueを起票

### レビュー観点

以下の4つの観点から分析します：

#### 🔧 コード品質
- 可読性、保守性
- 設計パターン、ベストプラクティス
- コーディング規約

#### 🔒 セキュリティ
- OWASP Top 10
- 認証・認可、入力検証
- 機密情報漏洩チェック

#### 🧪 テスト
- テストカバレッジ
- テストケースの妥当性
- エッジケース

#### ⚡ パフォーマンス
- アルゴリズム効率
- リソース使用
- データベース最適化

### レビュー結果のアクション

| 問題の重要度 | アクション |
|------------|------------|
| **Critical** | REQUEST_CHANGES（変更要求） |
| **Major/Minor** | 条件付きApprove + Issue起票 |
| **なし** | Approve |

## 高度な設定

### インラインコメントの有効化

GitHub MCPをインストールすることで、特定のコード行にコメントを投稿できます：

```bash
# GitHub MCPのインストール（Claude Code環境）
npm install -g @anthropic-ai/github-mcp
```

スキルは自動的にGitHub MCPを検出し、必要に応じて使用します。

### カスタムレビュー基準

`CLAUDE.md`ファイルを編集してレビュー基準をカスタマイズできます：

```markdown
### コード品質
- **可読性**: [カスタム基準]
- **保守性**: [カスタム基準]
...
```

## ディレクトリ構造

```
github-pr-reviewer/
├── SKILL.md                      # スキルのメインロジック
├── CLAUDE.md                     # レビュー基準とガイドライン
├── README.md                     # このファイル
├── GITHUB_ACTIONS_SETUP.md       # GitHub Actions設定ガイド
├── INTEGRATION_GUIDE.md          # 統合ガイド
├── PERMISSIONS_GUIDE.md          # 権限設定ガイド
├── VERTEX_AI_SETUP.md            # Vertex AI設定ガイド
├── .github/workflows/
│   ├── pr-review.yml             # Anthropic API版
│   ├── pr-review-with-github-app.yml  # GitHub App版
│   └── pr-review-vertex-ai.yml   # Vertex AI版
└── assets/                       # ドキュメント用画像
```

## トラブルシューティング

### `gh`コマンドが見つからない

GitHub Actionsワークフローに以下を追加：

```yaml
- name: Setup GitHub CLI
  run: |
    type -p gh >/dev/null || (sudo apt update && sudo apt install gh)
```

### 権限エラー

`GITHUB_TOKEN`に以下の権限が必要です：
- `pull-requests: write`
- `issues: write`
- `contents: read`

ワークフローファイルの`permissions`セクションを確認してください。

### GitHub MCPが動作しない

GitHub MCPは必須ではありません。利用できない場合、通常のレビューコメントのみが投稿されます。

## 詳細ドキュメント

- **[SKILL.md](./SKILL.md)**: スキルの詳細な実装とワークフロー
- **[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)**: GitHub Actionsの詳細設定
- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)**: 既存プロジェクトへの統合方法
- **[PERMISSIONS_GUIDE.md](./PERMISSIONS_GUIDE.md)**: 必要な権限の詳細
- **[VERTEX_AI_SETUP.md](./VERTEX_AI_SETUP.md)**: Vertex AI統合の設定方法

## 制限事項

- GitHub Actions環境専用（ローカル実行は非対応）
- 大規模PR（500ファイル以上）は処理時間がかかる場合があります
- 言語やフレームワーク固有の高度な分析には限界があります
- AIによる自動分析であり、最終的な判断は人間のレビュアーが行う必要があります

## ライセンス

このスキルはオープンソースプロジェクトとして提供されています。

## サポート

問題や質問がある場合は、リポジトリのIssueを作成してください。

---

**注意**: このスキルはGitHub Actions環境で実行されることを前提としています。`gh`コマンドとGitHub MCPを活用し、Pythonスクリプトを使用しないシンプルな実装になっています。
