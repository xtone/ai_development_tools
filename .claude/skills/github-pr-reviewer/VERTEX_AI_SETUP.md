# Vertex AI セットアップガイド

Google Cloud の Vertex AI を使用して Claude Code による自動PRレビューを実行するためのセットアップ手順です。

## 前提条件

- Google Cloud Platform (GCP) アカウント
- GCPプロジェクトの作成と課金の有効化
- GitHubリポジトリへの管理者権限
- GitHub App の作成（推奨）

## Vertex AI を使用するメリット

- **エンタープライズ対応**: Google Cloudのエンタープライズサポート
- **データレジデンシー**: データの保存場所を管理可能
- **統合課金**: Google Cloudの一元的な課金管理
- **セキュリティ**: Workload Identity Federationによる安全な認証
- **コンプライアンス**: 企業のコンプライアンス要件への対応

## セットアップ手順

### 1. Google Cloud の設定

#### 1.1 Vertex AI API の有効化

```bash
# Google Cloud CLIを使用する場合
gcloud services enable aiplatform.googleapis.com

# またはGCP Console: APIs & Services → Enable APIs and Services → Vertex AI API
```

#### 1.2 サービスアカウントの作成

```bash
# サービスアカウント作成
gcloud iam service-accounts create github-actions-claude \
  --display-name="GitHub Actions Claude Code" \
  --description="Service account for Claude Code GitHub Actions"

# プロジェクトIDを環境変数に設定
export PROJECT_ID="your-gcp-project-id"
export SA_EMAIL="github-actions-claude@${PROJECT_ID}.iam.gserviceaccount.com"
```

#### 1.3 サービスアカウントへの権限付与

```bash
# Vertex AI ユーザー権限を付与
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"

# 必要に応じて追加の権限を付与
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/logging.logWriter"
```

### 2. Workload Identity Federation の設定

#### 2.1 Workload Identity Pool の作成

```bash
# Workload Identity Pool作成
gcloud iam workload-identity-pools create "github-actions-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Pool ID を取得
export WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe "github-actions-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --format="value(name)")
```

#### 2.2 Workload Identity Provider の作成

```bash
# GitHubリポジトリ情報を環境変数に設定
export GITHUB_ORG="your-github-org"
export GITHUB_REPO="your-repo-name"

# Workload Identity Provider作成
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Provider の完全なリソース名を取得
export WORKLOAD_IDENTITY_PROVIDER=$(gcloud iam workload-identity-pools providers describe "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --format="value(name)")

echo "Workload Identity Provider: ${WORKLOAD_IDENTITY_PROVIDER}"
```

#### 2.3 サービスアカウントへのバインディング

```bash
# 特定のリポジトリからのアクセスを許可
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"
```

### 3. GitHub App の設定（推奨）

GitHub App を使用することで、より細かい権限管理が可能になります。

#### 3.1 GitHub App の作成

1. GitHub Settings → Developer settings → GitHub Apps → New GitHub App
2. 以下の権限を設定：
   - **Repository permissions:**
     - Contents: Read & Write
     - Issues: Read & Write
     - Pull requests: Read & Write
   - **Subscribe to events:**
     - Pull request
     - Issue comment

#### 3.2 秘密鍵の生成

1. 作成したGitHub Appの設定ページに移動
2. "Generate a private key" をクリック
3. ダウンロードされた `.pem` ファイルを保存

#### 3.3 GitHub App のインストール

1. GitHub Appの設定ページで "Install App" を選択
2. レビュー対象のリポジトリにインストール

### 4. GitHub Secrets の設定

GitHubリポジトリの Settings → Secrets and variables → Actions で以下のシークレットを追加：

#### 必須シークレット

1. **`GCP_WORKLOAD_IDENTITY_PROVIDER`**
   - 値: 手順2.2で取得した `WORKLOAD_IDENTITY_PROVIDER` の値
   - 例: `projects/123456789/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider`

2. **`GCP_SERVICE_ACCOUNT`**
   - 値: 作成したサービスアカウントのメールアドレス
   - 例: `github-actions-claude@your-project-id.iam.gserviceaccount.com`

3. **`APP_ID`**
   - 値: GitHub App ID（GitHub Appの設定ページで確認）

4. **`APP_PRIVATE_KEY`**
   - 値: ダウンロードした `.pem` ファイルの内容全体をコピー
   - 注意: `-----BEGIN RSA PRIVATE KEY-----` から `-----END RSA PRIVATE KEY-----` まで全て含める

### 5. ワークフローファイルの配置

Vertex AI用のワークフローファイルをリポジトリに配置：

```bash
# このスキルディレクトリから対象のリポジトリにコピー
cp .github/workflows/pr-review-vertex-ai.yml /path/to/your/repository/.github/workflows/

cd /path/to/your/repository
git add .github/workflows/pr-review-vertex-ai.yml
git commit -m "Add Vertex AI automated PR review workflow"
git push
```

### 6. CLAUDE.md の配置（オプションだが推奨）

```bash
cp CLAUDE.md /path/to/your/repository/
cd /path/to/your/repository
git add CLAUDE.md
git commit -m "Add Claude Code review configuration"
git push
```

## 動作確認

### テストPRの作成

1. リポジトリで新しいブランチを作成
2. コードの変更をコミット
3. Pull Requestを作成

### ワークフロー実行の確認

1. PRページの "Checks" タブを開く
2. "Automated PR Review (Vertex AI)" の実行状況を確認
3. 完了後、PRにレビューコメントが投稿されることを確認

### ログの確認

```bash
# Google Cloud でログを確認
gcloud logging read "resource.type=aiplatform.googleapis.com/Endpoint" \
  --project="${PROJECT_ID}" \
  --limit=50 \
  --format=json
```

## トラブルシューティング

### 認証エラー

**エラー**: `Error: google-github-actions/auth failed with: retry function failed`

**原因**: Workload Identity Federationの設定が不完全

**解決策**:
1. Workload Identity Provider のリソース名を確認
2. サービスアカウントのバインディングを確認
3. GitHub Secrets の値を再確認

```bash
# バインディングの確認
gcloud iam service-accounts get-iam-policy ${SA_EMAIL} \
  --project="${PROJECT_ID}"
```

### 権限エラー

**エラー**: `Permission denied on Vertex AI`

**原因**: サービスアカウントに必要な権限がない

**解決策**:
```bash
# 権限を再度付与
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"
```

### モデルアクセスエラー

**エラー**: `Model not found or access denied`

**原因**: Vertex AI でClaudeモデルへのアクセスが有効化されていない

**解決策**:
1. Google Cloud Console → Vertex AI → Model Garden に移動
2. Claude モデルを検索してアクセスを有効化
3. 利用規約に同意

### GitHub App認証エラー

**エラー**: `Bad credentials`

**原因**: GitHub App IDまたは秘密鍵が正しくない

**解決策**:
1. `APP_ID` がGitHub Appの正しいIDか確認
2. `APP_PRIVATE_KEY` に `.pem` ファイルの内容全体が含まれているか確認
3. 秘密鍵の改行が保持されているか確認

## コスト管理

### 料金の確認

Vertex AI の Claude API 使用料金:
- モデル: Claude Sonnet 4.5
- 料金体系: Google Cloud の Vertex AI 料金ページを参照

```bash
# 使用状況の確認
gcloud billing accounts list
gcloud billing projects describe ${PROJECT_ID}
```

### 予算アラートの設定

```bash
# 予算アラートの作成（例: 月額$100）
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Claude Code Monthly Budget" \
  --budget-amount=100USD
```

### コスト削減のヒント

1. **ターン数の制限**: `--max-turns` を適切に設定
2. **トリガーの制限**: ドラフトPRやWIPを除外
3. **ファイルサイズの制限**: 大規模ファイルを除外
4. **手動トリガー**: 自動実行ではなく、コメントによるトリガーを使用

## セキュリティベストプラクティス

### サービスアカウントの最小権限

必要最低限の権限のみを付与：
```bash
# 不要な権限は削除
gcloud projects remove-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/editor"  # 広すぎる権限は削除
```

### シークレットのローテーション

定期的にGitHub App の秘密鍵をローテーション：
1. 新しい秘密鍵を生成
2. GitHub Secrets を更新
3. 古い秘密鍵を削除

### 監査ログの有効化

```bash
# 監査ログの設定
gcloud logging sinks create claude-audit-logs \
  storage.googleapis.com/BUCKET_NAME \
  --log-filter='resource.type="aiplatform.googleapis.com/Endpoint"'
```

## カスタマイズ

### 特定のGCPリージョンを使用

ワークフローファイルで環境変数を設定：
```yaml
env:
  CLOUD_ML_REGION: us-central1
```

### 異なるClaudeモデルを使用

```yaml
claude_args: |
  --model claude-opus-4-0@20250805
  --max-turns 10
```

## 参考リンク

- [Claude Code GitHub Actions ドキュメント](https://docs.anthropic.com/en/docs/claude-code/github-actions)
- [Google Cloud Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Vertex AI ドキュメント](https://cloud.google.com/vertex-ai/docs)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

## サポート

問題が発生した場合：
1. GitHub Actions のログを確認
2. Google Cloud のログを確認（`gcloud logging read`）
3. このリポジトリのIssueを作成
