# MCP 設定・運用ガイド

プラグインが Notion / GitHub / Figma などの外部リソースを参照するために MCP サーバーを設定する。本ガイドは設定とトークン管理、トラブルシューティングをまとめる。

## MCP サーバー（4 サーバー）

`.mcp.json` で以下を設定する:

- **Figma MCP** — ワイヤーフレーム・デザイン参照（requirements / design フェーズ）
- **GitHub MCP** — PR・コミット・リリース（implementation フェーズ）
- **Notion MCP** — プラグイン参照先の Notion DB / ページ同期
- **社内ナレッジ MCP（GitHub MCP 代用）** — `ai_development_tools` リポジトリ検索

## トークン管理

- ローカル: `.env` ファイル（`.gitignore` で除外）
- CI: GitHub Secrets
- 命名統一: `FIGMA_TOKEN`, `GITHUB_TOKEN`, `NOTION_TOKEN`
- ローテーション: 90 日ごと（GitHub PAT classic）

## WSL2 環境での接続

WSL2 の localhost は個別にトンネルされているため、`host.docker.internal` 代用が必要。
（macOS 環境では不要。）

## エラーハンドリング 3 パターン

すべて「警告のみ・ブロックなし」（warn_and_document）と整合する。

| エラー | 動作 |
|---|---|
| タイムアウト（30 秒） | ローカルキャッシュフォールバック + プラグインの `pending-decisions.md` に警告 |
| 認証失敗（401/403） | コンソール + Slack + `pending-decisions.md` に同期表示 |
| Rate Limit（429） | 指数バックオフ（1s, 2s, 4s）3 回 → 人間にエスカレート |

## トラブルシューティング

### Notion MCP が応答しない

1. `.env` の `NOTION_TOKEN` が有効か確認
2. インテグレーションが対象 DB / ページに接続許可されているか確認
3. ローカルキャッシュ（7 日間の DB ダンプ）を利用

### GitHub MCP のスコープエラー

PAT スコープが `repo`, `read:org`, `workflow` を含むか確認。

## 参考リンク

- [Anthropic 公式 Skill 仕様](https://docs.claude.com/en/docs/claude-code/skills)
- [Claude Code プラグイン仕様](https://docs.claude.com/en/docs/claude-code/plugins)
- [MCP プロトコル仕様](https://modelcontextprotocol.io)
