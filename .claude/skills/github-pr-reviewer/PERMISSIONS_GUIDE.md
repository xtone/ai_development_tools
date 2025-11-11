# GitHub Actions 権限ガイド

GitHub Actionsで自動PRレビューを実行する際の、API実行権限とユーザー表示について説明します。

## 概要

GitHub Actionsでは、**誰の権限でGitHub APIを実行するか**によって、以下が変わります：

- PRやIssueでの表示名
- 実行可能なアクション
- ワークフローのトリガー可否
- 保護ブランチへのアクセス

## 3つの権限モデル

### 1. GITHUB_TOKEN（標準）

#### 使用するワークフロー
- `.github/workflows/pr-review.yml`

#### 設定方法
```yaml
- uses: anthropics/claude-code-action@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}  # 自動生成される
```

#### 実行権限
- **実行ユーザー**: `github-actions[bot]`
- **権限範囲**: ワークフローの `permissions` セクションで指定
- **セットアップ**: 不要（自動的に利用可能）

#### 表示例
```
github-actions[bot] commented:
## PR Review Summary
...
```

#### メリット
✅ セットアップ不要
✅ シンプル
✅ ほとんどの用途で十分

#### デメリット
❌ 表示名をカスタマイズできない
❌ このトークンで作成したイベントは新しいワークフローをトリガーしない
❌ 一部の保護ブランチルールで制限される可能性

#### 推奨用途
- 個人プロジェクト
- 小規模チーム
- シンプルな自動化

---

### 2. GitHub App Token（推奨）

#### 使用するワークフロー
- `.github/workflows/pr-review-with-github-app.yml`（Anthropic API版）
- `.github/workflows/pr-review-vertex-ai.yml`（Vertex AI版）

#### 設定方法
```yaml
- name: Generate GitHub App token
  id: app-token
  uses: actions/create-github-app-token@v2
  with:
    app-id: ${{ secrets.APP_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}

- uses: anthropics/claude-code-action@v1
  with:
    github_token: ${{ steps.app-token.outputs.token }}
```

#### 実行権限
- **実行ユーザー**: `[GitHub App名][bot]`（例: `MyCompany PR Reviewer[bot]`）
- **権限範囲**: GitHub Appで設定した権限
- **セットアップ**: GitHub Appの作成が必要

#### 表示例
```
MyCompany PR Reviewer[bot] commented:
## PR Review Summary
...
```

#### メリット
✅ 表示名をカスタマイズ可能
✅ 細かい権限管理
✅ 作成したイベントが新しいワークフローをトリガー可能
✅ エンタープライズでの監査ログが明確
✅ 複数リポジトリで同じAppを使用可能

#### デメリット
❌ GitHub Appの作成が必要
❌ セットアップがやや複雑

#### 推奨用途
- エンタープライズ環境
- 複数リポジトリでの運用
- カスタムブランディングが必要な場合
- 高度な権限管理が必要な場合

---

### 3. Personal Access Token（非推奨）

#### 設定方法
```yaml
- uses: anthropics/claude-code-action@v1
  with:
    github_token: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
```

#### 実行権限
- **実行ユーザー**: トークンを生成したユーザー
- **権限範囲**: ユーザーの権限全て
- **セットアップ**: ユーザーのPATを取得

#### 表示例
```
@username commented:
## PR Review Summary
...
```

#### デメリット
❌ 個人アカウントに紐付く（ユーザーが退職したら動作しなくなる）
❌ 過剰な権限を持つ可能性
❌ セキュリティリスク
❌ 監査ログが不明確

#### 推奨しない理由
- **セキュリティリスク**: 個人の全権限が使われる
- **属人化**: ユーザー退職時に動作しなくなる
- **監査の困難さ**: 個人の行動と区別がつかない

**この方法は使用しないことを強く推奨します。**

---

## 比較表

| 項目 | GITHUB_TOKEN | GitHub App | PAT（非推奨） |
|------|--------------|------------|---------------|
| **表示名** | `github-actions[bot]` | カスタマイズ可能 | 個人ユーザー名 |
| **セットアップ** | 不要 | GitHub App作成 | PAT生成 |
| **権限の細かさ** | ワークフロー単位 | App単位で詳細設定 | ユーザー権限全て |
| **ワークフロートリガー** | 制限あり | 可能 | 可能 |
| **保護ブランチ** | 制限される場合あり | App権限に依存 | ユーザー権限に依存 |
| **セキュリティ** | ✅ 良い | ✅ 最良 | ❌ 悪い |
| **監査性** | ✅ 良い | ✅ 最良 | ❌ 悪い |
| **推奨度** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ 非推奨 |

---

## セットアップ手順

### GITHUB_TOKEN（標準）の使用

**手順**: なし（自動的に利用可能）

**ワークフロー**: `.github/workflows/pr-review.yml`

そのまま使用できます。

---

### GitHub App Token の使用

#### 1. GitHub App の作成

1. GitHub の Settings → Developer settings → GitHub Apps → **New GitHub App**

2. **基本情報を入力**:
   - App name: `MyCompany PR Reviewer`（任意の名前）
   - Homepage URL: リポジトリURL
   - Webhook: 無効化（チェックを外す）

3. **権限を設定** (Repository permissions):
   - Contents: `Read and write`
   - Issues: `Read and write`
   - Pull requests: `Read and write`
   - Metadata: `Read-only`（自動設定）

4. **Subscribe to events**: 不要（イベント駆動ではなくワークフロー駆動のため）

5. **Where can this GitHub App be installed?**:
   - `Only on this account`（組織内のみ）

6. **Create GitHub App** をクリック

#### 2. 秘密鍵の生成

1. 作成したGitHub Appの設定ページに移動
2. **Private keys** セクションで **Generate a private key** をクリック
3. `.pem` ファイルがダウンロードされる

#### 3. App ID の確認

GitHub Appの設定ページ上部に表示されている **App ID** をメモ

#### 4. GitHub App のインストール

1. GitHub Appの設定ページで **Install App** を選択
2. 対象のリポジトリまたは組織を選択
3. リポジトリアクセスを設定:
   - **All repositories** または
   - **Only select repositories** → 対象リポジトリを選択

#### 5. GitHub Secrets の設定

リポジトリの Settings → Secrets and variables → Actions:

**`APP_ID`**:
```
12345678  # GitHub AppのApp ID
```

**`APP_PRIVATE_KEY`**:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
（.pemファイルの内容全体をコピー）
...
-----END RSA PRIVATE KEY-----
```

**注意**: 改行も含めて完全にコピーしてください

#### 6. ワークフローファイルの選択

**Anthropic API版**:
```bash
cp .github/workflows/pr-review-with-github-app.yml /path/to/your/repo/.github/workflows/
```

**Vertex AI版**:
```bash
cp .github/workflows/pr-review-vertex-ai.yml /path/to/your/repo/.github/workflows/
```

---

## 権限の確認方法

### GITHUB_TOKEN の権限を確認

ワークフローファイルの `permissions` セクションを確認:

```yaml
permissions:
  contents: write        # コードの読み書き
  pull-requests: write   # PRへのコメント、レビュー
  issues: write          # Issueの作成、編集
```

### GitHub App の権限を確認

1. GitHub Settings → Developer settings → GitHub Apps
2. 対象のGitHub Appを選択
3. **Permissions & events** タブを確認

---

## トラブルシューティング

### レビューコメントが投稿されない

**原因**: 権限不足

**確認事項**:
- GITHUB_TOKEN: `permissions.pull-requests: write` が設定されているか
- GitHub App: Pull requests権限が `Read and write` になっているか

### Issueが作成されない

**原因**: 権限不足

**確認事項**:
- GITHUB_TOKEN: `permissions.issues: write` が設定されているか
- GitHub App: Issues権限が `Read and write` になっているか

### ワークフローが他のワークフローをトリガーしない

**原因**: GITHUB_TOKENの制限

**解決策**: GitHub App Tokenを使用する

### GitHub Appの認証エラー

**エラー**: `Bad credentials`

**確認事項**:
1. `APP_ID` が正しいか
2. `APP_PRIVATE_KEY` に `.pem` ファイルの内容全体が含まれているか
3. `.pem` ファイルの改行が保持されているか
4. GitHub Appがリポジトリにインストールされているか

---

## セキュリティベストプラクティス

### 1. 最小権限の原則

必要な権限のみを付与:

```yaml
permissions:
  contents: write         # 必要
  pull-requests: write    # 必要
  issues: write           # 必要
  # actions: write        # 不要なら削除
  # packages: write       # 不要なら削除
```

### 2. GitHub App の定期的な監査

- 使用していないGitHub Appは削除
- 権限を定期的に見直し
- インストールされているリポジトリを確認

### 3. 秘密鍵の管理

- `.pem` ファイルは安全に保管
- GitHub Secretsで管理（コードにコミットしない）
- 定期的にローテーション（年1回推奨）

### 4. 監査ログの確認

組織の監査ログでGitHub Appの活動を確認:
- Settings → Audit log
- フィルター: `action:integration`

---

## 推奨構成

### 個人・小規模プロジェクト

**使用**: GITHUB_TOKEN
**ワークフロー**: `pr-review.yml`

シンプルで十分な機能を提供します。

### チーム・エンタープライズ

**使用**: GitHub App
**ワークフロー**: `pr-review-with-github-app.yml` または `pr-review-vertex-ai.yml`

以下の理由で推奨:
- カスタムブランディング
- 細かい権限管理
- 明確な監査ログ
- 複数リポジトリでの一元管理

---

## まとめ

| 用途 | 推奨方法 | ワークフロー |
|------|---------|-------------|
| 個人プロジェクト | GITHUB_TOKEN | `pr-review.yml` |
| 小規模チーム | GITHUB_TOKEN | `pr-review.yml` |
| エンタープライズ | GitHub App | `pr-review-with-github-app.yml` |
| Vertex AI使用 | GitHub App | `pr-review-vertex-ai.yml` |

**GitHub App** を使用することで、より柔軟で安全な自動化が実現できます。
