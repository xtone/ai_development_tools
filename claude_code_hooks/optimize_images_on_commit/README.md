# Git Commit時の画像最適化 Hook

git commit実行時に、ステージングされた画像ファイルを自動的に最適化するClaude Code hookです。

## 機能

- `git commit`実行前にステージング済み画像を自動最適化
- JPEG/PNG/GIF/SVGに対応
- ロスレス/高品質圧縮（見た目の劣化を最小限に）
- 最適化後に自動再ステージング
- サイズが増えた場合は元のファイルに復元

## セットアップ

### 1. 依存ツールのインストール

```bash
brew install jpegoptim optipng gifsicle
npm install -g svgo  # SVG最適化（オプション）
```

### 2. スクリプトの配置

**重要**: `optimize-before-commit.sh`と`optimize-images.sh`は**同じディレクトリ**に配置してください。

```bash
# Hooksディレクトリ作成
mkdir -p ~/.claude/hooks

# このリポジトリのスクリプトをコピー（両方とも同じディレクトリに配置）
cd /path/to/ai_development_tools
cp claude_code_hooks/optimize_images_on_commit/optimize-before-commit.sh ~/.claude/hooks/
cp claude_code_hooks/optimize_images_on_commit/optimize-images.sh ~/.claude/hooks/

# 実行権限を付与
chmod +x ~/.claude/hooks/optimize-before-commit.sh
chmod +x ~/.claude/hooks/optimize-images.sh
```

### 3. Claude Code hookの設定

`~/.claude/settings.json`に以下を追加：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/optimize-before-commit.sh"
          }
        ]
      }
    ]
  }
}
```

## 最適化設定

`optimize-images.sh`内で以下の設定を調整可能：

```bash
# 最適化対象の最小ファイルサイズ（デフォルト: 10KB）
readonly MIN_SIZE_THRESHOLD=10240

# JPEG品質（デフォルト: 85）
readonly JPEG_QUALITY=85

# PNG最適化レベル（0-7、デフォルト: 2）
readonly PNG_OPTIMIZATION_LEVEL=2

# GIF最適化レベル（1-3、デフォルト: 3）
readonly GIF_OPTIMIZATION_LEVEL=3
```

## 動作フロー

1. Claude CodeがBashツールで`git commit`を実行
2. Hookが発火し、ステージング済み画像を検出
3. 各画像を最適化
   - JPEG: メタデータ削除、プログレッシブ化
   - PNG: ロスレス圧縮
   - GIF: 色数最適化
   - SVG: 不要なメタデータ削除
4. 最適化成功時は自動で`git add`
5. commitを実行

## 使用例

```bash
# Claude Codeが実行
git add assets/image.jpg
git commit -m "Add new image"

# Hookが自動で動作
# 🎨 Optimizing images before commit...
# 📸 Found staged images:
#   - assets/image.jpg
#   Processing: assets/image.jpg
# ✅ Optimized: image.jpg | Saved: 23.5% (1.2MB → 920KB)
# ✨ Optimization complete! (1 files)
# [main abc123] Add new image
```

## ログ

最適化の詳細ログは以下に記録されます：

- コマンドログ: `~/.claude/logs/commit-optimization.log`
- 画像最適化ログ: `~/.claude/logs/image-optimization.log`

## 対応ファイル形式

| 形式 | ツール | 処理内容 |
|------|--------|----------|
| JPEG/JPG | jpegoptim | 品質85%、メタデータ削除、プログレッシブ化 |
| PNG | optipng | ロスレス圧縮（レベル2） |
| GIF | gifsicle | 色数最適化（256色）、圧縮レベル3 |
| SVG | svgo | 不要なメタデータ削除 |
| WebP | - | スキップ（既に最適化済みと判断） |

## 注意事項

- 10KB未満の小さい画像はスキップされます
- 最適化でサイズが増えた場合は元のファイルに復元されます
- **依存ツール（jpegoptim, optipng等）は事前に手動でインストールが必要です**
- 依存ツールがない場合はエラーメッセージが表示されますが、commitは続行されます
- エラーが発生してもcommitは続行されます

## トラブルシューティング

### 依存ツールが見つからないエラー

依存ツールがインストールされていない場合、エラーメッセージが表示されます。
[セットアップ > 1. 依存ツールのインストール](#1-依存ツールのインストール)を参照してインストールしてください。

インストール後、以下のコマンドで確認できます：

```bash
which jpegoptim optipng gifsicle svgo
```

### Hookが動作しない

1. スクリプトに実行権限があるか確認：
   ```bash
   ls -la ~/.claude/hooks/optimize-*.sh
   ```

2. ログを確認：
   ```bash
   tail -f ~/.claude/logs/commit-optimization.log
   ```

3. 手動実行でテスト：
   ```bash
   ~/.claude/hooks/optimize-images.sh path/to/image.jpg
   ```

## カスタマイズ

### 特定のディレクトリのみ対象にする

`optimize-before-commit.sh`を編集：

```bash
# ステージング済みの画像を取得
IMAGES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^(assets|images)/.*\.(jpg|jpeg|png|gif|svg)$' || true)
```

### 最適化の品質を変更

`optimize-images.sh`内の設定値を変更：

```bash
# より高品質（ファイルサイズ大）
readonly JPEG_QUALITY=90
readonly PNG_OPTIMIZATION_LEVEL=1

# より圧縮（ファイルサイズ小）
readonly JPEG_QUALITY=75
readonly PNG_OPTIMIZATION_LEVEL=7
```
