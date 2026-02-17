---
name: ci-learn
description: "CI/GitHub Actionsの失敗パターンをCLAUDE.mdに蓄積するスキル。`/ci-learn` で直近の失敗runから学び、`/ci-learn #run_id` で指定runを分析。同じCI失敗を繰り返さないコードベースを実現する。"
---

# CI Learner

CI/GitHub Actionsの失敗パターンをCLAUDE.mdに蓄積するスキル。同じCI失敗を繰り返さないコードベースを実現する。

## 目的

学習トライアドの第3の柱として、CI/CDパイプラインの失敗から体系的に学ぶ:
- CI失敗パターンをCLAUDE.mdに自動蓄積
- 同じビルドエラー・テスト失敗を繰り返すことを防止
- 「ローカルでは通るがCIで落ちる」問題の知見を共有

## 学習トライアド

| スキル | 学びの源泉 | タイミング |
|--------|-----------|-----------|
| `/lessons` | 自分で気づいた失敗・修正 | セッション終了時 |
| `/review-learn` | 他者からの指摘 | PRマージ後 |
| `/ci-learn` | CI/CDの失敗パターン | CI失敗発生後 |

3つを組み合わせることで、**個人の気づき＋チームの知見＋システムのフィードバック**が蓄積される。

## トリガー

- `/ci-learn` — 直近の失敗 CI run から学ぶ
- `/ci-learn #run_id` — 指定 run ID から学ぶ
- `/ci-learn --recent` — 直近5件の失敗 run を分析
- 「CIの失敗から学んで」「ビルドエラーをまとめて」等の自然言語

## System Instructions

### ステップ1: 対象 CI Run の特定

#### 引数がある場合（run ID 指定）

```bash
# 指定 run の詳細を取得
gh run view {run_id} --json databaseId,displayTitle,conclusion,headBranch,createdAt,event,url
```

#### 引数がない場合（直近の失敗 run）

```bash
# 直近の失敗 run を取得
gh run list --status failure --limit 5 --json databaseId,displayTitle,conclusion,headBranch,createdAt,event,workflowName
```

ユーザーに対象 run を確認する:
```
直近の失敗 CI Run:
1. #12345 - Build and Test (main) — 2時間前
2. #12340 - Deploy Staging (feature/auth) — 1日前
3. #12335 - Lint Check (fix/typo) — 2日前

どの run から学びますか？（番号 or 全て）
```

#### `--recent` フラグの場合

直近5件の失敗 run を全て分析対象にする。

### ステップ2: 失敗ログの取得

```bash
# 失敗ステップのログのみ取得
gh run view {run_id} --log-failed

# run の詳細（jobs, steps）を取得
gh run view {run_id} --json jobs
```

取得データの用途:
- `--log-failed`: エラーメッセージ・スタックトレースの抽出
- `jobs[].steps[]`: どのステップで失敗したかの特定（name, conclusion）
- `headBranch`: 失敗したブランチ（PR関連か判別）
- `event`: トリガー種別（push, pull_request, workflow_dispatch）

### ステップ3: 失敗パターンの分類

失敗ログを以下のカテゴリに分類:

| カテゴリ | 判定基準 | 例 |
|---------|---------|-----|
| ビルド | コンパイルエラー、依存関係解決失敗 | 「Gradle 8.x では kotlin.jvm.target を明示」 |
| テスト | テスト失敗、タイムアウト | 「@Test アノテーション忘れ」 |
| リント・フォーマット | lint/ktlint/detekt エラー | 「import の順序ルール」 |
| 環境・設定 | Node/Java バージョン不一致、secrets 不足 | 「JAVA_HOME の設定」 |
| デプロイ | リリース、アーティファクト関連 | 「artifact actions v4 への移行」 |
| 権限・認証 | token 期限切れ、権限不足 | 「GITHUB_TOKEN のスコープ」 |
| タイムアウト | ジョブ/ステップのタイムアウト | 「E2Eテストの timeout 設定」 |

### ステップ4: ルール化可能なパターンの抽出

以下の基準で「ルール化すべきパターン」を抽出:

**抽出対象**:
- 繰り返し発生しうるパターン（設定ミス、バージョン不整合）
- プロジェクト固有の CI 設定知見
- 「ローカルでは通るが CI で落ちる」系の問題

**除外対象**:
- 一時的なインフラ障害（GitHub Actions 側の問題）
- flaky テスト（再実行で成功するもの）
- 外部サービスの一時的なダウン
- 既に修正済みで再発しない問題（ログから明確に判別可能な場合）

### ステップ5: 既存ルールとの重複チェック

1. CLAUDE.md を読み込む
2. 既存の `## Lessons Learned` と `## CI Learnings` セクションを確認
3. 意味的に重複するパターンは除外
4. 既存ルールを補強・具体化するパターンは更新案として提示

### ステップ6: ルール案の生成

以下のフォーマットでルール案を生成:

```markdown
### {カテゴリ名}
- {具体的なルール}。{理由や背景}
  - 🔧 CI Run #{run_id} ({workflow名}) — {日付}
```

**記述の品質基準**（lessons-md-manager と同一）:
- 肯定形で記述（「〜しないこと」より「〜を使うこと」）
- 具体的なコード例やパターンを含める
- なぜそうすべきかの理由を添える
- 元の CI Run をクレジット

**良い例**:
```markdown
### ビルド
- Gradle 8.x では `kotlin.jvm.target` を明示的に設定する。未設定だとCIのJDKバージョンとローカルで異なりビルドが失敗する
  - 🔧 CI Run #12345 (Build and Test) — 2026-02-15

### テスト
- CI環境ではテストのタイムアウトをローカルの2倍に設定する。GitHub Actions のランナーはローカルマシンより低速なため
  - 🔧 CI Run #12340 (Unit Tests) — 2026-02-14
```

### ステップ7: ユーザー確認

失敗パターンをカテゴリ別にグループ化して提示:

```markdown
## CI 失敗パターン分析結果

### 分析対象
- Run #12345: Build and Test (main) — failure

### 蓄積候補

#### ビルド
1. Gradle 8.x で kotlin.jvm.target 未設定 → 明示的に設定する
   - 🔧 CI Run #12345 — 2026-02-15
   → ルール案: 「Gradle 8.x では `kotlin.jvm.target` を明示的に設定する」

#### テスト
1. CI環境でのタイムアウト → タイムアウト値を2倍に設定
   - 🔧 CI Run #12340 — 2026-02-14
   → ルール案: 「CI環境ではテストのタイムアウトをローカルの2倍に設定する」

---
除外したパターン: 一時障害 1件 / flaky 2件
```

ユーザーの承認を得てからステップ8に進む。

### ステップ8: CLAUDE.md への書き込み

追記先: `## CI Learnings` セクション

```markdown
## CI Learnings

このセクションはCI/GitHub Actionsの失敗パターンから自動生成されました。
`/ci-learn` コマンドで更新できます。

### ビルド
- Gradle 8.x では `kotlin.jvm.target` を明示的に設定する。未設定だとCIのJDKバージョンとローカルで異なりビルドが失敗する
  - 🔧 CI Run #12345 (Build and Test) — 2026-02-15

### テスト
- CI環境ではテストのタイムアウトをローカルの2倍に設定する。GitHub Actions のランナーはローカルマシンより低速なため
  - 🔧 CI Run #12340 (Unit Tests) — 2026-02-14
```

セクションの配置:
- `## CI Learnings` セクションがあればそこに追記
- なければ `## Lessons Learned` の後に作成
- どちらもなければCLAUDE.md末尾に新規作成

## エラーハンドリング

**エラー1: GitHubリポジトリではない**
- gitルートを確認し、GitHub remoteがあるかチェック
- ない場合はエラーメッセージを表示

**エラー2: gh CLIが未認証**
```
GitHub CLIが認証されていません。
以下のコマンドで認証してください:
$ gh auth login
```

**エラー3: 失敗した CI run がない**
```
直近に失敗した CI run がありません。
すべてのワークフローが正常に完了しています。
```

**エラー4: ログが取得できない（90日超過）**
```
CI Run #{run_id} のログは保存期間（90日）を超えているため取得できません。
より新しい run を指定してください。
```

**エラー5: GitHub Actions を使用していない**
```
このリポジトリには GitHub Actions ワークフローがありません。
.github/workflows/ ディレクトリにワークフローファイルを追加してください。
```

## 重要事項

- CLAUDE.mdはプロジェクト全体で共有されるファイル。慎重に編集すること
- 既存の内容は変更しない（追記のみ）
- CI Run のIDとワークフロー名を必ず残す（追跡可能性）
- 追記・変更は必ずユーザーの承認を得てから実行する
- プラットフォーム非依存: あらゆるGitHubリポジトリで使用可能
- 一時的な障害やflakyテストはルール化しない

## バージョン

### v1.0 - 初回リリース (2026-02-17)
- CI失敗ログからパターンを抽出
- 7カテゴリ自動分類（ビルド/テスト/リント/環境/デプロイ/権限/タイムアウト）
- 既存ルールとの重複チェック
- CI Runクレジット付きでCLAUDE.mdに追記
- 学習トライアド（lessons/review-learn/ci-learn）の完成
