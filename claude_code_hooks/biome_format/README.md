# Biome Format Hook

TypeScriptファイルの編集時に自動的にBiomeフォーマッターを実行するClaude Code hookです。

## 機能

- TypeScript/TSXファイル（`.ts`, `.tsx`）の編集時に自動的にBiomeフォーマットを実行
- `biome.json`設定ファイルがあるプロジェクトのみで動作
- 複数のプロジェクトディレクトリに対応

## セットアップ

### 1. スクリプトの配置

このディレクトリの `biome_format.sh` を任意の場所にコピーします。
今回はプロジェクトディレクトリ直下の`.claude/hooks/biome_format.sh`に保存する前提で説明します。

コピー後、実行権限を付与してください。

```bash
$ chmod a+x .claude/hooks/biome_format.sh
```

### 2. Claude Code hookの設定

Claude Codeの設定で以下のhookを追加してください：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/biome_format.sh"
          }
        ]
      }
    ]
  }
}
```

### 3. スクリプトの設定

`biome_format.sh` 内の設定を環境に合わせて調整してください：

```bash
# 対象プロジェクトディレクトリのリスト
PROJECT_DIRS=(
    "."  # ルートディレクトリ
    # 必要に応じて他のプロジェクトディレクトリを追加
)

# 対象ファイル拡張子のリスト
TARGET_EXTENSIONS=("ts" "tsx")
```

モノリポ構造で、claude codeのプロジェクトディレクトリ以下にTypeScriptのディレクトリが複数ある場合は、それぞれのディレクトリをリストとして設定してください。
例えば、`frontend`というディレクトリにNext.jsのプロジェクトがあるようなモノリポ構造の場合、`PROJECT_DIRS`は以下のように設定してください。

```bash
# 対象プロジェクトディレクトリのリスト
PROJECT_DIRS=(
    "frontend"
)
```

## 前提条件

- プロジェクトルートに `biome.json` 設定ファイルが存在すること (optional)
- `npx @biomejs/biome` コマンドが実行可能であること

## 動作

1. Claude CodeでTypeScript/TSXファイルを編集（Edit, Write, MultiEditツール使用時）
2. スクリプトが自動的に実行される
3. 対象ファイルがTypeScript/TSXファイルかチェック
4. プロジェクトディレクトリ内に `biome.json` が存在するかチェック
5. 条件を満たす場合、`npx @biomejs/biome format --write` を実行

## 注意事項

- スクリプトファイルに実行権限が必要です（`chmod +x biome_format.sh`）
- Biomeがプロジェクトにインストールされているか、npxで利用可能である必要があります
- 大きなファイルの場合、フォーマット処理に時間がかかる場合があります
