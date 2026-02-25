# Android Crash Analyzer

Firebase Crashlyticsのスタックトレースを解析し、トリアージ分類→根本原因分析→修正提案を出力する Claude Code スキルです。

**Version**: v1.0 (2026-02-25)

---

## 機能

- **即座のトリアージ分類**: MONITOR / INVESTIGATE / FIX / DEFEND の4段階で対応要否を判定
- **全タイプ対応**: ANR、Non-fatal（error）、Fatal（crash）すべてのクラッシュタイプを解析
- **コードベース照合**: スタックトレースのアプリフレームからソースコードを特定し、修正を提案
- **ANRプロアクティブスキャン**: ANR原因となりうるコードパターンを自動検出
- **パターン蓄積**: 分析結果をCLAUDE.mdに蓄積し、同じクラッシュの再分析を防止
- **大容量ファイル対応**: 1000行超のANRファイルも効率的に処理

---

## インストール

### Claude Code での使用

1. このスキルをプロジェクトにコピー:
   ```bash
   cp -r android-crash-analyzer /path/to/your-project/.claude/skills/
   ```

2. またはパーソナルスキルディレクトリにリンク:
   ```bash
   ln -s /path/to/android-crash-analyzer ~/.claude/skills/android-crash-analyzer
   ```

3. Claude Code を再起動（既に実行中の場合）

---

## 使い方

### 基本的な使い方

```
/crash-analyze path/to/stacktrace.txt
```

自然言語でもリクエスト可能:

```
このクラッシュレポートを分析して: path/to/crash_report.txt
```

```
スタックトレースを貼り付けたので解析して
```

### ワークフロー

スキルは自動的に以下を実行します:

1. **入力取得** — ファイル読み込み + ヘッダーからメタデータ抽出
2. **タイプ分類** — ANR / error / crash を判定
3. **構造解析** — アプリフレームの有無を判定
4. **トリアージ** — MONITOR / INVESTIGATE / FIX / DEFEND に分類
5. **分析** — 判定に応じた詳細分析を実行
6. **修正提案** — FIX/DEFENDの場合、具体的なコード修正を提示
7. **パターン蓄積** — ユーザー確認の上、CLAUDE.mdに追記

---

## トリアージ分類

| 判定 | 意味 | アクション |
|------|------|----------|
| MONITOR | 対処不要 | 発生頻度をモニタリング |
| INVESTIGATE | 調査必要 | ANRの根本原因を調査 |
| FIX | バグ修正 | 具体的なコード修正を提案 |
| DEFEND | 防御的対応 | try-catch等の防御コードを提案 |

---

## 対応パターン

### クラッシュタイプ
- **ANR** (Application Not Responding) — メインスレッドブロック
- **error** (Non-fatal) — SDK例外、アプリ例外
- **crash** (Fatal) — アプリ例外、システム例外

### ANRプロアクティブスキャン
- メインスレッドでのネットワーク呼び出し
- `SharedPreferences.commit()` の使用
- 非テストコードでの `runBlocking`
- Dispatchers.IO外での大容量画像デコード
- コルーチン外での同期ContentResolver呼び出し

### エッジケース対応
- 大容量ANRファイル（1000行超）の効率的処理
- ProGuard難読化の検出と案内
- ペースト入力（ファイルなし）での解析
- Caused byチェーンの根本原因追跡

---

## 設定

### 前提条件

- Firebase Crashlyticsからエクスポートしたスタックトレース（.txt）
- Androidプロジェクトのコードベース（修正提案を得る場合）
- Claude Code がインストール済み

### CLAUDE.md 連携

分析結果は `## Crash Patterns` セクションに蓄積されます:

```markdown
## Crash Patterns

### 非アクション対象
- `ALXSdkException: NoAd` は広告在庫不足時の正常動作。アクション不要
  - Issue abc123 (v2.49.1) — 2025-01-15

### バグ修正
- `IllegalArgumentException: currentEditionType is invalid` — 入力値バリデーション不足
  - Issue def456 (v2.49.1) — 2025-01-15
```

---

## ドキュメント

- `SKILL.md`: 完全なスキル実装ガイド（7ステップの詳細）

---

## 成功指標

- 対処不要なクラッシュを即座に切り分け（MONITORの偽陰性ゼロ）
- FIX/DEFENDの修正提案が実行可能（コンパイル通過）
- 同じクラッシュパターンの再分析をCLAUDE.md蓄積で防止

---

## バージョン履歴

### v1.0 (2026-02-25) - 初回リリース
- トリアージ分類マトリクス（MONITOR/INVESTIGATE/FIX/DEFEND）
- ANR/Non-fatal/Fatal 全タイプ対応
- ANRプロアクティブスキャン（5パターン）
- CLAUDE.md Crash Patterns 蓄積機能
- すべての説明を日本語で記述

---

## License

MIT License

---

**Maintainer**: 石原正也
**Repository**: https://github.com/xtone/ai_development_tools
