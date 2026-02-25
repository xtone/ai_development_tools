---
name: android-crash-analyzer
description: "Firebase Crashlyticsのスタックトレースを解析し、トリアージ分類→根本原因分析→修正提案を出力するスキル。以下の場合に使用: /crash-analyze、クラッシュ解析、スタックトレース分析、ANR分析、Crashlytics、クラッシュレポート、またはFirebase crashに関連する任意のリクエスト。クラッシュ対応のワークフローを標準化し、対応品質と速度を向上させる。ANR/Non-fatal/Fatal全タイプ対応。"
---

# Android Crash Analyzer

Firebase Crashlyticsのスタックトレースを解析し、トリアージ分類→根本原因分析→修正提案を出力する Claude Code スキルです。

## 目的

クラッシュ対応ワークフローを標準化し、対応品質と速度を向上させる:
- 対処不要なクラッシュを即座に切り分け（MONITOR）
- 修正可能なバグには具体的なコード修正を提案（FIX）
- システム例外には防御的ハンドリングを提案（DEFEND）
- パターンをCLAUDE.mdに蓄積し、同じクラッシュの再分析を防止

## Quick Reference

### トリアージ分類マトリクス

| タイプ | アプリコード | 判定 | アクション |
|--------|------------|------|----------|
| ANR | なし | MONITOR | モニタリング + コードベースのANR原因スキャン |
| ANR | あり | INVESTIGATE | 根本原因分析 + 修正提案 |
| error | なし | MONITOR | SDK動作として記録（対処不要） |
| error | あり | FIX | バグ修正提案 |
| crash | なし | MONITOR | モニタリング |
| crash | あり（アプリ例外） | FIX | バグ修正提案 |
| crash | あり（システム例外） | DEFEND | 防御的try-catch提案 |

### 判定フロー

```
スタックトレース入力
  → タイプ判定（ANR/error/crash）
    → アプリフレーム有無
      → MONITOR / INVESTIGATE / FIX / DEFEND
```

## トリガー

- `/crash-analyze <file_path>` — 指定ファイルのスタックトレースを解析
- `/crash-analyze` — ファイルパス入力を促す
- 「このクラッシュを分析して」「スタックトレースを解析して」等の自然言語

## System Instructions

ユーザーが Firebase Crashlytics のスタックトレース解析をリクエストした場合、以下の手順に従ってください:

### ステップ0: 入力取得・ヘッダー解析

#### ファイルパスが指定されている場合

Read ツールでファイルを読み込む。**大容量ファイル（1000行超）の場合**、最初に先頭100行のみ読み込み、その後 Grep でアプリフレームを抽出する。

#### ペースト入力の場合（ファイルなし）

ユーザーが直接貼り付けたスタックトレースからそのまま解析を開始する。

#### ヘッダー情報の抽出

ファイル先頭7行程度から以下を抽出:

| フィールド | 抽出パターン | 例 |
|-----------|------------|-----|
| パッケージ名 | `Package Name:` の値 | `jp.co.nttdocomo.dmenunews` |
| バージョン | `Version Name:` / `Version Code:` | `2.49.1 (504901100)` |
| Issue Hash | `Issue #` / ファイル名のハッシュ部分 | `abc123def456` |
| 発生日 | `Date:` / タイムスタンプ | `2025-01-15` |

**パッケージ名が不明な場合**: Glob で `**/AndroidManifest.xml` を検索し、`package=` 属性から取得する。フォールバックとして `build.gradle*` の `applicationId` を使用。

### ステップ1: タイプ分類

以下の優先順で判定:

**1. ファイル名パターン（最優先）**:
- `_ANR_` を含む → **ANR**
- `_error_` を含む → **error**（Non-fatal）
- `_crash_` を含む → **crash**（Fatal）

**2. フォールバック（ファイル名なし/ペースト入力）**:
- 本文に `ANR` / `Application Not Responding` → **ANR**
- 本文先頭が `Exception` / `Error` でプロセス終了なし → **error**
- 本文に `FATAL EXCEPTION` / `Process: ... has stopped` → **crash**
- 判定不能 → **unknown**（ユーザーに確認）

### ステップ2: スタックトレース構造解析

ステップ0で取得したパッケージ名を使い、スタックトレース内のアプリフレームを特定:

```
# アプリフレームの検索
パッケージ名（例: jp.co.nttdocomo.dmenunews）を含む行を抽出
```

**判定基準**:
- アプリパッケージ名を含む `at` 行が **1行以上** → アプリコードあり
- アプリパッケージ名を含む行が **0行** → アプリコードなし

**Caused by チェーン**: 複数の `Caused by:` がある場合、**最後の Caused by を根本原因**として扱う。

**ProGuard難読化の検出**: 単一文字のクラス名（`at a.b.c.d(Unknown Source)`）を検出した場合:
```
⚠️ ProGuardで難読化されたスタックトレースです。
mapping.txt を使用してデコードしてから再分析することを推奨します:
$ retrace mapping.txt stacktrace.txt
```

### ステップ3: トリアージ分類

ステップ1のタイプとステップ2のアプリフレーム有無から、Quick Reference のマトリクスに従い判定する。

**crash + アプリコードありの場合の追加判定**:
- 例外クラスがアプリ固有（アプリパッケージ内の例外） → **FIX**
- 例外クラスが `java.lang.*` / `kotlin.*` でアプリコードが直接の原因 → **FIX**
- 例外クラスがシステム/フレームワーク例外（`android.os.*`, `android.app.*` 等）でアプリコードは呼び出し元 → **DEFEND**

**システム例外の例**:
- `android.os.DeadSystemException`
- `android.os.TransactionTooLargeException`
- `android.view.WindowManager$BadTokenException`
- `java.lang.SecurityException`（権限関連）
- `android.os.DeadObjectException`

### ステップ4: 分析

判定結果に応じて分析を実行:

#### MONITOR の場合

理由を簡潔に説明し、モニタリング方針を提示:

```markdown
## クラッシュ分析レポート

**判定**: 🔍 MONITOR
**タイプ**: {ANR/error/crash}
**例外**: {例外クラス名}: {メッセージ}

### 理由
{対処不要と判断した理由}

### モニタリング方針
- 発生頻度が急増した場合に再調査
- 影響バージョン: {version}
- Issue: {hash}
```

#### INVESTIGATE の場合（ANR + アプリコードあり）

ANRのアプリフレームを特定し、メインスレッドブロック箇所を分析:

```markdown
## クラッシュ分析レポート

**判定**: 🔎 INVESTIGATE
**タイプ**: ANR

### メインスレッドブロック箇所
{アプリフレームからの推定箇所}

### コードベース調査
{対象ファイルのRead結果に基づく分析}

### 修正提案
{具体的な修正方法}
```

#### FIX の場合

アプリフレームを特定し、コードベースを検索して修正を提案:

```markdown
## クラッシュ分析レポート

**判定**: 🐛 FIX
**タイプ**: {error/crash}
**例外**: {例外クラス名}: {メッセージ}

### 根本原因
{最後のCaused byチェーンとアプリフレームの分析}

### 対象コード
`{ファイルパス}:{行番号}`

### 修正提案
{修正前/修正後のコード}
```

#### DEFEND の場合

システム例外を特定し、防御的ハンドリングを提案:

```markdown
## クラッシュ分析レポート

**判定**: 🛡️ DEFEND
**タイプ**: crash
**例外**: {システム例外名}: {メッセージ}

### 原因
{システム例外が発生する条件の説明}

### 防御コード提案
{try-catch等の防御的ハンドリングコード}
```

### ステップ5: 修正提案生成

FIX / DEFEND の場合、以下を実行:

1. ステップ4で特定したアプリフレームのファイルパスを Grep/Glob で検索
2. 対象ソースファイルを Read
3. 修正前/修正後のコードを提示

```markdown
### 修正前
```kotlin
// {file_path}:{line}
{現在のコード}
```

### 修正後
```kotlin
// {file_path}:{line}
{修正後のコード}
```

### 修正理由
{なぜこの修正が必要か}
```

### ステップ5a: ANRプロアクティブスキャン

ANR + アプリコードなし（MONITOR判定）の場合、コードベースを自動スキャンしてANR原因となりうるパターンを検出:

| パターン | 検索対象 | 推奨修正 |
|---------|---------|---------|
| メインスレッドでのネットワーク | `URL(...).openStream()` / `openConnection()` タイムアウト未設定 | OkHttp + タイムアウト設定 |
| 同期SharedPreferences | `SharedPreferences.commit()` | `apply()` に変更 |
| メインスレッドブロック | `runBlocking`（非テストコード） | `launch` / `async` に変更 |
| 大容量画像デコード | `BitmapFactory.decode*`（Dispatchers.IO外） | `withContext(Dispatchers.IO)` |
| 同期ContentResolver | `contentResolver.query/insert/update/delete`（コルーチン外） | `withContext(Dispatchers.IO)` |

Grep で各パターンを検索し、検出結果があれば報告:

```markdown
### ANRプロアクティブスキャン結果

コードベースをスキャンし、ANRの潜在的原因を検出しました:

| 箇所 | パターン | リスク |
|------|---------|------|
| `{file}:{line}` | {パターン名} | {説明} |
```

### ステップ6: パターン蓄積（オプション）

分析完了後、ユーザーに確認の上、CLAUDE.md の `## Crash Patterns` セクションに追記する。

#### 蓄積フォーマット

```markdown
## Crash Patterns

このセクションはクラッシュ分析パターンから自動生成されました。
`/crash-analyze` コマンドで更新できます。

### 非アクション対象
- `{例外名}: {メッセージ}` は{理由}。アクション不要
  - 📊 Issue {hash} (v{version}) — {date}

### バグ修正
- `{例外名}: {メッセージ}` — {根本原因の要約}
  - 🐛 Issue {hash} (v{version}) — {date}

### 防御的ハンドリング
- `{例外名}` — {条件}にtry-catch必要
  - 🛡️ Issue {hash} (v{version}) — {date}
```

#### セクションの配置

- `## Crash Patterns` セクションがあればそこに追記
- なければ `## CI Learnings` の後に作成
- どちらもなければ CLAUDE.md 末尾に新規作成

#### 重複チェック

追記前に既存の `## Crash Patterns` セクションを確認し、同一 Issue hash または同一例外パターンが既に記録されている場合はスキップ。

## エラーハンドリング

**エラー1: ファイルが見つからない**
```
指定されたファイルが見つかりません: {file_path}
パスを確認してください。
```

**エラー2: スタックトレースではないファイル**
```
このファイルはスタックトレースではないようです。
Firebase Crashlyticsからエクスポートした .txt ファイルを指定してください。
```

**エラー3: パッケージ名が特定できない**
```
アプリのパッケージ名を特定できませんでした。
AndroidManifest.xml が見つかりません。パッケージ名を教えてください。
```

**エラー4: ProGuard難読化**
```
⚠️ ProGuardで難読化されたスタックトレースです。
mapping.txt を使用してデコードしてから再分析することを推奨します:
$ retrace mapping.txt stacktrace.txt
```

## 重要事項

- CLAUDE.mdはプロジェクト全体で共有されるファイル。慎重に編集すること
- 既存の内容は変更しない（追記のみ）
- Issue hash とバージョンを必ず残す（追跡可能性）
- 追記・変更は必ずユーザーの承認を得てから実行する
- 大容量ANRファイル（1000行超）は全文Readせずヘッダー + Grepで処理
- Caused by チェーンは最後のものを根本原因として扱う
- ProGuard難読化を検出した場合は mapping.txt 使用を案内

## 互換性

### Agent Skills (Open Standard)

このスキルは [Agent Skills](https://agentskills.io) オープンスタンダードに準拠しています。

**対応ツール**:
- Claude Code
- GitHub Copilot
- VS Code
- Cursor (Nightly)
- OpenAI Codex

`.claude/skills/` ディレクトリに配置することで、上記すべてのツールで使用可能です。

## バージョン

### v1.0 - 初回リリース (2026-02-25)
- トリアージ分類マトリクス（MONITOR/INVESTIGATE/FIX/DEFEND）
- ANR/Non-fatal/Fatal 全タイプ対応
- ANRプロアクティブスキャン（5パターン）
- Caused by チェーン解析
- ProGuard難読化検出
- 大容量ファイル対応（1000行超）
- CLAUDE.md Crash Patterns 蓄積機能
- すべての説明を日本語で記述
