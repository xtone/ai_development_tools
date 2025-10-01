# Biome Format Hook

JavaScriptおよびTypeScriptファイルの編集時に自動的にBiomeフォーマッターを実行するClaude Code hookです。

## 機能

- JavaScript/TypeScriptファイル（`.js`, `.jsx`, `.ts`, `.tsx`）の編集時に自動的にBiomeフォーマットを実行
- 編集されたファイルのディレクトリから上位ディレクトリへ遡って`biome.json`を自動検索
- どのカレントディレクトリから実行されても正しく動作
- `biome.json`設定ファイルがある場合のみフォーマットを実行

## セットアップ

### 1. スクリプトの配置

このディレクトリの `biome_format.sh` を `~/bin/` ディレクトリにコピーします。

```bash
$ mkdir -p ~/bin
$ cp biome_format.sh ~/bin/
$ chmod +x ~/bin/biome_format.sh
```

**注意**: Claude Code hookは相対パスで指定するとカレントディレクトリが不定であるため正しく実行できないケースがあります。必ず絶対パス（`~/bin/biome_format.sh`）を使用してください。

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
            "command": "~/bin/biome_format.sh"
          }
        ]
      }
    ]
  }
}
```

### 3. スクリプトの設定（オプション）

必要に応じて、`biome_format.sh` 内の対象ファイル拡張子を変更できます：

```bash
# 対象ファイル拡張子のリスト
TARGET_EXTENSIONS=("ts" "tsx" "js" "jsx")
```

デフォルトでは、JavaScript/TypeScriptの一般的な拡張子（`.js`, `.jsx`, `.ts`, `.tsx`）が対象です。
プロジェクトディレクトリの設定は不要です。スクリプトが自動的に編集されたファイルから最も近い`biome.json`を探します。

## 前提条件

- `npx @biomejs/biome` コマンドが実行可能であること
- フォーマット対象のファイルまたはその上位ディレクトリに `biome.json` 設定ファイルが存在すること

## 動作

1. Claude CodeでJavaScript/TypeScriptファイルを編集（Edit, Write, MultiEditツール使用時）
2. スクリプトが自動的に実行される
3. 対象ファイルがJavaScript/TypeScriptファイルかチェック
4. ファイルパスを絶対パスに変換
5. 編集されたファイルのディレクトリから上位ディレクトリへ遡って `biome.json` を検索
6. `biome.json` が見つかった場合、`npx @biomejs/biome format --config-path --write` を実行

### biome.json検索の仕組み

スクリプトは編集されたファイルのディレクトリから開始し、ルートディレクトリ（`/`）に到達するまで親ディレクトリを遡って`biome.json`を探します。
最初に見つかった`biome.json`を使用してフォーマットを実行します。

これにより、モノリポ構造でも各プロジェクトの`biome.json`を正しく認識できます。

## 注意事項

- スクリプトファイルに実行権限が必要です（`chmod +x biome_format.sh`）
- Biomeがプロジェクトにインストールされているか、npxで利用可能である必要があります
- 大きなファイルの場合、フォーマット処理に時間がかかる場合があります
