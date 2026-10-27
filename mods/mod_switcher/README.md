# mod-switcher

`/mods` で mod の一覧をプロンプトの上に出し、その場で on/off を切り替える mod です。

## 使い方

`/mods` を実行すると、入力欄の上に一覧が出ます。入力欄が空の間は、そのまま次のキーで操作できます。

| キー | 動作 |
| --- | --- |
| j / ↓ | 下へ |
| k / ↑ | 上へ |
| x / スペース / 数字キー | その mod を切り替える（押した時点で保存） |
| q / Esc | 閉じる |

一覧が出ている間、入力欄が空の状態で打った j・k・x・q・スペースは文字として入りません。1 文字でも入力してあれば普通に打てます。送信すると一覧は閉じます。

| コマンド | 動作 |
| --- | --- |
| `/mods` | 一覧を開く／閉じる |
| `/mods list` | 一覧を文字で出す |
| `/mods on <名前>` / `/mods off <名前>` | 指定した mod を切り替える |

## 何が切り替わるか

一覧に出るのは「関数フックの mod」（`hooks/hooks.json` に `modules` がある plugin）です。

- **mod-switcher と同じフォルダに置いた mod**（`--plugin-dir` で並べた mod、Claude が書いた開発中の mod など）
  - off にすると、mod を並べたフォルダの隣の `.disabled/<そのフォルダ名>/` へ mod のフォルダを移し、on で戻します。フォルダが変わると Claude Code がすぐ読み込み直します。
- **インストール済みの mod**（`/plugin install` で入れたもの）
  - `claude plugin disable` / `claude plugin enable` を実行し、続けて `/reload-plugins` を実行します。設定に残るので、次回起動後もその状態のままです。

## 動作環境

| 項目 | 条件 |
| --- | --- |
| Claude Code | mod（関数フック）に対応した版。2.1.310 / 2.1.311 で動作確認 |
| OS | macOS（Linux でも動く想定ですが未確認。`/bin/mkdir`・`/bin/mv` と、PATH 上の `claude` コマンドを使います）。Windows は非対応 |
| 画面 | ターミナル版の Claude Code |

## 入れ方

```
/plugin marketplace add xtone/ai_development_tools
/plugin install mod-switcher@xtone-ai-development-tools
/reload-plugins
```

フォルダを直接読み込む場合は `claude --plugin-dir <このフォルダ>` で起動します。
