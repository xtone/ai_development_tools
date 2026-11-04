# mods

Claude Code の mod（関数フックのプラグイン）を置くディレクトリです。

mod は `hooks/hooks.json` の `modules` に TypeScript / JavaScript のモジュールを指定するプラグインです。シェルコマンドを呼ぶ通常の hooks と違い、Claude Code の画面（入力欄の上の帯やペイン）に描画したり、プロンプトやツール呼び出しに割り込んだりできます。mod の仕組みは早期提供版なので、Claude Code の更新で動かなくなる可能性があります。

| mod | できること | OS |
| --- | --- | --- |
| [image-preview](./image_preview/README.md) | 添付した画像を、送信前は入力欄の上に、送信後はペインにプレビューする | macOS |
| [mod-switcher](./mod_switcher/README.md) | `/mods` で mod の一覧をプロンプトの上に出し、その場で on/off を切り替える | macOS |

## 入れ方

```
/plugin marketplace add xtone/ai_development_tools
/plugin install image-preview@xtone-ai-development-tools
/plugin install mod-switcher@xtone-ai-development-tools
/reload-plugins
```

## mod を追加するとき

- `mods/<snake_case の名前>/` に置き、ルートの `.claude-plugin/marketplace.json` に `"source": "./mods/<名前>"` で登録します。
- 各 mod には README（できること・動作環境・入れ方）と CHANGELOG を付けます。
- 追加する前に `claude plugin validate mods/<名前>` が通ることを確認します。
