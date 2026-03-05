# CI環境でのコスト最適化ワークフロー

Opus単体で全ステップを実行する構成から、**Haiku（トリアージ）+ Opus（深層レビュー）の2ジョブ構成**に変更することで、トークン使用量を大幅に削減する。

---

## 1. 最適化の概要

### 従来構成（Opus単体）

```
[Opus] PR情報取得 → ファイル分類 → リファレンス全読み → 全チェック → 判定 → 投稿
       ~40ターン、リファレンス全読み込み
```

### 最適化構成（Haiku + Opus）

```
[Haiku] PR情報取得 → ファイル分類 → 表層チェック → .pr-triage.json出力
        ~10ターン

[Opus]  トリアージ読み込み → 必要なリファレンスのみ読み → Critical/Major集中 → 判定 → 投稿
        ~20ターン、リファレンス選択的読み込み
```

### 期待されるコスト削減効果

| 項目 | 従来 | 最適化後 | 削減率 |
|------|------|---------|--------|
| Opusターン数 | ~40 | ~20 | 50% |
| Opusトークン入力（リファレンス） | 全ファイル（~500行） | 必要分のみ（~100-200行） | 60-80% |
| Haikuコスト追加 | - | ~10ターン | （Opusの1/10以下） |
| **合計コスト** | **100%** | **約40-50%** | **50-60%** |

> Haikuの料金はOpusの約1/50（入力）〜1/100（出力）のため、Haikuフェーズの追加コストは無視できるレベル。

---

## 2. GitHub Actionsワークフロー設定例

### 完全な設定例（Vertex AI経由）

```yaml
name: Automated PR Review (Optimized)

on:
  pull_request:
    types: [opened, synchronize, reopened]
    paths-ignore:
      - '.claude/skills/**'
      - '*.md'
      - 'LICENSE'

permissions:
  contents: read
  pull-requests: write
  issues: write
  id-token: write  # Vertex AI Workload Identity Federation用

concurrency:
  group: pr-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  # ==========================================================
  # Phase 1: トリアージ（Haiku - 軽量・高速・低コスト）
  # ==========================================================
  triage:
    if: github.actor != 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}

      - name: Run Triage with Haiku
        uses: anthropics/claude-code-action@v1
        env:
          ANTHROPIC_VERTEX_PROJECT_ID: ${{ steps.auth.outputs.project_id }}
          CLOUD_ML_REGION: global
        with:
          github_token: ${{ steps.app-token.outputs.token }}
          use_vertex: "true"
          prompt: |
            PR #${{ github.event.pull_request.number }} のトリアージを実行してください。

            ## 手順

            1. `gh pr view ${{ github.event.pull_request.number }} --json title,body,headRefName,baseRefName` でPR情報を取得
            2. `gh pr diff ${{ github.event.pull_request.number }} --name-only` で変更ファイル一覧を取得
            3. `gh pr diff ${{ github.event.pull_request.number }}` でコード差分を取得
            4. 以下の分析を行う：
               - 変更ファイルのカテゴリ分類（added/modified/deleted）
               - 使用言語・フレームワークの検出
               - 変更カテゴリの判定（認可変更、DB変更、RLS変更、API変更、テスト変更、設定変更）
               - 必要なリファレンスファイルの判定
               - Minor/Suggestionレベルの表層的問題の検出
               - 差分の要約（200文字以内）
               - レビュー時に注目すべきポイント

            5. 分析結果を `.pr-triage.json` ファイルに出力する

            ## 必要なリファレンスの判定基準

            以下の条件に該当する場合のみ、対応するリファレンスを `required_references` に含める：
            - TypeScript/JavaScript ファイルの変更あり → `typescript-best-practices.md`
            - 認証・認可に関わるコード変更あり（auth, permission, role, session, token等のキーワード） → `authorization-review-general.md`
            - PostgreSQL RLS に関わる変更あり（RLS, row level security, policy等のキーワード） → `authorization-review-postgres-rls.md`
            - CI環境でのGitHub投稿が必要 → `github-pr-review-actions.md`（常に含める）

            ## 表層チェック項目（Minor/Suggestion）

            差分を確認し、以下の問題を検出する（該当するもののみ）：
            - `any` 型の使用（TypeScript）
            - `var` キーワードの使用（TypeScript/JavaScript）
            - 空のインターフェイス定義
            - マジックナンバーの使用
            - 命名規則違反（camelCase/PascalCase/UPPER_CASE）
            - テストの未追加（新規ファイルがあるのにテストファイルがない）

            ## 出力フォーマット

            `.pr-triage.json` に以下のJSON構造で出力すること：

            ```json
            {
              "pr_number": <PR番号>,
              "summary": "<変更の概要（1-2文）>",
              "files": {
                "added": ["<追加ファイルパス>"],
                "modified": ["<変更ファイルパス>"],
                "deleted": ["<削除ファイルパス>"]
              },
              "languages": ["<検出された言語>"],
              "frameworks": ["<検出されたフレームワーク>"],
              "change_categories": {
                "has_auth_changes": <true/false>,
                "has_db_changes": <true/false>,
                "has_rls_changes": <true/false>,
                "has_api_changes": <true/false>,
                "has_test_changes": <true/false>,
                "has_config_changes": <true/false>
              },
              "required_references": ["<必要なリファレンスファイル名>"],
              "surface_issues": [
                {
                  "severity": "Minor|Suggestion",
                  "file": "<ファイルパス>",
                  "line": <行番号>,
                  "issue": "<問題の説明>",
                  "suggestion": "<改善案>"
                }
              ],
              "diff_summary": "<差分の要約（200文字以内）>",
              "estimated_complexity": "low|medium|high",
              "focus_areas": ["<レビュー時の注目ポイント>"]
            }
            ```

            重要: テキスト出力は最小限にし、`.pr-triage.json` の出力に集中してください。
          claude_args: |
            --model claude-haiku-4-5-20251001
            --max-turns 10
            --allowedTools "Read,Glob,Grep,Bash(gh:*),Write"

      - name: Upload triage results
        uses: actions/upload-artifact@v4
        with:
          name: pr-triage
          path: .pr-triage.json
          retention-days: 1

  # ==========================================================
  # Phase 2: 深層レビュー（Opus - 高精度・Critical/Major集中）
  # ==========================================================
  review:
    needs: triage
    if: github.actor != 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Download triage results
        uses: actions/download-artifact@v4
        with:
          name: pr-triage
          path: .

      - name: Authenticate to Google Cloud
        id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}

      - name: Install vercel-react-best-practices skill
        run: npx -y skills add vercel-labs/agent-skills --skill vercel-react-best-practices --agent claude-code --yes

      - name: Run Claude Code PR Review via Vertex AI
        uses: anthropics/claude-code-action@v1
        env:
          ANTHROPIC_VERTEX_PROJECT_ID: ${{ steps.auth.outputs.project_id }}
          CLOUD_ML_REGION: global

          CLAUDE_CODE_ENABLE_TELEMETRY: "1"
          OTEL_METRICS_EXPORTER: "otlp"
          OTEL_LOGS_EXPORTER: "otlp"
          OTEL_EXPORTER_OTLP_PROTOCOL: "http/protobuf"
          OTEL_EXPORTER_OTLP_ENDPOINT: ${{ secrets.GRAFANA_OTLP_ENDPOINT }}
          OTEL_EXPORTER_OTLP_HEADERS: "Authorization=Basic ${{ secrets.GRAFANA_OTLP_TOKEN }}"
          OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE: "cumulative"
          OTEL_METRIC_EXPORT_INTERVAL: "30000"
          OTEL_LOGS_EXPORT_INTERVAL: "5000"
          OTEL_RESOURCE_ATTRIBUTES: "github.repository=${{ github.repository }},github.repository_owner=${{ github.repository_owner }},github.actor=${{ github.actor }},github.event_name=${{ github.event_name }},deployment.environment=production"
        with:
          github_token: ${{ steps.app-token.outputs.token }}
          use_vertex: "true"
          show_full_output: "true"
          prompt: |
            PR #${{ github.event.pull_request.number }} をコードレビューしてください。

            重要: まず `.pr-triage.json` ファイルを読み込んでください。トリアージフェーズの分析結果が含まれています。
            このファイルの内容に基づき、必要なリファレンスのみを読み込み、Critical/Majorレベルの問題に集中してレビューを行ってください。

            レビュー完了後、必ず以下の2つのアクションをGitHub上で実行してください。
            1. 問題のあるコード行にインラインコメントを投稿する（mcp__github_inline_comment__create_inline_comment または gh api を使用）
            2. `gh pr review` コマンドでレビュー結果（approve/request-changes）を投稿する

            テキスト出力のみで終了せず、必ずGitHub上にレビューを投稿してください。

            /code-review
          claude_args: |
            --model claude-opus-4-6@default
            --max-turns 25
            --allowedTools "Skill,Read,Glob,Grep,WebSearch,mcp__github_inline_comment__create_inline_comment,Bash(gh:*)"
```

---

## 3. Haiku使用時の注意点

### Vertex AIでのHaikuモデルID

Vertex AI経由でHaikuを使用する場合、モデルIDは環境によって異なる場合がある。
使用可能なモデルIDを事前に確認すること：

```bash
# 利用可能なモデル一覧の確認（gcloud CLI）
gcloud ai models list --region=global --filter="displayName:claude"
```

一般的なVertex AIのモデルID：
- `claude-haiku-4-5-20251001` (Claude 4.5 Haiku)
- `claude-opus-4-6@default` (Claude Opus 4.6)

### トリアージ失敗時のフォールバック

トリアージジョブが失敗した場合、レビュージョブはスキップされる。
必要に応じて、トリアージなしでOpus単体レビューを行うフォールバックジョブを追加できる：

```yaml
  review-fallback:
    needs: triage
    if: failure() && github.actor != 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      # トリアージなしでOpus単体レビュー（従来構成と同じ）
      # ...
```

---

## 4. 段階的な導入

### Step 1: まず効果を測定

既存のワークフローと並行して最適化版を実行し、以下を比較する：
- トークン使用量（OTel メトリクス）
- レビュー品質（検出された問題の差分）
- 実行時間

### Step 2: チューニング

実測結果に基づき以下を調整：
- Haikuの `max-turns`（デフォルト10、必要に応じて増減）
- Opusの `max-turns`（デフォルト25、トリアージ品質次第で削減可能）
- トリアージプロンプトの表層チェック項目

### Step 3: 本番切り替え

品質に問題がなければ、最適化版に完全移行する。
