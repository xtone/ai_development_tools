# MCP 設定・運用ガイド

## MCP サーバー（4 サーバー）

`.mcp.json` で以下を設定する:

- **Figma MCP** — ワイヤーフレーム・デザイン参照（requirements / design フェーズ）
- **GitHub MCP** — PR・コミット・リリース（implementation フェーズ）
- **Notion MCP** — Notion DB 同期・タスク更新（全フェーズ）
- **社内ナレッジ MCP（GitHub MCP 代用）** — ai_development_tools 検索

## トークン管理

- ローカル: `.env` ファイル（`.gitignore` で除外）
- CI: GitHub Secrets
- 命名統一: `FIGMA_TOKEN`, `GITHUB_TOKEN`, `NOTION_TOKEN`
- ローテーション: 90 日ごと（GitHub PAT classic）

## WSL2 環境での接続

WSL2 の localhost は個別にトンネルされているため、`host.docker.internal` 代用が必要。
（macOS 環境では不要。）

## エラーハンドリング 3 パターン

すべて T-002 本決定「警告のみ・ブロックなし」と整合する。

| エラー | 動作 |
|---|---|
| タイムアウト（30 秒） | ローカルキャッシュフォールバック + docs/pending-decisions.md に警告 |
| 認証失敗（401/403） | コンソール + Slack + docs/pending-decisions.md に同期表示 |
| Rate Limit（429） | 指数バックオフ（1s, 2s, 4s）3 回 → 人間にエスカレート |

## トラブルシューティング

### Notion MCP が応答しない

1. `.env` の `NOTION_TOKEN` が有効か確認
2. インテグレーションが対象 DB に接続許可されているか確認
3. ローカルキャッシュ（7 日間の DB ダンプ）を利用

### GitHub MCP のスコープエラー

PAT スコープが `repo`, `read:org`, `workflow` を含むか確認。スコープは `xtone/ai_development_tools` と `xtone-grouping/*` の 2 つを許可（MCP-10）。

## 参考リンク

- [Anthropic 公式 Skill 仕様](https://docs.claude.com/en/docs/claude-code/skills)
- [Claude Code プラグイン仕様](https://docs.claude.com/en/docs/claude-code/plugins)
- [MCP プロトコル仕様](https://modelcontextprotocol.io)
