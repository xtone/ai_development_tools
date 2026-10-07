# session-tips-digest 設計スペック

作成日: 2026-10-06
対象: 新規プラグイン `knowledge-sharing` の最初のスキル `session-tips-digest`

## 目的

Claude Code のセッション記録から、他のメンバーに共有できる運用 Tips を定期的に抽出し、最新の一次情報で裏付けを取り、Markdown と Artifact（必要なら Notion）として公開する作業を 1 コマンドで再現できるようにする。

2026-10-06 に手作業で行った次の流れを型にする。

1. `~/.claude/` の履歴・セッション JSONL・memory を集計して Tips 候補を抽出する
2. 機密情報と固有名を除いてパターン化し、UX ライティングで書く
3. 公式ドキュメント・論文などの一次情報で各 Tips を裏付ける、修正する、範囲を狭める
4. Markdown 2 ファイル（本体・参照リスト）を書き、日本語 lint を通す
5. HTML に変換して Artifact として公開する

## 利用者と成功条件

- 利用者: Claude Code を日常的に使う社内エンジニア。月 1 回程度、自分の記録から Tips を書き出して共有する
- 成功条件: 期間を指定して起動すると、機密スキャンが 0 件の Tips 本体と参照リストができ、Artifact の URL が返る。Tips の各項目に匿名化された事例と再現できる手順が付いている

## スコープ外

- セッション 1 本の効率採点（`common-development/evaluate-session` の領域）
- Slack 投稿、メール送信
- 複数人の記録を集めて横断集計すること（個人の `~/.claude/` だけを対象にする）

## プラグイン構成

```
knowledge_sharing/
├── .claude-plugin/marketplace.json
├── README.md
└── skills/
    └── session-tips-digest/
        ├── SKILL.md
        ├── scripts/
        │   ├── extract_sessions.py
        │   ├── scan_sensitive.py
        │   ├── md_to_artifact.py
        │   └── tests/
        │       ├── fixtures/
        │       ├── test_extract_sessions.py
        │       ├── test_scan_sensitive.py
        │       └── test_md_to_artifact.py
        ├── references/
        │   ├── tip-selection.md
        │   ├── research-sources.md
        │   └── writing-style.md
        └── templates/
            ├── tips.md
            └── references.md
```

ルートの `.claude-plugin/marketplace.json` に `knowledge-sharing`（source `./knowledge_sharing`、version 0.1.0）を追加する。

## 起動と引数

```
/knowledge-sharing:session-tips-digest [--since 30d] [--projects a,b] [--out tips/]
                                        [--artifact-url URL] [--notion PAGE_URL] [--no-research]
```

| 引数 | 既定 | 意味 |
|---|---|---|
| `--since` | `30d` | 抽出する期間。`7d`、`2026-09-01` のような日付も受ける |
| `--projects` | 全部 | 対象プロジェクト名の部分一致リスト |
| `--out` | `tips/` | 成果物ディレクトリ。作業ファイルは `tips/.work/` |
| `--artifact-url` | なし | 既存 Artifact を更新する。なければ新規公開 |
| `--notion` | なし | 指定ページ配下に本体を書き出す |
| `--no-research` | なし | Phase 3 を省略する |

`tips/` に前回の本体があれば差分更新モードになり、前回の最終更新日以降だけを抽出して既存 Tips に追記する。

## フェーズ

### Phase 0 準備

引数を解釈し、`--out` を作る。既存の本体を読んで差分更新モードかを決める。

### Phase 1 抽出

`extract_sessions.py --since 30d [--projects ...] --claude-dir ~/.claude --out tips/.work/sessions.json`

出力 JSON の内容:

- `prompts`: 期間内のユーザー入力（timestamp、project 名、本文）。`history.jsonl` から
- `tool_usage`: ツール名、Skill 名、Agent 型、MCP サーバー、`gh` サブコマンドの出現回数。`projects/*/*.jsonl` の `tool_use` から
- `bash_samples`: 指定パターン（`gh stack`、`git worktree`、`gcloud`、`aws`、`agy` など）に一致した Bash コマンドの先頭 300 文字、プロジェクト名付き
- `memories`: `projects/*/memory/*.md` の name、description、How to apply
- `harness`: `settings.json` の hooks の有無、enabledPlugins の名前、env のキー名、`commands/` `skills/` `agents/` のファイル名
- `vocabulary`: Phase 2 のスキャン辞書に使うプロジェクト名、リポジトリ名、ホスト名、メールアドレスの一覧

設定ファイルの値（env の値、ヘッダー、トークン）は出力しない。

Claude はこの JSON を読み、`references/tip-selection.md` の基準で候補を選ぶ。

- 他のプロジェクトでも再現できる
- 記録に実例がある（推測で作らない）
- コードや公式ドキュメントに書いてあることの転記ではない

### Phase 2 匿名化と執筆

`templates/tips.md` の 5 章（プロンプトの型、ワークフロー、カスタムコマンドとプラグイン、落とし穴、環境設定）に沿って書く。各 Tips は「何を」「なぜ（匿名化した事例）」「コマンド」の順。

書き終えたら `scan_sensitive.py --vocab tips/.work/sessions.json tips/*.md` を実行する。検出対象:

- Bearer やトークン様の文字列（英数 32 文字以上の連続など）
- メールアドレス
- GCP 組織 ID や AWS アカウント ID のような 12 桁前後の数列
- `notion.com`、`notion.so` を含む URL
- ホームディレクトリのパス（`/Users/`、`/home/`）
- `vocabulary` の語（プロジェクト名、リポジトリ名、ホスト名）

1 件でも残っていれば終了コード 1 を返し、Claude は次に進まない。

natural-japanese の lint が使える環境なら実行し、なければ `references/writing-style.md` のチェックリストで代替する。

### Phase 3 調査（既定で実行、`--no-research` で省略）

各 Tips について `references/research-sources.md` の優先順位で一次情報を探す。

1. 公式ドキュメント（code.claude.com、docs.github.com、cloud.google.com など）
2. ベンダー公式ブログ（anthropic.com/engineering、aws.amazon.com/blogs など）
3. arXiv の論文
4. その他（採用は最小限、数値は引かない）

結果は `templates/references.md` の 3 行形式（出典、言っていること、Tips をどう変えるか）で書き、各項目を「裏付ける」「修正する」「範囲を狭める」のどれかに分類する。Tips を弱める結果も必ず載せる。確度の高いものは本体にも反映し、本体末尾に参考文献の節を置く。

### Phase 4 公開

`md_to_artifact.py tips/claude-code-tips.md --out tips/dist/index.html`

HTML は、`<title>`、`:root` のテーマトークン（light と dark）、目次付きの読み物レイアウトを持つ。見出し・表・コードブロック・二重バッククォート・太字入りコードスパンを正しく変換する（2026-10-06 に手作業で踏んだ入れ子 `<code>` の回帰を防ぐ）。

HTML にも `scan_sensitive.py` をかけてから Artifact として公開する。`--artifact-url` があれば既存 URL を更新する。
`--notion` があれば Notion MCP で指定ページ配下に本体を書き出す。MCP が未接続なら接続手順を案内して終了する。
最後に、Artifact が非公開であることと、共有は Share メニューから行うことを利用者に伝える。

## スクリプト共通方針

- Python 3 標準ライブラリのみ。`python3 -I` で実行する
- 入力はすべて引数で渡し、カレントディレクトリに依存しない
- 失敗時は非 0 で終了し、標準エラーに理由を 1 行出す

## テスト

`scripts/tests/` に pytest を置く。

- `test_extract_sessions.py`: fixture の小さな `~/.claude` 構造（history.jsonl 3 行、プロジェクト JSONL 1 本、memory 1 件、settings.json）で、期間フィルタ、ツール集計、settings の値が出力に含まれないことを確認する
- `test_scan_sensitive.py`: 各種類を 1 件ずつ含む Markdown で全件検出し、クリーンな Markdown で 0 件、終了コードが検出ありで 1 になることを確認する
- `test_md_to_artifact.py`: 入れ子 `<code>` が出ない、`<title>` が先頭 8KB 内にある、テーマトークンが `:root` にある、表とコードブロックが変換されることを確認する

受け入れ条件: このマシンで `--since 7d` を指定して Phase 1〜4 を 1 回通し、スキャン 0 件で Artifact が公開できる。

## 既存スキルとの関係

`common-development/evaluate-session` はセッション 1 本の「無駄」を採点する。本スキルは期間横断で「共有できる知見」を抜く。README に両者の使い分けを書き、SKILL.md の description で「効率評価ではない」と明記する。

## 配布

feature ブランチ `feat/knowledge-sharing-plugin` で PR を作る。マーケットプレイスの `marketplace.json` にエントリを追加し、プラグインは version 0.1.0。
