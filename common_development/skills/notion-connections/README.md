# Notion Connections

Notion MCP の接続を名前付きで管理し、複数の Notion ワークスペースを切り替えずに同時に使えるようにする Claude Code スキルです。

**Version**: v1.0.1

---

## 背景

Notion の MCP（`https://mcp.notion.com/mcp`）は、1つの登録で1つのワークスペースにしか接続できません。
ただし登録名を変えれば同じ URL を何個でも登録でき、認証も登録ごとに別々に持てます。
このスキルは、ワークスペースごとに `notion-<名前>` の登録を作り、その追加・確認・削除・付け替えを案内します。

> 「会社や案件ごとの Notion を、切り替えずに並べて使う」

ツール名は `mcp__notion-acme__notion-fetch` のように登録名で分かれるため、どのワークスペースを操作するかも呼び出し時点ではっきりします。

---

## 機能

- **接続の追加**: 登録名の提案・重複チェック → `claude mcp add` → OAuth でのワークスペース切り替えの注意 → 接続先の確認、までを案内
- **接続先の確認**: `notion-fetch(id: "self")` で実際に繋がっているワークスペースを確かめ、記録と食い違えば知らせる
- **削除・名前の付け替え**: 旧名を参照している許可ルール（`mcp__<名前>` / `mcp__<名前>__…`）や `disabledMcpServers` を全プロジェクトから洗い出す
- **認証の共有への配慮**: 認証は「登録名＋URL」ごとに共有されるため、他プロジェクトの同名登録を重複として扱い、削除時の影響も確認する
- **読み取り専用の補助スクリプト**: 設定（`~/.claude.json` / `.mcp.json`）は読むだけで書き換えない。認証情報は表示しない
- **PF非依存**: あらゆるプロジェクトで使用可能

---

## インストール

### Claude Code での使用

1. プラグインとしてインストール（推奨）:
   ```
   /plugin marketplace add xtone/ai_development_tools
   /plugin install common-development@xtone-ai-development-tools
   ```

2. またはパーソナルスキルディレクトリにリンク:
   ```bash
   ln -s /path/to/notion-connections ~/.claude/skills/notion-connections
   ```

3. Claude Code を再起動（既に実行中の場合）。プラグインなら `/reload-plugins` でも読み込める

### 前提条件

- Python 3.7 以上（補助スクリプトは標準ライブラリのみ）
- Claude Code CLI（`claude mcp add/remove/list`、接続先の確認に `claude -p` を使う）
- ブラウザで Notion の OAuth 認証ができること（認証は手作業）

---

## 使い方

スキル名を言わなくても、Notion MCP の登録・接続先・ワークスペースに関する依頼で起動します。`/notion-connections` で明示的に呼び出すこともでき、`/notion-connections list` のように続けて依頼を書けます。同じ名前のコマンドやスキルが他にある場合は、プラグイン名を付けた `/common-development:notion-connections` で呼び出してください。

### ワークスペースを追加する

```
別の Notion ワークスペースにも繋ぎたい
```

既存の接続を一覧 → 登録名の提案（例: `notion-acme`）→ スコープの選択（user / local）→ 登録 → 新しいセッションの `/mcp` で認証 → 接続先の確認と記録、の順に進みます。

### 接続先を確認する

```
いま Notion ってどのワークスペースに繋がってる？
```

登録済みの接続と、記録済みのワークスペースを表示します。必要に応じて実際の接続先を確かめます。

### 削除・名前を付け替える

```
notion って名前の Notion MCP を notion-acme に変えたい
```

新しい名前で追加 → 確認 → 古い名前を削除、の順に進めます。古い名前を参照している許可ルールは、新しい名前への書き換えを提案します。

---

## 出力フォーマット

`list` の出力例:

```
プロジェクト: /path/to/my-app
名前	スコープ	無効化	記録済みワークスペース
notion-acme	user	-	Acme Corp（2026-10-02 確認）
notion-example	local	-	未確認

他プロジェクトの local 登録:
  /path/to/other-app: notion
```

確認した接続先は `~/.claude/notion-connections.json` に記録されます（利用者の手元のみ）:

```json
{
  "notion-acme": {
    "workspace_name": "Acme Corp",
    "workspace_id": "<ワークスペース ID>",
    "verified_at": "2026-10-02T15:00:00+09:00"
  }
}
```

---

## 補助スクリプトのサブコマンド

| サブコマンド | 内容 |
|---------|------|
| `list` | 今のプロジェクトから見える Notion 接続と、記録済みの接続先 |
| `check-name <名前>` | 名前の形式・重複（他プロジェクトの同名登録を含む）をチェック。18 文字以上なら注意を出す |
| `find-refs <名前>` | `mcp__<名前>` を参照している許可ルールと `disabledMcpServers` を探す（一致した参照だけを表示） |
| `record <名前> <ワークスペース名> <ワークスペースID>` | 確認できた接続先を記録 |
| `forget <名前>` | 記録を消す |

テスト: `python3 -m unittest discover -s scripts`

---

## ドキュメント

- `SKILL.md`: 完全なスキル実装ガイド（手順と知っておくべき制約を含む）
- `scripts/notion_mcp.py`: 補助スクリプト
- `scripts/test_notion_mcp.py`: 補助スクリプトのテスト
- `evals/evals.json`: skill-creator の評価ケース

---

## バージョン履歴

### v1.0.1 (2026-10-05) - 修正
- SKILL.md の frontmatter を YAML として読めるように修正（description を引用符で囲む）
- README.md を追加

### v1.0 (2026-10-02) - 初回リリース
- 追加・一覧・削除・名前の付け替えの手順
- 補助スクリプト（一覧・名前チェック・参照箇所の検索・接続先の記録）とテスト
- 他プロジェクトの同名登録の検出と、削除時の認証への影響の確認
- PF非依存

---

## License

MIT License

---

**Maintainer**: HIRANO, Takahiro
**Repository**: https://github.com/xtone/ai_development_tools
