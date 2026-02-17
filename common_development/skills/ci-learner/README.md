# CI Learner

CI/GitHub Actionsの失敗パターンをCLAUDE.mdに蓄積する Claude Code スキルです。

**Version**: v1.0

---

## 背景

学習トライアドの第3の柱として、CI/CDパイプラインの失敗から体系的に学びます。
`gh run list` / `gh run view --log-failed` を活用し、追加インフラ不要で動作します。

> 「同じCI失敗を繰り返さないコードベースを実現する」

---

## 学習トライアド

| スキル | 学びの源泉 | タイミング |
|--------|-----------|-----------|
| `/lessons` | 自分で気づいた失敗・修正 | セッション終了時 |
| `/review-learn` | 他者からの指摘 | PRマージ後 |
| `/ci-learn` | CI/CDの失敗パターン | CI失敗発生後 |

3つを組み合わせることで、**個人の気づき＋チームの知見＋システムのフィードバック**が蓄積されます。

---

## 機能

- **失敗ログ取得**: GitHub CLIでCI runの失敗ログを自動取得
- **カテゴリ分類**: ビルド/テスト/リント/環境/デプロイ/権限/タイムアウトに自動分類
- **パターン抽出**: 繰り返し発生しうるパターンを抽出（一時障害・flakyテストは除外）
- **重複チェック**: 既存ルールとの重複を検出
- **クレジット付与**: CI Run IDとワークフロー名を記録
- **PF非依存**: あらゆるGitHubリポジトリで使用可能

---

## インストール

### Claude Code での使用

1. このスキルをプロジェクトにコピー:
   ```bash
   cp -r ci-learner /path/to/your-project/.claude/skills/
   ```

2. またはパーソナルスキルディレクトリにリンク:
   ```bash
   ln -s /path/to/ci-learner ~/.claude/skills/ci-learner
   ```

3. Claude Code を再起動（既に実行中の場合）

### 前提条件

- GitHub CLI (`gh`) がインストール済み
- `gh auth login` で認証済み

---

## 使い方

### 直近の失敗 run から学ぶ

```
/ci-learn
```

直近5件の失敗 CI run を表示し、選択した run の失敗ログからパターンを抽出します。

### 特定の run から学ぶ

```
/ci-learn #12345
```

指定した run ID の失敗ログからパターンを抽出します。

### 直近の失敗をまとめて分析

```
/ci-learn --recent
```

直近5件の失敗 run をまとめて分析し、共通パターンを抽出します。

---

## 出力フォーマット

CLAUDE.mdに追記される形式:

```markdown
## CI Learnings

このセクションはCI/GitHub Actionsの失敗パターンから自動生成されました。

### ビルド
- Gradle 8.x では `kotlin.jvm.target` を明示的に設定する。未設定だとCIのJDKバージョンとローカルで異なりビルドが失敗する
  - 🔧 CI Run #12345 (Build and Test) — 2026-02-15

### テスト
- CI環境ではテストのタイムアウトをローカルの2倍に設定する。GitHub Actions のランナーはローカルマシンより低速なため
  - 🔧 CI Run #12340 (Unit Tests) — 2026-02-14
```

---

## カテゴリ一覧

| カテゴリ | 内容 |
|---------|------|
| ビルド | コンパイルエラー、依存関係解決失敗 |
| テスト | テスト失敗、タイムアウト |
| リント・フォーマット | lint/ktlint/detekt エラー |
| 環境・設定 | Node/Java バージョン不一致、secrets 不足 |
| デプロイ | リリース、アーティファクト関連 |
| 権限・認証 | token 期限切れ、権限不足 |
| タイムアウト | ジョブ/ステップのタイムアウト |

プロジェクトに応じてカテゴリは自動的に追加・調整されます。

---

## ドキュメント

- `SKILL.md`: 完全なスキル実装ガイド（System Instructions含む）

---

## バージョン履歴

### v1.0 (2026-02-17) - 初回リリース
- CI失敗ログからパターンを抽出
- 7カテゴリ自動分類
- 既存ルールとの重複チェック
- CI Runクレジット付きでCLAUDE.mdに追記
- 学習トライアド（lessons/review-learn/ci-learn）の完成
- PF非依存

---

## License

MIT License

---

**Maintainer**: 石原正也
**Repository**: https://github.com/xtone/ai_development_tools
